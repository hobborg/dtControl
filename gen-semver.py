#!/usr/bin/env python3
# Adapted from https://gitlab.com/threedotslabs/ci-scripts/blob/master/common/gen-semver and
# based on post at https://threedots.tech/post/automatic-semantic-versioning-in-gitlab-ci/
import os
import re
import sys
import semver
import subprocess


def git(*args):
    return subprocess.check_output(["git"] + list(args))


def tag_repo(tag):
    url = os.environ["CI_REPOSITORY_URL"]

    # Transforms the repository URL to the SSH URL
    # Example input: https://gitlab-ci-token:xxxxxxxxxxxxxxxxxxxx@gitlab.com/threedotslabs/ci-examples.git
    # Example output: git@gitlab.com:threedotslabs/ci-examples.git
    push_url = re.sub(r'.+@([^/]+)/', r'git@\1:', url)

    git("remote", "set-url", "--push", "origin", push_url)
    git("config", "user.email", "'ashok@in.tum.de'")
    git("config", "user.name", "'Pranav Ashok'")
    git("add", "VERSION")
    git("commit", "-m", "CI: Updated VERSION")
    git("tag", tag)
    git("push", "origin", tag)


def bump(latest):
    commit_msg = git("log", "--format=%B", "-n", "1", "HEAD").decode().strip()
    if "#nobump" in commit_msg:
        return latest
    if "#minor" in commit_msg:
        return semver.bump_minor(latest)
    if "#major" in commit_msg:
        return semver.bump_major(latest)
    # Then use bump_patch, bump_minor or bump_major
    return semver.bump_patch(latest)


def main():
    version_file = open("VERSION", 'w')
    try:
        latest = git("describe", "--tags").decode().strip()
        print(f"Current version: {latest}")
    except subprocess.CalledProcessError:
        # No tags in the repository
        version = "1.0.0"
    else:  # comes here if try succeeds without throwing exception
        if '-' not in latest:  # Skip already tagged commits
            version = latest
            version_file.write(version)
            version_file.close()
            print("Skipping tag update as latest commit already tagged.")
        else:
            version = bump(latest)

        version_file.write(version)
        version_file.close()
        print("Saved to file 'version'")

        if not (version == latest):  # If version has indeed changed
            print(f"Bumped version: {version}")
            tag_repo(version)
        else:
            print("Not bumping version.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

