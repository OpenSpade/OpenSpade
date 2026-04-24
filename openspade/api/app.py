from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_apscheduler import APScheduler
from binance_connector import BinanceConnector

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置 APScheduler
app.config['SCHEDULER_API_ENABLED'] = True

# 初始化调度器
scheduler = APScheduler()
scheduler.init_app(app)

# 全局 BinanceConnector 实例
connector = None


@app.route('/api/init', methods=['POST'])
def init_connector():
    """初始化 Binance 连接器"""
    global connector
    data = request.json
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')

    if not api_key or not api_secret:
        return jsonify({'error': 'API key and secret are required'}), 400

    try:
        connector = BinanceConnector(api_key=api_key, api_secret=api_secret)
        return jsonify({'success': True, 'message': 'Binance connector initialized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assets/spot', methods=['GET'])
def get_spot_assets():
    """获取现货账户资产"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    assets = connector.get_all_spot_assets()
    return jsonify(assets)


@app.route('/api/assets/futures', methods=['GET'])
def get_futures_assets():
    """获取期货账户资产"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    assets = connector.get_all_futures_assets()
    return jsonify(assets)


@app.route('/api/assets/all', methods=['GET'])
def get_all_assets():
    """获取所有账户资产"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    assets = connector.get_all_assets()
    return jsonify(assets)


@app.route('/api/assets/total', methods=['GET'])
def get_total_assets():
    """获取总资产"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    total = connector.get_total_assets()
    return jsonify({'total': total})


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """获取所有持仓"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    positions = connector.get_positions()
    return jsonify(positions)


@app.route('/api/positions/<symbol>', methods=['GET'])
def get_position_info(symbol):
    """获取指定符号的持仓信息"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    position = connector.get_position_info(symbol)
    if position:
        return jsonify(position)
    else:
        return jsonify({'error': 'Position not found'}), 404


@app.route('/api/prices/<symbol>', methods=['GET'])
def get_current_price(symbol):
    """获取指定符号的当前价格"""
    price = connector.get_current_price(symbol)
    return jsonify({'price': price})


@app.route('/api/prices', methods=['GET'])
def get_all_prices():
    """获取所有价格"""
    symbols = request.args.getlist('symbols')
    prices = connector.get_all_prices(symbols if symbols else None)
    return jsonify(prices)


@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """获取投资组合摘要"""
    if not connector:
        return jsonify({'error': 'Binance connector not initialized'}), 400

    summary = connector.get_portfolio_summary()
    return jsonify(summary)


# 示例定时任务
@scheduler.task('interval', id='test_task', seconds=10, misfire_grace_time=900)
def test_task():
    """每10秒执行一次的测试任务"""
    print('Test task executed')

if __name__ == '__main__':
    # 启动调度器
    scheduler.start()
    app.run(debug=True, host='0.0.0.0', port=5001)
