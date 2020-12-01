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
from github.Repository import Repository

from github.GithubException import UnknownObjectException
from thoth.common import OpenShift

from thoth.common import init_logging

__title__ = "thoth.mi-scheduler"
__version__ = "1.0.7"

init_logging()
_LOGGER = logging.getLogger(__title__)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")


class Schedule:
    """Schedule class which handles repository and organization checks and schedule methods."""

    def __init__(self, github: Github, organizations: List[str] = None, repositories: List[str] = None):
        """Initialize with github, orgs and repos optional."""
        self.gh = github
        self.orgs = organizations
        self.repos = repositories
        self.github_repos: Set[Repository] = set()

        self.oc = OpenShift()

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

                    self.github_repos.add(repo)

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

                self.github_repos.add(gh_repo)

            except UnknownObjectException:
                _LOGGER.error("Repository %s was not recognized by GitHub API", repo)

    def schedule_for_mi_analysis(self) -> None:
        """Schedule workflows for mi analysis."""
        for repo in self.github_repos:
            workflow_id = self.oc.schedule_mi_workflow(repository=repo.full_name)
            _LOGGER.info("Scheduled mi with id %r", workflow_id)

    def schedule_for_kebechet_analysis(self):
        """Schedule workflows for kebechet analysis."""
        raise NotImplementedError  # TODO: implement schedule workflow in thoth.common
        for repo in self.github_repos:
            workflow_id = self.oc.schedule_mi_kebechet_workflow(repository=repo.full_name)
            _LOGGER.info("Scheduled mi-kebechet analysis with id %r", workflow_id)


def main():
    """MI-Scheduler entrypoint."""
    gh = Github(login_or_token=GITHUB_ACCESS_TOKEN)

    oc = OpenShift()

    repos, orgs = oc.get_mi_repositories_and_organizations()
    Schedule(gh, orgs, repos).schedule_for_mi_analysis()

    # TODO: uncomment whe schedule method implemented in thoth.common
    # kebechet_repos = oc.get_mi_kebechet_repositories()
    # Schedule(gh, repositories=kebechet_repos).schedule_for_kebechet_analysis(kebechet_repos)


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v%s", __version__)
    main()
