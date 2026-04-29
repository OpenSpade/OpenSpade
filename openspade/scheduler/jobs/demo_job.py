from openspade.scheduler import scheduled_job


@scheduled_job('demo_job', trigger='interval', seconds=5)
def demo_job():
    """A simple demo job that prints a message every 5 seconds."""
    print("Demo job executed at:")
