# Sematic
from sematic.cli.cli import cli


@cli.command("migrate")
def migrate_cli() -> None:
    # Migrations are already applied for every CLI call.
    pass
