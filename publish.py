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


"""Publish a new version of a library

To release a new version, create a git annotated tag named v<major>.<minor>.<patch>,
according to Semantic Versioning principles. Then run this script to deploy a release.

When running, you must supply the github organization and repo, so that links in the
changelog will be correct, and in order to create correct Github releases.

The script will do the following steps:
- Check if the build refers exactly to an annotated tag following the convention above
- Generate a suitable changelog
- Create packages for upload (wheels and tarballs)
- Use https://github.com/j0057/github-release to create a Github release
- Use the projects setup.py to create a PyPi release (using Twine for upload)
"""
from __future__ import unicode_literals, print_function

import argparse
import os
import re
import subprocess
import sys
import tempfile

from git import Repo, GitCommandError
from git.cmd import Git
from github_release import gh_release_create

# Magical, always present, empty tree reference. See https://stackoverflow.com/questions/9765453/
THE_NULL_COMMIT = Git().hash_object(os.devnull, t="tree")

ISSUE_NUMBER = re.compile(r"#(\d+)")

CHANGELOG_HEADER = """
Changes since last version
--------------------------

"""


class Formatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


class Repository(object):
    RELEASE_TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)(\.(0|[1-9]\d*)){0,2}$")

    def __init__(self, options):
        self.repo = Repo(options.directory)
        self._force = options.force
        self.current_tag = self.repo.git.describe(all=True).split('/')[1]
        print(f"Current tag: {self.current_tag}", file=sys.stderr)

    def ready_for_release(self):
        """Return true if the current git checkout is suitable for release

        To be suitable, it must not be dirty, must not have untracked files, must be an annotated tag,
        and the tag must follow the naming convention v<major>.<minor>.<bugfix>
        """
        if not self._force:
            if self.repo.is_dirty():
                print("Repository is dirty", file=sys.stderr)
                return False
            if self.repo.untracked_files:
                file_list = "\n\t".join(self.repo.untracked_files)
                print(f"Repository has untracked files:\n\t{file_list}", file=sys.stderr)
                return False
        if not self.current_tag:
            print("No tag found")
            return False
        tag_is_valid = self.RELEASE_TAG_PATTERN.match(self.current_tag) is not None
        if not tag_is_valid:
            print(f"""Tag "{self.current_tag}" is not a valid release tag. Expected "vX.Y.Z" where X, Y, and Z are non-negative integers, formatted without leading zeros.""", file=sys.stderr)
        return tag_is_valid

    def generate_changelog(self):
        """Use the git log to create a changelog with all changes since the previous tag"""
        try:
            previous_name = self.repo.git.describe(f"{self.current_tag}^", abbrev=0)
            previous_tag = self.repo.rev_parse(previous_name)
        except GitCommandError:
            previous_tag = THE_NULL_COMMIT
        commit_range = f"{previous_tag}..{self.current_tag}"
        return [(self._shorten(commit.hexsha), commit.summary) for commit in self.repo.iter_commits(commit_range)
                if len(commit.parents) <= 1]

    def _shorten(self, sha):
        return self.repo.git.rev_parse(sha, short=True)


class Uploader(object):
    def __init__(self, options, version, changelog, artifacts):
        self.dry_run = options.dry_run
        self.repo = f"{options.organization}/{options.repository}"
        self.version = version
        self.changelog = changelog
        self.artifacts = artifacts

    def _call(self, *args, **kwargs):
        msg = kwargs.pop("msg", "")
        if kwargs:
            raise TypeError(f"Unexpected **kwargs: {kwargs!r}")
        try:
            if self.dry_run:
                cmd_line = " ".join(repr(x) for x in args)
                print(f"Dry run. Would have called: {cmd_line}")
            else:
                subprocess.check_call(args)
        except subprocess.CalledProcessError:
            print(msg, file=sys.stderr)
            raise

    def github_release(self):
        """Create release in github, and upload artifacts and changelog"""
        gh_release_create(
            self.repo, self.version, self.artifacts,
            body=format_gh_changelog(self.changelog), publish=True, dry_run=self.dry_run
        )

    def pypi_release(self):
        """Create release in pypi.python.org, and upload artifacts and changelog"""
        self._call("twine", "upload", "--skip-existing", *self.artifacts, msg="Failed to upload artifacts to PyPI")


def format_rst_changelog(changelog, options):
    output = CHANGELOG_HEADER.splitlines(False)
    links = {}
    for sha, summary in changelog:
        links[sha] = f".. _{sha}: https://github.com/{options.organization}/{options.repository}/commit/{sha}"
        for match in ISSUE_NUMBER.finditer(summary):
            issue_number = match.group(1)
            links[issue_number] = f".. _#{issue_number}: https://github.com/{options.organization}/{options.repository}/issues/{issue_number}"
        summary = ISSUE_NUMBER.sub(r"`#\1`_", summary)
        output.append(f"* `{sha}`_: {summary}")
    output.append("")
    output.extend(links.values())
    return "\n".join(output)


def format_gh_changelog(changelog):
    output = CHANGELOG_HEADER.splitlines(False)
    links = {}
    for sha, summary in changelog:
        output.append(f"* {sha}: {summary}")
    output.append("")
    output.extend(links.values())
    return "\n".join(output)


def create_artifacts(changelog, options):
    """List all artifacts for uploads

    Wheels and tarballs
    """
    fd, name = tempfile.mkstemp(prefix="changelog", suffix=".rst", text=True)
    formatted_changelog = format_rst_changelog(changelog, options)
    with open(fd, "w", encoding="utf-8") as fobj:
        fobj.write(formatted_changelog)
    subprocess.check_call([
        sys.executable, "setup.py",
        "egg_info", "--tag-build=",
        "sdist",
        "bdist_wheel", "--universal"
        ],
        env=( os.environ.copy() | {"CHANGELOG_FILE": name} ) # see https://stackoverflow.com/a/78652759
    )
    os.unlink(name)
    return [os.path.abspath(os.path.join("dist", fname)) for fname in os.listdir("dist")]


def publish(options):
    repo = Repository(options)
    if not repo.ready_for_release():
        print("Repository is not ready for release", file=sys.stderr)
        return 1
    changelog = repo.generate_changelog()
    artifacts = create_artifacts(changelog, options)
    uploader = Uploader(options, repo.current_tag, changelog, artifacts)
    return_code = 0
    for i, release in enumerate((uploader.github_release, uploader.pypi_release)):
        try:
            release()
        except subprocess.CalledProcessError:
            return_code |= pow(2, i)
    return return_code


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=Formatter)
    parser.add_argument("-d", "--directory", default=".", help="Git repository")
    parser.add_argument("-f", "--force", action="store_true", help="Make a release even if the repo is unclean")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Do everything, except upload to GH/PyPI")
    parser.add_argument("organization", help="Github organization")
    parser.add_argument("repository", help="The name of the repository on GitHub and PyPi")
    options = parser.parse_args()
    if "GITHUB_TOKEN" not in os.environ:
        print("Publish requires the GITHUB_TOKEN environment variable to be set. Before you run this command, try `export GITHUB_TOKEN=your-gh-token-blah-blah-blah-whatever` (on Unix-likes) or `set GITHUB_TOKEN=your-gh-token-blah-blah-blah-whatever` (on Windows)\n\nPublish also requires the TWINE_USERNAME and TWINE_PASSWORD environment variables to be set in the same way; but, unlike GITHUB_TOKEN, you will be prompted to provide them later if they aren't in the environment, so setting them beforehand is not mandatory.")
        sys.exit(3)
    sys.exit(publish(options))


if __name__ == "__main__":
    main()
