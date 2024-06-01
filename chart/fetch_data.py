import pandas as pd
import pandas_ta as ta
from binance.client import Client
import logging
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from credentials import binance_api_key, binance_secret_key
import time
import schedule
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Binance Client
api_key = binance_api_key
api_secret = binance_secret_key
client = Client(api_key, api_secret)

# Database setup
DATABASE_URL = 'sqlite:///indicators.db'  # Change this to your preferred database URL
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define the HistoricalData model
class HistoricalData(Base):
    __tablename__ = 'historical_data'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    interval = Column(String)
    timestamp = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

# Define the Indicators model
class Indicators(Base):
    __tablename__ = 'indicators'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    interval = Column(String)
    timestamp = Column(DateTime)
    rsi = Column(Integer)
    macd = Column(Integer)
    macd_signal = Column(Integer)
    macd_diff = Column(Integer)
    ema_25 = Column(Float)
    ema_50 = Column(Float)
    ema_100 = Column(Float)
    ema_200 = Column(Float)
    ema_25_cross_ema_50 = Column(String)
    ema_25_cross_ema_100 = Column(String)
    ema_25_cross_ema_200 = Column(String)
    ema_50_cross_ema_100 = Column(String)
    ema_50_cross_ema_200 = Column(String)
    ema_100_cross_ema_200 = Column(String)
    bollinger_hband = Column(Float)
    bollinger_mband = Column(Float)
    bollinger_lband = Column(Float)
    pivot = Column(Float)
    pivot_res1 = Column(Float)
    pivot_sup1 = Column(Float)
    pivot_res2 = Column(Float)
    pivot_sup2 = Column(Float)
    minor_pivot = Column(Float)
    minor_pivot_res1 = Column(Float)
    minor_pivot_sup1 = Column(Float)
    minor_pivot_res2 = Column(Float)
    minor_pivot_sup2 = Column(Float)
    fib_38_2 = Column(Float)
    fib_61_8 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    stoch_k = Column(Float)
    stoch_d = Column(Float)
    cci = Column(Float)
    atr = Column(Float)
    obv = Column(Float)
    williams_r = Column(Float)
    wedge_pattern = Column(Integer)
    triangle_pattern = Column(Integer)
    double_top_pattern = Column(Integer)
    double_bottom_pattern = Column(Integer)
    fvg_pattern = Column(Integer)
    head_and_shoulders = Column(Integer)
    harmonic_pattern = Column(Integer)
# Create tables
Base.metadata.create_all(engine)

def fetch_historical_data(symbol, interval, start_str):
    try:
        logging.info(f"Fetching historical data for {symbol} at interval {interval} starting from {start_str}")
        
        # Retrieve historical data from Binance API
        klines = client.get_historical_klines(symbol, interval, start_str)
        if not klines:
            logging.error("No data fetched from Binance API")
            return pd.DataFrame()
        
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data = data.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
        
        if data.empty or len(data) < 50:  # Adjust the threshold as needed
            logging.error("Insufficient data to calculate indicators")
            return pd.DataFrame()
        
        logging.info(f"Fetched {len(data)} rows of data for {symbol} at interval {interval}")
        return data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}", exc_info=True)
        return pd.DataFrame()
    
# Indicators and Oscillator Calculation
def calculate_indicators(data):
    try:
        data['rsi'] = ta.rsi(data['close'], length=14)
        macd = ta.macd(data['close'])
        if macd is not None:
            data['macd'] = macd['MACD_12_26_9']
            data['macd_signal'] = macd['MACDs_12_26_9']
            data['macd_diff'] = macd['MACDh_12_26_9']
        else:
            data['macd'] = None
            data['macd_signal'] = None
            data['macd_diff'] = None
        bbands = ta.bbands(data['close'], length=20, std=2)
        if bbands is not None:
            data['bollinger_hband'] = bbands['BBU_20_2.0']
            data['bollinger_mband'] = bbands['BBM_20_2.0']
            data['bollinger_lband'] = bbands['BBL_20_2.0']
        else:
            data['bollinger_hband'] = None
            data['bollinger_mband'] = None
            data['bollinger_lband'] = None

        data['ema_25'] = ta.ema(data['close'], length=25)
        data['ema_50'] = ta.ema(data['close'], length=50)
        data['ema_100'] = ta.ema(data['close'], length=100)
        data['ema_200'] = ta.ema(data['close'], length=200)

        # Calculate SMA, STOCH and ..  indicators
        data['sma_50'] = ta.sma(data['close'], length=50)
        data['sma_200'] = ta.sma(data['close'], length=200)
        stoch = ta.stoch(data['high'], data['low'], data['close'])
        if stoch is not None:
            data['stoch_k'] = stoch['STOCHk_14_3_3']
            data['stoch_d'] = stoch['STOCHd_14_3_3']
        else:
            data['stoch_k'] = None
            data['stoch_d'] = None
        data['cci'] = ta.cci(data['high'], data['low'], data['close'], length=20)
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=14)
        data['obv'] = ta.obv(data['close'], data['volume'])
        data['williams_r'] = ta.willr(data['high'], data['low'], data['close'], length=14)

        data['ema_25'].fillna(0, inplace=True)
        data['ema_50'].fillna(0, inplace=True)
        data['ema_100'].fillna(0, inplace=True)
        data['ema_200'].fillna(0, inplace=True)

        data['ema_25'].ffill(inplace=True)
        data['ema_50'].ffill(inplace=True)
        data['ema_100'].ffill(inplace=True)
        data['ema_200'].ffill(inplace=True)

        data['ema_25'].bfill(inplace=True)
        data['ema_50'].bfill(inplace=True)
        data['ema_100'].bfill(inplace=True)
        data['ema_200'].bfill(inplace=True)

        # Detect EMA crosses
        data['ema_25_cross_ema_50'] = detect_ema_cross(data['ema_25'], data['ema_50'])
        data['ema_25_cross_ema_100'] = detect_ema_cross(data['ema_25'], data['ema_100'])
        data['ema_25_cross_ema_200'] = detect_ema_cross(data['ema_25'], data['ema_200'])
        data['ema_50_cross_ema_100'] = detect_ema_cross(data['ema_50'], data['ema_100'])
        data['ema_50_cross_ema_200'] = detect_ema_cross(data['ema_50'], data['ema_200'])
        data['ema_100_cross_ema_200'] = detect_ema_cross(data['ema_100'], data['ema_200'])

        data = calculate_major_pivots(data)
        data = calculate_minor_pivots(data)
        data = calculate_fibonacci_levels(data)

        # Detect FVG
        data['fvg_pattern'] = detect_fvg(data)

        # Detect patterns
        data['head_and_shoulders'] = detect_head_and_shoulders(data)
        data['harmonic_pattern'] = detect_harmonic_pattern(data)
        data['wedge_pattern'] = detect_wedge(data)
        data['triangle_pattern'] = detect_triangle(data)
        data['double_top_pattern'] = detect_double_top(data)
        data['double_bottom_pattern'] = detect_double_bottom(data)

        logging.info("Calculated RSI, MACD, Bollinger Bands, EMA crosses, major and minor pivots, Fibonacci levels, SMAs, Stochastic, CCI, ATR, OBV, and Williams %R")
        return data
    except Exception as e:
        logging.error(f"Error calculating indicators: {e}", exc_info=True)
        return pd.DataFrame()



def detect_ema_cross(ema_short, ema_long):
    cross_up = (ema_short.shift(1) <= ema_long.shift(1)) & (ema_short > ema_long)
    cross_down = (ema_short.shift(1) >= ema_long.shift(1)) & (ema_short < ema_long)
    return cross_up.astype(int) - cross_down.astype(int)

  
def calculate_major_pivots(data):
    """
    Calculate major pivot points for given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low', 'close'].
    
    Returns:
    DataFrame: The original DataFrame with additional columns for major pivots and their support and resistance levels.
    """
    data['pivot'] = (data['high'].shift(1) + data['low'].shift(1) + data['close'].shift(1)) / 3
    data['pivot_res1'] = 2 * data['pivot'] - data['low'].shift(1)
    data['pivot_sup1'] = 2 * data['pivot'] - data['high'].shift(1)
    data['pivot_res2'] = data['pivot'] + (data['high'].shift(1) - data['low'].shift(1))
    data['pivot_sup2'] = data['pivot'] - (data['high'].shift(1) - data['low'].shift(1))
    
    return data

def calculate_minor_pivots(data, window=10):
    """
    Calculate minor pivot points for given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low', 'close'].
    window (int): The number of periods to use for rolling calculations (default is 10).
    
    Returns:
    DataFrame: The original DataFrame with additional columns for minor pivots and their support and resistance levels.
    """
    if len(data) < window:
        raise ValueError("Not enough data to calculate minor pivots")
    
    high = data['high'].rolling(window=window, min_periods=1).max()
    low = data['low'].rolling(window=window, min_periods=1).min()
    close = data['close'].shift(-(window-1)).rolling(window=window, min_periods=1).apply(lambda x: x[0] if len(x) == window else np.nan, raw=True)

    pivot = (high + low + close) / 3
    res1 = 2 * pivot - low
    sup1 = 2 * pivot - high
    res2 = pivot + (high - low)
    sup2 = pivot - (high - low)

    data['minor_pivot'] = pivot
    data['minor_pivot_res1'] = res1
    data['minor_pivot_sup1'] = sup1
    data['minor_pivot_res2'] = res2
    data['minor_pivot_sup2'] = sup2
    
    return data

def detect_fvg(data, window=10):
    """
    Detect Fair Value Gaps (FVG) in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low'].
    window (int): The number of periods to look back for detecting gaps (default is 10).
    
    Returns:
    np.array: An array indicating the presence of FVGs (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))
    
    # Iterate over the data with the specified window
    for i in range(window, len(data)):
        for j in range(1, window + 1):
            prev_high = data['high'][i-j]
            prev_low = data['low'][i-j]
            current_high = data['high'][i]
            current_low = data['low'][i]
            
            # Detect gap up
            if current_low > prev_high:
                patterns[i] = 1
                break  # Break to avoid multiple detections for the same index

            elif current_high < prev_low:
                patterns[i] = 1
                break  # Break to avoid multiple detections for the same index
    
    return patterns

def detect_double_top(data, window=10, tolerance=0.02):
    """
    Detect double top patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low', 'close'].
    window (int): The number of periods to use for the rolling window to detect peaks.
    tolerance (float): The tolerance level for peak matching.
    
    Returns:
    np.array: An array indicating the presence of double top patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))
    
    if len(data) < window:
        return patterns
    
    for i in range(window, len(data)):
        highs = data['high'][i-window:i]
        
        if len(highs) < window:
            continue
        max1 = highs.max()
        max1_idx = highs.idxmax()
        highs_excluding_max1 = highs.drop(max1_idx)
        if highs_excluding_max1.empty:
            continue
        
        max2 = highs_excluding_max1.max()
        max2_idx = highs_excluding_max1.idxmax()

        if max2_idx < max1_idx:
            continue
        if abs(max1 - max2) / max1 < tolerance:
            if data['close'][i] < highs.mean():
                patterns[i] = 1
    
    return patterns


def detect_double_bottom(data, window=10, tolerance=0.02):
    """
    Detect double bottom patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low', 'close'].
    window (int): The number of periods to use for the rolling window to detect troughs.
    tolerance (float): The tolerance level for trough matching.
    
    Returns:
    np.array: An array indicating the presence of double bottom patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))
    
    if len(data) < window:
        return patterns
    
    for i in range(window, len(data)):
        lows = data['low'][i-window:i]
        
        if len(lows) < window:
            continue
        min1 = lows.min()
        min1_idx = lows.idxmin()

        lows_excluding_min1 = lows.drop(min1_idx)
        if lows_excluding_min1.empty:
            continue
        
        min2 = lows_excluding_min1.min()
        min2_idx = lows_excluding_min1.idxmax()

        if min2_idx < min1_idx:
            continue

        if abs(min1 - min2) / min1 < tolerance:
            if data['close'][i] > lows.mean():
                patterns[i] = 1
    
    return patterns

def detect_triangle(data, window=10, tolerance=0.02):
    """
    Detect triangle patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low'].
    window (int): The number of periods to use for the rolling window to detect trend lines.
    tolerance (float): The tolerance level for pattern matching.
    
    Returns:
    np.array: An array indicating the presence of triangle patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))
    
    if len(data) < window:
        return patterns
    
    for i in range(window, len(data)):
        highs = data['high'][i-window:i]
        lows = data['low'][i-window:i]
        
        if len(highs) < window or len(lows) < window:
            continue
        
        high_slope = (highs.iloc[-1] - highs.iloc[0]) / window
        low_slope = (lows.iloc[-1] - lows.iloc[0]) / window
        
        if high_slope > 0 and low_slope > 0:
            if abs(highs.max() - highs.min()) / highs.min() < tolerance:
                patterns[i] = 1
        elif high_slope < 0 and low_slope < 0:
            if abs(lows.max() - lows.min()) / lows.min() < tolerance:
                patterns[i] = 1
        else:
            if abs(high_slope - low_slope) / max(abs(high_slope), abs(low_slope)) < tolerance:
                patterns[i] = 1
    
    return patterns

def detect_head_and_shoulders(data, tolerance=0.02):
    """
    Detect head and shoulders patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low', 'close'].
    tolerance (float): The tolerance level for pattern matching.
    
    Returns:
    np.array: An array indicating the presence of head and shoulders patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))

    for i in range(6, len(data)):
        left_shoulder = data['high'][i-6]
        head = data['high'][i-3]
        right_shoulder = data['high'][i]
        neckline = min(data['low'][i-5], data['low'][i-1])
        neckline = (neckline + data['low'][i-2]) / 2 

        if not (head > left_shoulder and head > right_shoulder):
            continue

        if not (left_shoulder * (1 - tolerance) <= right_shoulder <= left_shoulder * (1 + tolerance)):
            continue

        if data['close'][i] < neckline:
            patterns[i] = 1

    return patterns


def detect_wedge(data, window=10, tolerance=0.02):
    """
    Detect wedge patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low'].
    window (int): The number of periods to use for the rolling window to detect trend lines.
    tolerance (float): The tolerance level for pattern matching.
    
    Returns:
    np.array: An array indicating the presence of wedge patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))
    
    if len(data) < window:
        return patterns
    
    for i in range(window, len(data)):
        highs = data['high'][i-window:i]
        lows = data['low'][i-window:i]
        
        if len(highs) < window or len(lows) < window:
            continue
        
        high_slope = (highs.iloc[-1] - highs.iloc[0]) / window
        low_slope = (lows.iloc[-1] - lows.iloc[0]) / window

        if high_slope < 0 and low_slope < 0:
            high_slope_2 = (highs.iloc[1] - highs.iloc[0]) / (window - 1)
            low_slope_2 = (lows.iloc[1] - lows.iloc[0]) / (window - 1)
            if high_slope_2 != 0 and low_slope_2 != 0 and \
               abs((high_slope - high_slope_2) / high_slope_2) < tolerance and \
               abs((low_slope - low_slope_2) / low_slope_2) < tolerance:
                patterns[i] = 1
        elif high_slope > 0 and low_slope > 0:
            high_slope_2 = (highs.iloc[1] - highs.iloc[0]) / (window - 1)
            low_slope_2 = (lows.iloc[1] - lows.iloc[0]) / (window - 1)
            if high_slope_2 != 0 and low_slope_2 != 0 and \
               abs((high_slope - high_slope_2) / high_slope_2) < tolerance and \
               abs((low_slope - low_slope_2) / low_slope_2) < tolerance:
                patterns[i] = 1
    
    return patterns

def detect_harmonic_pattern(data, tolerance=0.02):
    """
    Detect harmonic patterns in the given price data.
    
    Parameters:
    data (DataFrame): A DataFrame with columns ['high', 'low'].
    tolerance (float): The tolerance level for Fibonacci ratio matching.
    
    Returns:
    np.array: An array indicating the presence of harmonic patterns (1 if detected, else 0).
    """
    patterns = np.zeros(len(data))

    for i in range(5, len(data)):
        X = data['low'][i-5]
        A = data['high'][i-4]
        B = data['low'][i-3]
        C = data['high'][i-2]
        D = data['low'][i-1]
        current = data['low'][i]

        if not (0.618 - tolerance <= (B - X) / (A - X) <= 0.618 + tolerance):
            continue

        if not (0.382 - tolerance <= (C - A) / (A - B) <= 0.382 + tolerance or
                0.886 - tolerance <= (C - A) / (A - B) <= 0.886 + tolerance):
            continue

        if not (0.382 - tolerance <= (D - B) / (C - B) <= 0.382 + tolerance or
                0.886 - tolerance <= (D - B) / (C - B) <= 0.886 + tolerance):
            continue

        if not (1.618 - tolerance <= (current - C) / (C - D) <= 1.618 + tolerance or
                2.618 - tolerance <= (current - C) / (C - D) <= 2.618 + tolerance):
            continue

        patterns[i] = 1

    return patterns

def calculate_fibonacci_levels(data):
    try:
        high = data['high'].rolling(window=20).max()
        low = data['low'].rolling(window=20).min()
        data['fib_38_2'] = high - 0.382 * (high - low)
        data['fib_61_8'] = high - 0.618 * (high - low)
        return data
    except Exception as e:
        logging.error(f"Error calculating Fibonacci levels: {e}", exc_info=True)
        return data

def store_historical_data(symbol, interval, data):
    try:
        for index, row in data.iterrows():
            historical_data = HistoricalData(
                symbol=symbol,
                interval=interval,
                timestamp=row['timestamp'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            session.add(historical_data)
        session.commit()
        logging.info(f"Stored historical data for {symbol} at interval {interval} in database")
    except Exception as e:
        logging.error(f"Error storing historical data in database: {e}", exc_info=True)

def store_indicators_data(symbol, interval, data):
    try:
        for index, row in data.iterrows():
            indicators = Indicators(
                symbol=symbol,
                interval=interval,
                timestamp=row['timestamp'],
                rsi=row.get('rsi'),
                macd=row.get('macd'),
                macd_signal=row.get('macd_signal'),
                macd_diff=row.get('macd_diff'),
                ema_25=row.get('ema_25'),
                ema_50=row.get('ema_50'),
                ema_100=row.get('ema_100'),
                ema_200=row.get('ema_200'),
                ema_25_cross_ema_50=row.get('ema_25_cross_ema_50'),
                ema_25_cross_ema_100=row.get('ema_25_cross_ema_100'),
                ema_25_cross_ema_200=row.get('ema_25_cross_ema_200'),
                ema_50_cross_ema_100=row.get('ema_50_cross_ema_100'),
                ema_50_cross_ema_200=row.get('ema_50_cross_ema_200'),
                ema_100_cross_ema_200=row.get('ema_100_cross_ema_200'),
                bollinger_hband=row.get('bollinger_hband'),
                bollinger_mband=row.get('bollinger_mband'),
                bollinger_lband=row.get('bollinger_lband'),
                pivot=row.get('pivot'),
                pivot_res1=row.get('pivot_res1'),
                pivot_sup1=row.get('pivot_sup1'),
                pivot_res2=row.get('pivot_res2'),
                pivot_sup2=row.get('pivot_sup2'),
                minor_pivot=row.get('minor_pivot'),
                minor_pivot_res1=row.get('minor_pivot_res1'),
                minor_pivot_sup1=row.get('minor_pivot_sup1'),
                minor_pivot_res2=row.get('minor_pivot_res2'),
                minor_pivot_sup2=row.get('minor_pivot_sup2'),
                fib_38_2=row.get('fib_38_2'),
                fib_61_8=row.get('fib_61_8'),
                sma_50=row.get('sma_50'),
                sma_200=row.get('sma_200'),
                stoch_k=row.get('stoch_k'),
                stoch_d=row.get('stoch_d'),
                cci=row.get('cci'),
                atr=row.get('atr'),
                obv=row.get('obv'),
                williams_r=row.get('williams_r'),
                head_and_shoulders=row.get('head_and_shoulders'),
                harmonic_pattern=row.get('harmonic_pattern'),
                wedge_pattern=row.get('wedge_pattern'),
                triangle_pattern=row.get('triangle_pattern'),
                double_top_pattern=row.get('double_top_pattern'),
                double_bottom_pattern=row.get('double_bottom_pattern'),
                fvg_pattern=row.get('fvg_pattern')
            )
            session.add(indicators)
        session.commit()
        logging.info(f"Stored indicators data for {symbol} at interval {interval} in database")
    except Exception as e:
        logging.error(f"Error storing indicators data in database: {e}", exc_info=True)

def update_database(symbol, interval):
    try:
        session.query(HistoricalData).delete()
        session.query(Indicators).delete()
        last_record = None
        if last_record:
            start_str = last_record.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            if interval == '15m':
                start_str = '3 weeks ago UTC'
            elif interval == '4h':
                start_str = '25 weeks ago UTC'
            elif interval == '1d':
                start_str = '35 months ago UTC'
        
        data = fetch_historical_data(symbol, interval, start_str)
        if not data.empty:
            store_historical_data(symbol, interval, data)
            indicators = calculate_indicators(data)
            store_indicators_data(symbol, interval, indicators)
    except Exception as e:
        logging.error(f"Error updating database: {e}", exc_info=True)

def periodic_update(symbol, interval):
    try:
        logging.info(f"Starting periodic update for {symbol} at interval {interval}")
        session.query(HistoricalData).delete()
        session.query(Indicators).delete()
        last_record = None
        if last_record:
            start_str = last_record.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            if interval == '15m':
                start_str = '3 weeks ago UTC'
            elif interval == '4h':
                start_str = '25 weeks ago UTC'
            elif interval == '1d':
                start_str = '35 months ago UTC'
        
        data = fetch_historical_data(symbol, interval, start_str)
        if not data.empty:
            store_historical_data(symbol, interval, data)
            indicators = calculate_indicators(data)
            store_indicators_data(symbol, interval, indicators)
            logging.info(f"Periodic update completed for {symbol} at interval {interval}")
        else:
            logging.warning(f"No new data fetched for {symbol} at interval {interval}")
    except Exception as e:
        logging.error(f"Error during periodic update: {e}", exc_info=True)

def schedule_updates(symbols, intervals):
    for symbol in symbols:
        for interval in intervals:
            schedule.every(5).minutes.do(periodic_update, symbol=symbol, interval=interval)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main(intervals=None):
    if intervals is None:
        intervals = ['15m', '4h', '1d']  # Default intervals

    symbols = ['BTCUSDT', 'ETHUSDT']  # Example symbols

    # Initial data load
    for symbol in symbols:
        for interval in intervals:
            logging.info(f"Processing interval {interval} for symbol {symbol}")
            update_database(symbol, interval)

    # Schedule periodic updates
    schedule_updates(symbols, intervals)

    # Start the scheduler
    run_scheduler()

if __name__ == "__main__":
    main()
