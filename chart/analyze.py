import pandas as pd
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from openai import OpenAI
import base64
import os
import re
from telegram_bot import send_message
from credentials import openai_api_key
from plot_chart import generate_chart_PNG_mpl_finance
from dateutil.relativedelta import relativedelta

# Database setup
DATABASE_URL = 'sqlite:///indicators.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Models for database tables
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

class Analysis(Base):
    __tablename__ = 'analysis'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    interval = Column(String)
    timestamp = Column(DateTime)
    analysis = Column(Text)
    image = Column(Text)

# Table creation
Base.metadata.create_all(engine)

# OpenAI Authentication 
client = OpenAI(api_key=openai_api_key)

# Function to fetch data to send to send to chatgpt 
def fetch_data(symbol, interval):
    try:
        end_time = datetime.utcnow()
        
        # Data period based on interval
        if interval == '4h':
            start_time = end_time - timedelta(weeks=24)
        elif interval == '1d':
            start_time = end_time - relativedelta(months=34)
        elif interval == '15m':
            start_time = end_time - relativedelta(weeks=2)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        historical_query = session.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.interval == interval,
            HistoricalData.timestamp.between(start_time, end_time)
        )
        historical_data = pd.read_sql(historical_query.statement, historical_query.session.bind)
        
        indicators_query = session.query(Indicators).filter(
            Indicators.symbol == symbol,
            Indicators.interval == interval,
            Indicators.timestamp.between(start_time, end_time)
        )
        indicators_data = pd.read_sql(indicators_query.statement, indicators_query.session.bind)
        
        logging.info(f"Fetched data for {symbol} at interval {interval} from {start_time} to {end_time}")
        return historical_data, indicators_data
    except Exception as e:
        logging.error(f"Error fetching data from database: {e}", exc_info=True)
        return pd.DataFrame(), pd.DataFrame()

def merge_data(historical_data, indicators_data):
    try:
        data = pd.merge(historical_data, indicators_data, on=['symbol', 'interval', 'timestamp'])
        logging.info("Merged historical and indicators data")
        return data
    except Exception as e:
        logging.error(f"Error merging data: {e}", exc_info=True)
        return pd.DataFrame()


def generate_analysis(symbol, precision, interval, data:pd.DataFrame):
    
    # select last 400 rows
    gpt_data = data.iloc[-400:]
    
    pair_name = {"BTCUSDT":"بیت کوین","ETHUSDT":"اتریوم"}[symbol]
    
    try:
        # ChatGPT Response Template
        template = f"_تحلیل ارز دیجیتال {pair_name} توسط یک هوش مصنوعی_" + """

        نماد: *{symbol}*
        بازه زمانی: *{interval}*
        قیمت فعلی : *{current_price}*
        تاریخ: *{date}*

        *شاخص‌های تکنیکال:*
        - خرید یا فروش EMA: {ema_signal}  
        - خرید یا فروش MACD: {macd_signal}  
        - خرید یا فروش RSI: {rsi_signal}
        - خرید یا فروش SMA : {sma_signal}
        - خرید یا فروش Stochastic: {stoch_signal}
        - سیگنال CCI: {cci_signal}
        - سیگنال ATR: {atr_value}
        - سیگنال OBV: {obv_value}
        - خرید یا فروش Williams %R: {williams_r_signal}

        *تحلیل بر اساس فیبوناچی، خط روند و پیوت‌های اصلی و فرعی:*
        {fibo_trend_pivot_analysis}

        *سطوح حمایت و مقاومت:*
        - سطح حمایت: {support_level}
        - سطح مقاومت: {resistance_level}

        *پیش‌بینی یک روز آینده و یک هفته آینده:*
        {predictions}
        
        *سیگنال پرپچوال*
        - جهت: {direction}
        - نقطه ورود: {entry}
        - اهرم: {leverage}x
        - تارگت: {target}
        - حد ضرر: {stop_loss}

        *هشدار: این تحلیل های هوش مصنوعی است. تنها یک ابزار است 

        """
        
        # Message Prompt to ChatGPT
        message = f"""
        Provide a technical analysis in Farsi for the following data using this template.
        use price action and smart money in your analysis and signals.
        use integer numbers only.
        if there is any pattern detected or FVG mention it on your analyze. also tell us about elliot waves and wave counting and forecast of elliot waves. 
        if the situation of market was suitable for trading provide signal if not tell it is not good time to trade. 
        also provide signal with reaction strategies if it is a good opportunity, also signal with swing strategies. 
        remember risk management in proving signals.

        {template}

        Data:
        {gpt_data.to_csv(index=False, float_format=f'%.{precision}f')}
        """

        # Generate the main analysis using GPT-4o
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a master of Crypto Technical Analysis."},
                {"role": "user", "content": message}
            ]
        )
        analysis = completion.choices[0].message.content
        
        # Replace Hashtags
        analysis = re.sub(r'#(\w+)', lambda m: '#' + m.group(1).replace('_', '\\_'), analysis)
        
        
        analysis = analysis \
            .replace('```','') \
            .replace('***','*') \
            .replace('**','*') \
            .replace('___','_') \
            .replace('__','_') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('  ',' ') \
            .replace('<mark>','_') \
            .replace('</mark>','_') \
            .strip()
            
        analysis +="\n\n\n _با ما همراه باشید برای تحلیل‌های بیشتر!_"
        analysis +="\n#ارز\\_دیجیتال #تحلیل\\_تکنیکال #" + pair_name.replace(' ','\\_')

        print(analysis)
        logging.info("Generated analysis using GPT-4o")
        return analysis
    except Exception as e:
        logging.error(f"Error generating analysis with GPT-4o: {e}", exc_info=True)
        return "Error generating analysis."

def store_analysis(symbol, interval, analysis, image_file_name):
    try:
        analysis_record = Analysis(
            symbol=symbol,
            interval=interval,
            timestamp=datetime.utcnow(),
            analysis=analysis,
            image=image_file_name
        )
        session.add(analysis_record)
        session.commit()
        logging.info(f"Stored analysis for {symbol} at interval {interval} in database")
    except Exception as e:
        logging.error(f"Error storing analysis in database: {e}", exc_info=True)

def main(symbols, intervals):
    for symbol, precision in symbols:
        for interval in intervals:
            historical_data, indicators_data = fetch_data(symbol, interval)
            if not historical_data.empty and not indicators_data.empty:
                data = merge_data(historical_data, indicators_data)
                analysis = generate_analysis(symbol, precision, interval, data)
                
                image_file_name = generate_chart_PNG_mpl_finance(symbol,'BINANCE',interval,analysis,data)
                
                store_analysis(symbol, interval, analysis, image_file_name)

                # Sending chatgpt response to Telegram channel 
                logging.info(f"Sending analysis to Telegram for {symbol}")
                send_message(analysis, symbol, interval, image_file_name)

                print("Technical Analysis Done:")
