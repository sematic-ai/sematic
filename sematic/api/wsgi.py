# Third-party
import flask
import gunicorn.app.base  # type: ignore
from gunicorn.util import daemonize  # type: ignore


class SematicWSGI(gunicorn.app.base.BaseApplication):
    """The standalone application class for gunicorn.

    https://docs.gunicorn.org/en/stable/custom.html

    """

    def __init__(self, app: flask.app.Flask, options: dict = None) -> None:
        """Initializer for the standalone application class for
        gunicorn.

        https://docs.gunicorn.org/en/stable/custom.html


        Parameters
        ----------
        app:
            The wsgi compliant server application.
        options:
            Options passed to the gunicorn instance.

        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        """Loads the configuration for gunicorn application.

        https://docs.gunicorn.org/en/stable/custom.html

        """
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self) -> flask.app.Flask:
        """Access the wsgi compliant gunicorn application.

        https://docs.gunicorn.org/en/stable/custom.html


        Returns
        -------
        self.application
            The wsgi compliant gunicorn application.

        """
        return self.application

    def run(self):
        if self.cfg.daemon:
            daemonize(self.cfg.enable_stdio_inheritance)
        super().run()
