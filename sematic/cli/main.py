# Sematic
import sematic.cli.cancel  # noqa: F401
import sematic.cli.new  # noqa: F401
import sematic.cli.run  # noqa: F401
import sematic.cli.settings  # noqa: F401
import sematic.cli.start  # noqa: F401
import sematic.cli.stop  # noqa: F401
import sematic.cli.version  # noqa: F401
from sematic.cli.cli import cli

if __name__ == "__main__":
    cli()
