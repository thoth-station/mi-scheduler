#!/usr/bin/env python3
# project template
# Copyright(C) 2010 Red Hat, Inc.
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""This is the main script of the template project."""

from typing import Set, List

import logging
import os

from github import Github

from github.GithubException import UnknownObjectException
from thoth.common import OpenShift
from thoth.common import init_logging

from thoth.storages import GraphDatabase

__title__ = "thoth.mi-scheduler"
__version__ = "1.1.1"

init_logging()
_LOGGER = logging.getLogger(__title__)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

KEBECHET_ENTITIES = "KebechetUpdateManager,DependencyUpdate"


class Schedule:
    """Schedule class which handles repository and organization checks and schedule methods."""

    def __init__(self, github: Github, organizations: List[str] = None, repositories: List[str] = None):
        """Initialize with github, orgs and repos optional."""
        self.gh = github
        self.orgs = organizations if organizations else []
        self.repos = repositories if repositories else []

        self.checked_repos: Set[str] = set()

        self._initialize_repositories_from_organizations()
        self._initialize_repositories_from_raw()

    def _initialize_repositories_from_organizations(self):
        """Check organizations if exist and acquire their repositories."""
        for org in self.orgs:
            try:
                gh_org = self.gh.get_organization(org)
                for repo in gh_org.get_repos():
                    if repo.archived:
                        _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
                        continue

                    if repo.full_name in self.repos:
                        self.repos.remove(repo.full_name)

                    self.checked_repos.add(repo.full_name)

            except UnknownObjectException:
                _LOGGER.error("organization %s was not recognized by GitHub API", org)

    def _initialize_repositories_from_raw(self):
        """Check repositories if exist and if not archived."""
        for repo in self.repos:
            try:
                gh_repo = self.gh_get_repo(repo)

                if gh_repo.archived:
                    _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
                    continue

                self.checked_repos.add(gh_repo.full_name)

            except UnknownObjectException:
                _LOGGER.error("Repository %s was not recognized by GitHub API", repo)

    def schedule_for_mi_analysis(self) -> None:
        """Schedule workflows for mi analysis."""
        for repo in self.checked_repos:
            workflow_id = OpenShift().schedule_mi_workflow(repository=repo)
            _LOGGER.info("Scheduled mi with id %r", workflow_id)

    def schedule_for_kebechet_analysis(self):
        """Schedule workflows for kebechet analysis."""
        for repo in self.checked_repos:
            workflow_id = OpenShift().schedule_mi_workflow(repository=repo, entities=KEBECHET_ENTITIES)
            _LOGGER.info("Scheduled mi-kebechet analysis with id %r", workflow_id)


def main():
    """MI-Scheduler entrypoint."""
    gh = Github(login_or_token=GITHUB_ACCESS_TOKEN)

    # regular mi schedule
    repos, orgs = OpenShift().get_mi_repositories_and_organizations()
    Schedule(gh, organizations=orgs, repositories=repos).schedule_for_mi_analysis()

    # kebechet schedule
    graph = GraphDatabase()
    graph.connect()
    kebechet_repos = graph.get_active_kebechet_github_installations_repos()
    # TODO use the return value more efficiently to assign only active managers
    Schedule(gh, repositories=kebechet_repos).schedule_for_kebechet_analysis(kebechet_repos)


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v%s", __version__)
    main()
