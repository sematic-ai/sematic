if __name__ == "__main__":
    # Third-party
    import gevent.monkey  # type: ignore

    # This enables us to use websockets and standard HTTP requests in
    # the same server locally, which is what we want. If you try to
    # use Gunicorn to do this, gevent will complain about
    # not monkey patching early enough, unless you have the gevent
    # monkey patch applied VERY
    # early (like user/sitecustomize).
    # Monkey patching: https://github.com/gevent/gevent/issues/1235
    gevent.monkey.patch_all()

# Sematic
import sematic.cli.cancel  # noqa: F401, E402
import sematic.cli.clean  # noqa: F401, E402
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
