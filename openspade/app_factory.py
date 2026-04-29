from flask import Flask


class Config:
    """默认配置类"""
    SECRET_KEY = 'dev-secret-key'
    DEBUG = False


def create_app(config_class=Config):
    """工厂函数，只在需要时创建app实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 注册所有蓝图
    from openspade.api.product import product_bp
    from openspade.api.user import user_bp

    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(product_bp, url_prefix='/api/product')

    return app
