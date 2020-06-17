# Copyright (C) 2020 Dominik Tuchyna
#
# This file is part of SrcOpsMetrics.
#
# SrcOpsMetrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SrcOpsMetrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SrcOpsMetrics.  If not, see <http://www.gnu.org/licenses/>.

"""SrcOpsMetrics Scheduler."""

from github import Github
from thoth.common import OpenShift


def schedule_repositories(organizations: str, repositories: str) -> None:
    """Schedule workflows for repositories.

    Repositories are also gathered from all of the organizations passed.

    :param organizations:str: List of organizations in string format: org1,org2,org3,...
    :param repositories:str: List of repositories in string format: repo1,repo2,...
    """
    gh = Github()

    orgs = organizations.split(',')
    repos = [repo.full_name for repo in gh.get_organization(
        org).get_repos() for org in orgs]
    repos.extend(repositories.split(','))

    oc = OpenShift()
    for repo in repos:
        oc.schedule_srcopsmetrics_workflow(repository=repo)
