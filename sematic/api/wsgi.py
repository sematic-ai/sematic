# Standard Library
from typing import Any, Dict, Optional

# Third-party
import flask
import uvicorn
from logging import getLogger


class SematicWSGI:
    """The standalone application class for gunicorn.

    https://docs.gunicorn.org/en/stable/custom.html

    """

    def __init__(
        self, app: flask.app.Flask, options: Optional[Dict[Any, Any]] = None
    ) -> None:
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
        # TODO: clean this up
        # get_config().wsgi_workers_count
        logger = getLogger(__name__)

        logger.info("Running application: %s", self.application)
        uvicorn.run(
            self.application,
            host=self.options.get("host", "127.0.0.1"),
            port=self.options.get("port", "5001"),
            log_config=self.options.get("logconfig_dict", None),
            workers=self.options.get("workers", 1),
        )
