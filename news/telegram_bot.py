import logging
import os
from aiogram import Bot, Dispatcher
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, AnalyzedNews
import schedule
import time
from credentials import telegram_bot_token_news, telegram_channel_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram bot configuration
telegram_token = telegram_bot_token_news
channel_id = telegram_channel_id
bot = Bot(token=telegram_token)
dp = Dispatcher()

# Database configuration
DATABASE_URL = 'sqlite:///news_data.db'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

async def send_message_to_telegram(message):
    try:
        max_length = 4096
        parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        
        for part in parts:
            try:
                await bot.send_message(chat_id=channel_id, text=part, parse_mode='Markdown')
            except:
                logging.exception(f"could not send formatted message: {part}")
                await bot.send_message(chat_id=channel_id, text=part)
        
        logging.info("Message sent to Telegram channel")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")
    finally:
        await bot.session.close()

def send_message(message):
    try:
        asyncio.run(send_message_to_telegram(message))
    except RuntimeError as e:
        if str(e) == 'Event loop is closed':
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(send_message_to_telegram(message))

def fetch_and_send_latest_analysis():
    session = Session()
    try:
        logging.info("Fetching the latest analysis to send to Telegram")
        latest_analysis = session.query(AnalyzedNews).filter(AnalyzedNews.sent == False).order_by(AnalyzedNews.id.desc()).first()
        latest_analysis.sent = True
        session.commit()
        
        if latest_analysis:
            logging.info(f"Latest analysis found with id {latest_analysis.id}")
            message = f"Analysis: {latest_analysis.analysis}"
            send_message(message)
            logging.info("Latest analysis sent to Telegram")
        else:
            logging.info("No analysis found")
    except Exception as e:
        logging.error(f"Error fetching or sending latest analysis: {e}")
    finally:
        session.close()

def job():
    logging.info("Starting scheduled job to send latest analysis to Telegram")
    fetch_and_send_latest_analysis()
    logging.info("Scheduled job completed")
