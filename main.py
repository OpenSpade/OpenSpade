
from openspade.app_factory import create_app


def main():
    # 只创建一个app实例
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()
