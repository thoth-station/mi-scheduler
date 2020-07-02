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
"""Python project setup.py file."""

from setuptools import setup, find_packages
from pathlib import Path


def get_version():
    """Get version of mi-scheduler project."""
    with open("version.py", "r") as f:
        content = f.readlines()

    for line in content:
        if line.startswith("__version__ ="):
            return line.split(" = ")[1][1:-2]
    raise ValueError("No version identifier found")


VERSION = get_version()

HERE = Path(__file__).parent
README: str = Path(HERE, "README.rst").read_text(encoding="utf-8")

setup(
    name="mi-scheduler",
    version=VERSION,
    twidescription="Scheduler for Meta-information Indicators project",
    packages=find_packages(),
    long_description=README,
    long_description_content_type="text/x-rst",
    author="Dominik Tuchyna",
    author_email="xtuchyna@redhat.com",
    license="GPLv3+",
    url="https://github.com/thoth-station/mi-scheduler/",
)
