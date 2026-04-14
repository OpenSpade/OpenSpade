import requests
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime

# 请求头，模拟浏览器请求
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Content-Type': 'application/json'
}

# 请求间隔时间（秒）
REQUEST_INTERVAL = 0.1

def get_binance_futures_pairs():
    """
    获取币安期货合约交易对列表
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        
        # 提取交易对信息
        symbols = data.get('symbols', [])
        trading_pairs = []
        
        for symbol in symbols:
            if symbol.get('status') == 'TRADING':  # 只获取可交易的合约
                trading_pairs.append(symbol.get('symbol'))
        
        return trading_pairs
    except requests.exceptions.RequestException as e:
        print(f"获取交易对列表时网络出错: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"解析交易对列表时出错: {e}")
        return []
    except Exception as e:
        print(f"获取交易对列表时未知错误: {e}")
        return []

def get_binance_futures_klines(symbol, interval="1d", limit=500):
    """
    获取币安期货合约的K线数据
    :param symbol: 交易对符号，如 BTCUSDT
    :param interval: 时间间隔，默认日线 "1d"
    :param limit: 返回数据的数量，默认100
    :return: K线数据的DataFrame
    """
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        # 添加请求间隔，避免被API限制
        time.sleep(REQUEST_INTERVAL)
        
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        return df
    except requests.exceptions.RequestException as e:
        print(f"获取{symbol}的K线数据时网络出错: {e}")
        return pd.DataFrame()
    except json.JSONDecodeError as e:
        print(f"解析{symbol}的K线数据时出错: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"获取{symbol}的K线数据时未知错误: {e}")
        return pd.DataFrame()

def calculate_technical_indicators(df):
    """
    计算技术分析指标
    :param df: K线数据的DataFrame
    :return: 带有技术指标的DataFrame
    """
    if df.empty:
        return df
    
    # 计算移动平均线
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    
    # 计算相对强弱指标（RSI）
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    # 避免除以零
    loss = loss.replace(0, 0.0001)
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算布林带
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
    
    # 计算MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # 计算波动率（标准差）
    df['Volatility'] = df['close'].rolling(window=20).std()
    
    # 计算成交量变化率
    df['Volume_Change'] = df['volume'].pct_change()
    
    # 计算价格变化率
    df['Price_Change'] = df['close'].pct_change()
    
    return df

def generate_trading_signal(df):
    """
    生成交易信号
    :param df: 带有技术指标的DataFrame
    :return: 交易信号
    """
    if len(df) < 20:
        return "数据不足"
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 基于RSI的信号
    if latest['RSI'] > 70:
        rsi_signal = "超买"
    elif latest['RSI'] < 30:
        rsi_signal = "超卖"
    else:
        rsi_signal = "正常"
    
    # 基于MACD的信号
    if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
        macd_signal = "金叉"
    elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
        macd_signal = "死叉"
    else:
        macd_signal = "无"
    
    # 基于移动平均线的信号
    if latest['MA10'] > latest['MA20'] > latest['MA50']:
        ma_signal = "多头排列"
    elif latest['MA10'] < latest['MA20'] < latest['MA50']:
        ma_signal = "空头排列"
    else:
        ma_signal = "无"
    
    # 综合信号
    if rsi_signal == "超卖" and macd_signal == "金叉" and ma_signal == "多头排列":
        return "买入"
    elif rsi_signal == "超买" and macd_signal == "死叉" and ma_signal == "空头排列":
        return "卖出"
    else:
        return "持有"

def analyze_trading_pair(symbol, interval="1d", limit=100):
    """
    分析单个交易对
    :param symbol: 交易对符号
    :param interval: 时间间隔
    :param limit: 数据数量
    :return: 分析结果
    """
    # 获取K线数据
    df = get_binance_futures_klines(symbol, interval, limit)
    if df.empty:
        return None
    
    # 计算技术指标
    df = calculate_technical_indicators(df)
    
    # 生成分析结果
    latest_data = df.iloc[-1]
    analysis_result = {
        'symbol': symbol,
        'latest_price': latest_data['close'],
        'price_change': latest_data['Price_Change'] * 100 if not pd.isna(latest_data['Price_Change']) else 0,
        'rsi': latest_data['RSI'],
        'ma10': latest_data['MA10'],
        'ma20': latest_data['MA20'],
        'ma50': latest_data['MA50'],
        'macd': latest_data['MACD'],
        'macd_signal': latest_data['MACD_signal'],
        'macd_hist': latest_data['MACD_hist'],
        'volatility': latest_data['Volatility'],
        'volume': latest_data['volume'],
        'volume_change': latest_data['Volume_Change'] * 100 if not pd.isna(latest_data['Volume_Change']) else 0
    }
    
    # 生成交易信号
    analysis_result['signal'] = generate_trading_signal(df)
    
    return analysis_result

def analyze_multiple_pairs(pairs, interval="1d", limit=100, max_pairs=10):
    """
    分析多个交易对
    :param pairs: 交易对列表
    :param interval: 时间间隔
    :param limit: 数据数量
    :param max_pairs: 最大分析交易对数量
    :return: 分析结果列表
    """
    results = []
    # 限制分析的交易对数量，避免请求过多
    for i, symbol in enumerate(pairs[:max_pairs]):
        print(f"分析第 {i+1}/{min(len(pairs), max_pairs)} 个交易对: {symbol}")
        analysis = analyze_trading_pair(symbol, interval, limit)
        if analysis:
            results.append(analysis)
    return results

def save_analysis_results(results, filename="analysis_results.json"):
    """
    保存分析结果到文件
    :param results: 分析结果列表
    :param filename: 文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"分析结果已保存到 {filename}")
    except Exception as e:
        print(f"保存分析结果时出错: {e}")

if __name__ == "__main__":
    # 测试获取交易对列表
    pairs = get_binance_futures_pairs()
    print(f"获取到 {len(pairs)} 个币安期货合约交易对")
    print("前10个交易对:")
    for pair in pairs[:10]:
        print(pair)
    
    # 测试获取K线数据
    if pairs:
        test_symbol = pairs[0]  # 使用第一个交易对进行测试
        print(f"\n测试获取{test_symbol}的日线K线数据:")
        klines_df = get_binance_futures_klines(test_symbol)
        if not klines_df.empty:
            print(f"获取到 {len(klines_df)} 条K线数据")
            print(klines_df.head())
        
        # 测试技术分析
        print(f"\n测试{test_symbol}的技术分析:")
        analysis = analyze_trading_pair(test_symbol)
        if analysis:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # 测试分析多个交易对
    if pairs:
        print("\n测试分析多个交易对:")
        results = analyze_multiple_pairs(pairs, max_pairs=5)
        print(f"\n分析完成，共分析了 {len(results)} 个交易对")
        print("分析结果:")
        for result in results:
            print(f"{result['symbol']}: 价格={result['latest_price']:.2f}, 信号={result['signal']}, RSI={result['rsi']:.2f}")
        
        # 保存分析结果
        save_analysis_results(results)
