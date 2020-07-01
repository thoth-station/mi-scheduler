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
from github import Github
from thoth.common import OpenShift

from template.version import __version__


@click.command()
@click.option(
    "--repositories",
    "-r",
    type=str,
    required=False,
    help="Repositories to be analysed (e.g thoth-station/performance)",
)
@click.option(
    "--organizations",
    "-o",
    type=str,
    required=False,
    help="All repositories of an Organization to be analysed (e.g. AICoE)",
)

def cli(
    repositories: Optional[str],
    organizations: Optional[str],
):
    """Command Line Interface for SrcOpsMetrics."""
    repositories = [] if repositories is None else repositories
    organizations = [] if organizations is None else organizations

    gh = Github()

    orgs = organizations.split(',')
    repos = [repo.full_name for repo in gh.get_organization(org).get_repos() for org in orgs]

    repos.extend(repositories.split(','))

    schedule_repositories(repositories=repos)


def schedule_repositories(repositories: List[str]) -> None:
    """Schedule workflows for repositories.

    Repositories are also gathered from all of the organizations passed.

    :param organizations:str: List of organizations in string format: org1,org2,org3,...
    :param repositories:str: List of repositories in string format: repo1,repo2,...
    """
    oc = OpenShift()
    for repo in repositories:
        oc.schedule_srcopsmetrics_workflow(repository=repo)


if __name__ == "__main__":
    print(f"mi-scheduler for scheduling mi workflows v{__version__}.")
    cli()
