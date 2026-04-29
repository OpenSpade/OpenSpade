from flask_apscheduler import APScheduler
from typing import Callable, Dict, Any

scheduler = APScheduler()


def init_scheduler(app, config: Dict[str, Any] = None):
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
            'misfire_grace_time': 900
        }
    }
    default_config.update(config)

    for key, value in default_config.items():
        app.config[key] = value

    scheduler.init_app(app)
    return scheduler


def add_job(id: str, func: Callable, trigger: str = 'interval', **kwargs):
    scheduler.add_job(id=id, func=func, trigger=trigger, **kwargs)


def remove_job(id: str):
    scheduler.remove_job(id)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)


def get_scheduler():
    return scheduler