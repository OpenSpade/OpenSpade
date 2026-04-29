import atexit
import importlib
import os
import pkgutil
from pathlib import Path
from typing import Callable, Dict, Any

from flask_apscheduler import APScheduler

scheduler = APScheduler()

# Job registry populated by @scheduled_job decorator
_job_registry = []


def scheduled_job(id: str, trigger: str = 'interval', **kwargs):
    """Decorator to register a function as a scheduled job.

    Usage::

        @scheduled_job('my_job', trigger='interval', seconds=60)
        def my_job():
            ...
    """
    def decorator(func):
        func._job_meta = {
            'id': id,
            'trigger': trigger,
            'kwargs': kwargs,
        }
        _job_registry.append(func)
        return func
    return decorator


def discover_jobs():
    """Auto-discover job modules in scheduler/jobs/ package."""
    jobs_path = Path(__file__).parent / 'jobs'
    jobs_package = 'openspade.scheduler.jobs'

    for importer, module_name, is_pkg in pkgutil.iter_modules([str(jobs_path)]):
        try:
            importlib.import_module(f'{jobs_package}.{module_name}')
        except Exception as e:
            print(f'[scheduler] Failed to load job module "{module_name}": {e}')


def init_scheduler(app, config: Dict[str, Any] = None):
    """Initialize APScheduler, discover jobs, and start."""
    # Guard against double-start in debug reloader
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return scheduler

    if config is None:
        config = {}

    default_config = {
        'SCHEDULER_API_ENABLED': True,
        'SCHEDULER_EXECUTORS': {
            'default': {'type': 'threadpool', 'max_workers': 10}
        },
        'SCHEDULER_JOB_DEFAULTS': {
            'coalesce': False,
            'max_instances': 3,
            'misfire_grace_time': 900,
        },
    }
    default_config.update(config)

    for key, value in default_config.items():
        app.config[key] = value

    scheduler.init_app(app)

    # Discover and register all decorated jobs
    _job_registry.clear()
    discover_jobs()

    for func in _job_registry:
        meta = func._job_meta
        # Wrap job in app context so Flask globals are available
        wrapped = _wrap_with_app_context(func, app)
        scheduler.add_job(
            id=meta['id'],
            func=wrapped,
            trigger=meta['trigger'],
            **meta['kwargs'],
        )
        print(f'[scheduler] Registered job: {meta["id"]} ({meta["trigger"]})')

    if not scheduler.running:
        scheduler.start()

    atexit.register(lambda: scheduler.shutdown(wait=True) if scheduler.running else None)
    return scheduler


def _wrap_with_app_context(func, app):
    """Wrap a job function so it runs inside Flask app context."""
    def wrapped():
        with app.app_context():
            func()
    wrapped.__name__ = func.__name__
    wrapped.__module__ = func.__module__
    return wrapped


def add_job(id: str, func: Callable, trigger: str = 'interval', **kwargs):
    scheduler.add_job(id=id, func=func, trigger=trigger, **kwargs)


def remove_job(id: str):
    scheduler.remove_job(id)


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)


def get_scheduler():
    return scheduler
