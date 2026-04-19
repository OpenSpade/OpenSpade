import requests
import json
import pandas as pd
import numpy as np
import time
import sqlite3
import os
import concurrent.futures
from datetime import datetime

# 数据库文件路径
DB_FILE = "binance_futures.db"

# 请求头，模拟浏览器请求
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Content-Type': 'application/json'
}

# 请求间隔时间（秒）
REQUEST_INTERVAL = 0.1

# 最大线程数
MAX_WORKERS = 10

def init_database():
    """
    初始化SQLite数据库，创建必要的表
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trading_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS klines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            latest_price REAL NOT NULL,
            price_change REAL,
            rsi REAL,
            ma10 REAL,
            ma20 REAL,
            ma50 REAL,
            macd REAL,
            macd_signal REAL,
            macd_hist REAL,
            volatility REAL,
            volume REAL,
            volume_change REAL,
            signal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"数据库 {DB_FILE} 初始化完成")

def save_trading_pairs_to_db(pairs):
    """
    保存交易对列表到数据库
    """
    if not pairs:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for symbol in pairs:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO trading_pairs (symbol) VALUES (?)",
                (symbol,)
            )
        except Exception as e:
            print(f"保存交易对 {symbol} 时出错: {e}")

    conn.commit()
    conn.close()
    print(f"已保存 {len(pairs)} 个交易对到数据库")

def save_klines_to_db(symbol, df):
    """
    保存K线数据到数据库
    """
    if df.empty:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO klines
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                str(row['timestamp']),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume'])
            ))
        except Exception as e:
            print(f"保存 {symbol} K线数据时出错: {e}")

    conn.commit()
    conn.close()

def save_analysis_to_db(analysis_result):
    """
    保存分析结果到数据库
    """
    if not analysis_result:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO analysis_results
            (symbol, latest_price, price_change, rsi, ma10, ma20, ma50,
             macd, macd_signal, macd_hist, volatility, volume, volume_change, signal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_result['symbol'],
            float(analysis_result['latest_price']),
            float(analysis_result['price_change']),
            float(analysis_result['rsi']) if not pd.isna(analysis_result['rsi']) else None,
            float(analysis_result['ma10']) if not pd.isna(analysis_result['ma10']) else None,
            float(analysis_result['ma20']) if not pd.isna(analysis_result['ma20']) else None,
            float(analysis_result['ma50']) if not pd.isna(analysis_result['ma50']) else None,
            float(analysis_result['macd']) if not pd.isna(analysis_result['macd']) else None,
            float(analysis_result['macd_signal']) if not pd.isna(analysis_result['macd_signal']) else None,
            float(analysis_result['macd_hist']) if not pd.isna(analysis_result['macd_hist']) else None,
            float(analysis_result['volatility']) if not pd.isna(analysis_result['volatility']) else None,
            float(analysis_result['volume']) if not pd.isna(analysis_result['volume']) else None,
            float(analysis_result['volume_change']) if not pd.isna(analysis_result['volume_change']) else None,
            analysis_result['signal']
        ))
        conn.commit()
    except Exception as e:
        print(f"保存分析结果时出错: {e}")
    finally:
        conn.close()

def get_trading_pairs_from_db():
    """
    从数据库获取交易对列表
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT symbol FROM trading_pairs ORDER BY symbol")
    pairs = [row[0] for row in cursor.fetchall()]

    conn.close()
    return pairs

def get_analysis_results_from_db(limit=100):
    """
    从数据库获取分析结果
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT symbol, latest_price, price_change, rsi, signal, created_at
        FROM analysis_results
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    results = []
    for row in cursor.fetchall():
        results.append({
            'symbol': row[0],
            'latest_price': row[1],
            'price_change': row[2],
            'rsi': row[3],
            'signal': row[4],
            'created_at': row[5]
        })

    conn.close()
    return results

def get_latest_analysis_from_db(symbol):
    """
    获取特定交易对的最新分析结果
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT symbol, latest_price, price_change, rsi, ma10, ma20, ma50,
               macd, macd_signal, macd_hist, volatility, volume, volume_change, signal, created_at
        FROM analysis_results
        WHERE symbol = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (symbol,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'symbol': row[0],
            'latest_price': row[1],
            'price_change': row[2],
            'rsi': row[3],
            'ma10': row[4],
            'ma20': row[5],
            'ma50': row[6],
            'macd': row[7],
            'macd_signal': row[8],
            'macd_hist': row[9],
            'volatility': row[10],
            'volume': row[11],
            'volume_change': row[12],
            'signal': row[13],
            'created_at': row[14]
        }
    return None

def get_klines_from_db(symbol, limit=100):
    """
    从数据库获取K线数据
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timestamp, open, high, low, close, volume
        FROM klines
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (symbol, limit))

    data = []
    for row in cursor.fetchall():
        data.append({
            'timestamp': row[0],
            'open': row[1],
            'high': row[2],
            'low': row[3],
            'close': row[4],
            'volume': row[5]
        })

    conn.close()
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_binance_futures_pairs():
    """
    获取币安期货合约交易对列表（仅USDT交易对）
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        symbols = data.get('symbols', [])
        trading_pairs = []

        for symbol in symbols:
            if symbol.get('status') == 'TRADING':
                symbol_name = symbol.get('symbol')
                if symbol_name and symbol_name.endswith('USDT'):
                    trading_pairs.append(symbol_name)

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
    """
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    try:
        time.sleep(REQUEST_INTERVAL)

        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

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
    """
    if df.empty:
        return df

    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    loss = loss.replace(0, 0.0001)
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']

    df['Volatility'] = df['close'].rolling(window=20).std()
    df['Volume_Change'] = df['volume'].pct_change()
    df['Price_Change'] = df['close'].pct_change()

    return df

def generate_trading_signal(df):
    """
    生成交易信号
    """
    if len(df) < 20:
        return "数据不足"

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    if latest['RSI'] > 70:
        rsi_signal = "超买"
    elif latest['RSI'] < 30:
        rsi_signal = "超卖"
    else:
        rsi_signal = "正常"

    if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
        macd_signal = "金叉"
    elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
        macd_signal = "死叉"
    else:
        macd_signal = "无"

    if latest['MA10'] > latest['MA20'] > latest['MA50']:
        ma_signal = "多头排列"
    elif latest['MA10'] < latest['MA20'] < latest['MA50']:
        ma_signal = "空头排列"
    else:
        ma_signal = "无"

    if rsi_signal == "超卖" and macd_signal == "金叉" and ma_signal == "多头排列":
        return "买入"
    elif rsi_signal == "超买" and macd_signal == "死叉" and ma_signal == "空头排列":
        return "卖出"
    else:
        return "持有"

def analyze_trading_pair(symbol, interval="1d", limit=100):
    """
    分析单个交易对，并保存到数据库
    """
    df = get_binance_futures_klines(symbol, interval, limit)
    if df.empty:
        return None

    save_klines_to_db(symbol, df)

    df = calculate_technical_indicators(df)

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

    analysis_result['signal'] = generate_trading_signal(df)

    save_analysis_to_db(analysis_result)

    return analysis_result

def analyze_multiple_pairs(pairs, interval="1d", limit=100, max_pairs=10):
    """
    分析多个交易对（使用多线程）
    """
    results = []
    target_pairs = pairs[:max_pairs]
    total_pairs = len(target_pairs)

    print(f"开始分析 {total_pairs} 个交易对，使用 {MAX_WORKERS} 个线程")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {
            executor.submit(analyze_trading_pair, symbol, interval, limit): symbol
            for symbol in target_pairs
        }

        for i, future in enumerate(concurrent.futures.as_completed(future_to_symbol)):
            symbol = future_to_symbol[future]
            try:
                analysis = future.result()
                if analysis:
                    results.append(analysis)
                    print(f"已完成 {i+1}/{total_pairs}: {symbol}")
                else:
                    print(f"分析失败 {i+1}/{total_pairs}: {symbol}")
            except Exception as e:
                print(f"分析 {symbol} 时出错: {e}")

    return results

def save_analysis_results_to_json(results, filename="analysis_results.json"):
    """
    保存分析结果到JSON文件
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"分析结果已保存到 {filename}")
    except Exception as e:
        print(f"保存分析结果时出错: {e}")

def show_database_stats():
    """
    显示数据库统计信息
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trading_pairs")
    pairs_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM klines")
    klines_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analysis_results")
    analysis_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT symbol, latest_price, signal, created_at
        FROM analysis_results
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    recent_results = cursor.fetchall()

    conn.close()

    print("\n" + "="*50)
    print("数据库统计信息")
    print("="*50)
    print(f"交易对数量: {pairs_count}")
    print(f"K线数据数量: {klines_count}")
    print(f"分析结果数量: {analysis_count}")
    print("\n最新分析结果:")
    print("-"*50)
    for result in recent_results:
        print(f"{result[0]}: 价格={result[1]:.2f}, 信号={result[2]}, 时间={result[3]}")
    print("="*50)

if __name__ == "__main__":
    init_database()

    pairs = get_binance_futures_pairs()
    print(f"获取到 {len(pairs)} 个币安期货USDT交易对")
    print("前10个交易对:")
    for pair in pairs[:10]:
        print(pair)

    save_trading_pairs_to_db(pairs)

    if pairs:
        test_symbol = pairs[0]
        print(f"\n测试分析 {test_symbol}:")
        analysis = analyze_trading_pair(test_symbol)
        if analysis:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))

    if pairs:
        print("\n开始多线程分析交易对...")
        start_time = time.time()
        results = analyze_multiple_pairs(pairs, max_pairs=20)
        end_time = time.time()
        print(f"\n分析完成，共分析了 {len(results)} 个交易对，耗时 {end_time - start_time:.2f} 秒")

        save_analysis_results_to_json(results)

    show_database_stats()

    print("\n从数据库读取最新分析结果:")
    db_results = get_analysis_results_from_db(5)
    for result in db_results:
        print(f"{result['symbol']}: 价格={result['latest_price']:.2f}, 信号={result['signal']}")
