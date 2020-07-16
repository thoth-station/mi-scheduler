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

from typing import Set

import logging
from github import Github
from github.GithubException import GithubException
from thoth.common import OpenShift

from thoth.common import init_logging

__title__ = "thoth.mi-scheduler"
__version__ = "1.0.0"

init_logging()
_LOGGER = logging.getLogger(__title__)


def main():
    """MI-Scheduler entrypoint."""
    oc = OpenShift()
    cm = oc.get_configmap(configmap_id="mi-scheduler", namespace="thoth-test-core")

    organizations = cm.get("organizations", "")
    repositories = cm.get("repositories", "")

    gh = Github()
    repos = set()

    orgs = organizations.split(",") if organizations is not None else []
    for org in orgs:
        try:
            gh_org = gh.get_organization(org)
            for repo in gh_org.get_repos():
                if repo.archived:
                    _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
                else:
                    repos.add(repo.full_name)
        except GithubException:
            _LOGGER.error("organization %s was not recognized by GitHub API", org)

    repos_raw = repositories.split(",") if repositories is not None else []
    for repo in repos_raw:
        try:
            if gh.get_repo(repo).archived:
                _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
            else:
                repos.add(repo)
        except GithubException:
            _LOGGER.error("Repository %s was not recognized by GitHub API", repo)

    schedule_repositories(repositories=repos)


def schedule_repositories(repositories: Set[str]) -> None:
    """Schedule workflows for repositories.

    Repositories are also gathered from all of the organizations passed.

    :param repositories:str: List of repositories in string format: repo1,repo2,...
    """
    oc = OpenShift()
    for repo in repositories:
        workflow_id = oc.schedule_srcopsmetrics(repository=repo)
        _LOGGER.info("Scheduled srcopsmetrics with id %r", workflow_id)


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v%s", __version__)
    main()
