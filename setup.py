from setuptools import setup, find_packages
from pathlib import Path
import os


def get_version():
    with open(os.path.join('./', '__init__.py')) as f:
        content = f.readlines()

    for line in content:
        if line.startswith('__version__ ='):
            return line.split(' = ')[1][1:-2]
    raise ValueError("No version identifier found")


VERSION = get_version()

HERE = Path(__file__).parent
README: str = Path(HERE, "README.rst").read_text(encoding="utf-8")

setup(
    name='mi-scheduler',
    version=VERSION,
    twidescription='Scheduler for Meta-information Indicators project',
    packages=find_packages(),
    long_description=README,
    long_description_content_type='text/x-rst',
    author='Dominik Tuchyna',
    author_email='xtuchyna@redhat.com',
    license='GPLv3+',
    url='https://github.com/thoth-station/mi-scheduler/',
)