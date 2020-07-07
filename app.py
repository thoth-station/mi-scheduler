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

from typing import List, Optional

import click
import logging
from github import Github
from github.GithubException import GithubException
from thoth.common import OpenShift

from thoth.common import init_logging

__title__ = "mi-scheduler"
__version__ = "0.1.0"

init_logging()
_LOGGER = logging.getLogger()


@click.command()
@click.option(
    "--repositories", help="Repositories to be analysed (e.g thoth-station/performance)",
)
@click.option(
    "--organizations",
    "-o",
    type=str,
    required=False,
    help="Organizations (all of their repositories) to be analysed (e.g. AICoE)",
)
def main(
    repositories: Optional[str], organizations: Optional[str],
):
    """Command Line Interface for SrcOpsMetrics."""
    repositories = "" if repositories is None else repositories
    organizations = "" if organizations is None else organizations

    gh = Github()

    orgs = organizations.split(",")

    repos = []
    for org in orgs:
        try:
            gh_org = gh.get_organization(org)
            for repo in gh_org.get_repos():
                if repo.archived:
                    _LOGGER.info("repository %s is archived, therefore skipped" % repo.full_name)
                else:
                    repos.append(repo.full_name)
        except GithubException:
            _LOGGER.error("organization %s was not recognized by GitHub API" % org)

    repos.extend(repositories.split(","))

    schedule_repositories(repositories=repos)


def schedule_repositories(repositories: List[str]) -> None:
    """Schedule workflows for repositories.

    Repositories are also gathered from all of the organizations passed.

    :param organizations:str: List of organizations in string format: org1,org2,org3,...
    :param repositories:str: List of repositories in string format: repo1,repo2,...
    """
    oc = OpenShift()
    for repo in repositories:
        oc.schedule_srcopsmetrics(repository=repo)


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v %s" % __version__)
    main()
