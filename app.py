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

import logging
import os
from pathlib import Path
from typing import List, Set, Optional

import click

from github import Github
from github.GithubException import UnknownObjectException
from thoth.common import OpenShift, init_logging
from thoth.storages import GraphDatabase

__title__ = "thoth.mi-scheduler"
__version__ = "1.7.6"

init_logging()
_LOGGER = logging.getLogger(__title__)

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

KEBECHET_ENTITIES = "PullRequest,Issue"
MI_ENTITIES = os.getenv("MI_ENTITIES")

KEBECHET_KNOWLEDGE_PATH = Path("thoth-sli-metrics").joinpath("kebechet-update-manager")

DEPLOYMENT_NAME = os.environ["THOTH_DEPLOYMENT_NAME"]


class Schedule:
    """Schedule class which handles repository and organization checks and schedule methods."""

    def __init__(
        self,
        openshift: OpenShift,
        github: Optional[Github] = None,
        organizations: List[str] = None,
        repositories: List[str] = None,
        subdir: str = "",
    ):
        """Initialize with github, orgs and repos optional."""
        self.gh = github
        self.oc = openshift

        self.orgs = organizations if organizations else []
        self.repos = repositories if repositories else []

        self.checked_repos: Set[str] = set()

        self.kebechet_stats_path = Path(DEPLOYMENT_NAME).joinpath(subdir).joinpath(KEBECHET_KNOWLEDGE_PATH).as_posix()
        self.mi_path = Path(DEPLOYMENT_NAME).joinpath("mi").joinpath(subdir).as_posix()

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
                gh_repo = self.gh.get_repo(repo)

                if gh_repo.archived:
                    _LOGGER.info("repository %s is archived, therefore skipped", repo)
                    continue

                self.checked_repos.add(repo)

            except UnknownObjectException:
                _LOGGER.error("Repository %s was not recognized by GitHub API", repo)

    def schedule_for_mi_analysis(self) -> None:
        """Schedule workflows for mi analysis."""
        for repo in self.checked_repos:
            workflow_id = self.oc.schedule_mi_workflow(
                create_knowledge=True,
                repository=repo,
                entities=MI_ENTITIES,
                knowledge_path=self.mi_path,
            )
            _LOGGER.info("Scheduled mi with id %r", workflow_id)

    def schedule_for_kebechet_analysis(self):
        """Schedule workflows for kebechet analysis."""
        for repo in self.checked_repos:
            workflow_id = self.oc.schedule_mi_workflow(
                create_knowledge=True,
                repository=repo,
                entities=KEBECHET_ENTITIES,
                knowledge_path=self.mi_path,
                mi_used_for_thoth=True,
            )
            _LOGGER.info("Scheduled mi-kebechet analysis with id %r", workflow_id)

    def schedule_for_kebechet_merge(self):
        """Schedule workflows for kebechet analysis."""
        workflow_id = self.oc.schedule_mi_workflow(
            knowledge_path=self.mi_path,
            mi_used_for_thoth=True,
            mi_merge=True,
            mi_merge_path=self.kebechet_stats_path,
        )
        _LOGGER.info("Scheduled mi-kebechet merge with id %r", workflow_id)


@click.command()
@click.option(
    "--kebechet-analysis",
    is_flag=True,
    required=False,
    help="Flag for SCHEDULE_KEBECHET_ANALYSIS, used for scheduling mi workflows for kebechet repositories",
)
@click.option(
    "--kebechet-merge",
    is_flag=True,
    required=False,
    help="Flag for SCHEDULE_KEBECHET_MERGE, used for merging data collected from previous mi analysis",
)
@click.option(
    "--gh-repo-analysis",
    is_flag=True,
    required=False,
    help="Flag for SCHEDULE_GH_REPO_ANALYSIS, used for scheduling mi workflows for mi repositories",
)
@click.option(
    "--subdir",
    default="",
    is_flag=False,
    required=False,
    help="""
    Subdirectory for data storage. In case of regular mi data, the resulting path is then deployment_name/mi/<subdir>/
    In case of kebechet related data, data path is deployment_name/<subdir>/.
    """,
    show_default=True,
)
def main(
    kebechet_analysis: Optional[bool],
    kebechet_merge: Optional[bool],
    gh_repo_analysis: Optional[bool],
    subdir: str = "",
):
    """MI-Scheduler entrypoint."""
    gh = Github(login_or_token=GITHUB_ACCESS_TOKEN)
    oc = OpenShift()

    # regular mi schedule
    if gh_repo_analysis:
        repos, orgs = oc.get_mi_repositories_and_organizations()
        Schedule(
            github=gh, openshift=oc, organizations=orgs, repositories=repos, subdir=subdir
        ).schedule_for_mi_analysis()

    if kebechet_analysis:
        graph = GraphDatabase()
        graph.connect()
        kebechet_repos = graph.get_active_kebechet_github_installations_repos()
         _LOGGER.debug("Got these active kebechet installation repos: %s", kebechet_repos)
        Schedule(github=gh, openshift=oc, repositories=kebechet_repos, subdir=subdir).schedule_for_kebechet_analysis()

    if kebechet_merge:
        Schedule(openshift=oc, subdir=subdir).schedule_for_kebechet_merge()


if __name__ == "__main__":
    _LOGGER.info("mi-scheduler for scheduling mi workflows v%s", __version__)
    main(auto_envvar_prefix="SCHEDULE")
