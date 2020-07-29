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

__title__ = "thoth.mi-scheduler"
__version__ = "1.0.5"

init_logging()
_LOGGER = logging.getLogger(__title__)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")


def main():
    """MI-Scheduler entrypoint."""
    oc = OpenShift()
    cm = oc.get_configmap(configmap_id="mi-scheduler", namespace="thoth-test-core")

    organizations = cm["data"].get("organizations", "")
    repositories = cm["data"].get("repositories", "")
    _LOGGER.info("Detected %s organizations from configMap for inspection", organizations)
    _LOGGER.info("Detected %s repositories from configMap for inspection", repositories)

    gh = Github(login_or_token=GITHUB_ACCESS_TOKEN)
    repos = set()

    orgs = list_data(organizations)
    for org in orgs:
        try:
            gh_org = gh.get_organization(org)
            for repo in gh_org.get_repos():
                if repo.archived:
                    _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
                else:
                    repos.add(repo.full_name)
        except UnknownObjectException:
            _LOGGER.error("organization %s was not recognized by GitHub API", org)

    repos_raw = list_data(repositories)
    for repo in repos_raw:
        try:
            if gh.get_repo(repo).archived:
                _LOGGER.info("repository %s is archived, therefore skipped", repo.full_name)
            else:
                repos.add(repo)
        except UnknownObjectException:
            _LOGGER.error("Repository %s was not recognized by GitHub API", repo)

    schedule_repositories(repositories=repos)


def list_data(str_list: str) -> List[str]:
    """Make list out of the string acquired from configMap."""
    if str_list is not None and str_list != "":
        return str_list.split(",")
    return []


def schedule_repositories(repositories: Set[str]) -> None:
    """Schedule workflows for repositories.

    Repositories are also gathered from all of the organizations passed.

    :param repositories:str: List of repositories in string format: repo1,repo2,...
    """
    oc = OpenShift()
    for repo in repositories:
        workflow_id = oc.schedule_mi_workflow(repository=repo)
        _LOGGER.info("Scheduled mi with id %r", workflow_id)


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v%s", __version__)
    main()
