#!/usr/bin/env python
# -*- coding: utf-8

# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from setuptools import setup

GENERIC_REQ = [
    "six==1.12.0",
    'GitPython==2.1.11',
    "twine==1.12.1",
    "githubrelease==1.5.8",
    "gitdb2>=2.0.0,<3.0.0",  # Pin this to avoid a problem with changed API.
                             # TODO: Should update to latest GitPython to fix.
]

CODE_QUALITY_REQ = [
    'prospector==1.2.0',
]

TESTS_REQ = [
    'tox==3.6.1',
    'mock==2.0.0',
    'pytest==4.0.2',
    'pytest-cov==2.6.0',
    'pytest-html==1.19.0',
    'pytest-sugar==0.9.2',
    'attrs==19.1.0',  # Pin this to avoid problems caused by https://github.com/python-attrs/attrs/issues/307
                      # TODO: Proper fix is to upgrade to pytest>5.2.0, but that drops Python 2 support
]


def _generate_description():
    description = [_read("README.rst")]
    changelog_file = os.getenv("CHANGELOG_FILE")
    if changelog_file:
        description.append(_read(changelog_file))
    return "\n".join(description)


def _get_license_name():
    with open(os.path.join(os.path.dirname(__file__), "LICENSE")) as f:
        for line in f:
            if line.strip():
                return line.strip()


def _read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def main():
    setup(
        name="publish",
        author="FiaaS developers",
        author_email="fiaas@googlegroups.com",
        use_scm_version=True,
        py_modules=["publish"],
        zip_safe=True,
        include_package_data=True,

        # Requirements
        install_requires=GENERIC_REQ,
        setup_requires=['pytest-runner', 'wheel', 'setuptools_scm'],
        extras_require={
            "dev": TESTS_REQ + CODE_QUALITY_REQ,
            "codacy": ["codacy-coverage"],
            "docs": ["Sphinx>=1.6.3"]
        },

        # Metadata
        description="Publish python package to PyPI and Github",
        long_description=_generate_description(),
        url="https://github.com/fiaas/publish",
        license=_get_license_name(),
        keywords="pypi github fiaas",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Topic :: Internet",
            "Topic :: Software Development :: Build Tools",
            "Topic :: System :: Software Distribution",
        ],

        # Entrypoints
        entry_points={
            "console_scripts": [
                "publish=publish:main"
            ]
        }

    )


if __name__ == "__main__":
    main()
