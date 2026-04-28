from flask import Flask
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True

scheduler = APScheduler()
scheduler.init_app(app)

# 示例定时任务
@scheduler.task('interval', id='test_task', seconds=5, misfire_grace_time=900)
def test_task():
    """每5秒执行一次的测试任务"""
    print('Test task executed')

if __name__ == '__main__':
    print('Starting scheduler...')
    scheduler.start()
    print('Scheduler started successfully!')
    print('Testing task will run every 5 seconds.')
    print('Press Ctrl+C to exit.')
    
    # 保持脚本运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('Exiting...')
        scheduler.shutdown()
