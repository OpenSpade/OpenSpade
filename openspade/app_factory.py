from flask import Flask
from datetime import datetime


class Config:
    """默认配置类"""
    SECRET_KEY = 'dev-secret-key'
    DEBUG = False


def test_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Test job executed!")


def create_app(config_class=Config):
    """工厂函数，只在需要时创建app实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 注册所有蓝图
    from openspade.api.product import product_bp
    from openspade.api.user import user_bp

    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(product_bp, url_prefix='/api/product')

    from openspade.scheduler import init_scheduler, add_job
    init_scheduler(app)
    add_job('test_job', test_job, trigger='interval', seconds=10)

    return app
