# Standard Library
import logging
import re
import sys

# Third-party
import click

# Sematic
from sematic import api_client
from sematic.cli.cli import cli
from sematic.config.config import switch_env


logger = logging.getLogger(__name__)

_COMMIT_STRUCTURE_HELP = "Structured as <repo owner>/<repo name>:<commit sha>"

# Regex matches a string which:
# - has an owner section, followed by `/`, followed by the repo section
# - has the repo section followed by `:`, followed by the commit sha section
# - owner and repo sections must each contain at least one character
# - owner and repo sections must not contain `/` or `:`
# - commit sha section must be exactly 40 characters
# - commit sha section must contain only lowercase letters a-f or digits
_COMMIT_STRUCTURE_REGEX = r"[^\s/:]+/[^\s/:]+:[a-f0-9]{40}"


@cli.group("github", short_help="Use Sematic's GitHub plugin")
def github():
    """Use Sematic's GitHub plugin"""
    switch_env("user")
    if not api_client.is_github_plugin_enabled():
        click.echo(
            "The GitHub plugin is not enabled for your Sematic deployment. "
            "Please talk to your server administrator if you want access!"
        )
        sys.exit(1)


@github.command(  # type: ignore
    "check-commit", short_help="Have Sematic check the status of a commit."
)
@click.argument("commit", required=True)
def check_commit(commit):
    """Have Sematic check the status of a commit on GitHub.

    This command is non-blocking; it does not wait for Sematic to be done
    executing the runs that are being used to check the commit. Instead,
    it simply examines the statuses of any runs that are being used to
    check the specified commit and updates GitHub with the result.

    If there are no runs being used to check the commit, Sematic will
    treat this as a successful check. Calling this Cli command can thus
    be used to generate a successful commit check even if there are no runs
    to check the commit.
    """
    if re.match(_COMMIT_STRUCTURE_REGEX, commit) is None:
        click.echo(f"Invalid commit specification. Expected: {_COMMIT_STRUCTURE_HELP}")
        sys.exit(1)
    owner_and_repo, commit_sha = commit.split(":")
    owner, repo = owner_and_repo.split("/")
    message = api_client.check_github_commit(owner, repo, commit_sha)
    click.echo(message)
