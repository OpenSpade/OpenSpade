from flask import Flask


class Config:
    """Default configuration."""
    SECRET_KEY = 'dev-secret-key'
    DEBUG = False


def create_app(config_class=Config, enable_scheduler=True):
    """Application factory.

    Args:
        config_class: Configuration object to load.
        enable_scheduler: Set to False to skip scheduler init (useful in tests).
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Auto-discover and register all API blueprints
    from openspade.api import register_blueprints
    register_blueprints(app)

    # Initialize scheduler and auto-discover jobs
    if enable_scheduler:
        from openspade.scheduler import init_scheduler
        init_scheduler(app)

    return app
