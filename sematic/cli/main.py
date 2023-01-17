# Sematic
from sematic.config.config import switch_env
from sematic.db.migrate import migrate_up

switch_env("local")
migrate_up()

# Sematic
import sematic.cli.cancel  # noqa: F401, E402
import sematic.cli.logs  # noqa: F401, E402
import sematic.cli.migrate  # noqa: F401, E402
import sematic.cli.new  # noqa: F401, E402
import sematic.cli.run  # noqa: F401, E402
import sematic.cli.settings  # noqa: F401, E402
import sematic.cli.start  # noqa: F401, E402
import sematic.cli.stop  # noqa: F401, E402
import sematic.cli.version  # noqa: F401, E402
from sematic.cli.cli import cli  # noqa: E402

if __name__ == "__main__":
    cli()
