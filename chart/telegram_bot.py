import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
import asyncio
from credentials import telegram_bot_token_btc, telegram_channel_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Telegram Bot
telegram_token = telegram_bot_token_btc
channel_id = telegram_channel_id
bot = Bot(token=telegram_token)
dp = Dispatcher()

# Store the message IDs of the last analysis for each symbol
last_message_ids = {'BTCUSDT': None, 'ETHUSDT': None}

# Function to send message to Telegram channel
async def send_message_to_telegram(message, symbol, interval, image_file_name):
    try:
        max_length = 4096  # Telegram's maximum message length
        parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        reply_to_message_id = None # last_message_ids[symbol]
        logging.info(f"Uploading Photo {image_file_name} to {channel_id}")
        with open(image_file_name,"rb") as f:
            msg = await bot.send_photo(chat_id=channel_id, photo=BufferedInputFile(f.read(), image_file_name) , caption=f"{symbol} {interval} chart")
        
        reply_to_message_id = msg.message_id
        
        logging.info(f"Sending message to {channel_id}")
        for part in parts:
            if reply_to_message_id:
                try:
                    msg = await bot.send_message(chat_id=channel_id, text=part, parse_mode='Markdown', reply_to_message_id=reply_to_message_id)
                except:
                    logging.exception(f"could not send formatted message: {part}")
                    msg = await bot.send_message(chat_id=channel_id, text=part, reply_to_message_id=reply_to_message_id)
                    
            else:
                try:
                    msg = await bot.send_message(chat_id=channel_id, text=part, parse_mode='Markdown')
                except:
                    logging.exception(f"could not send formatted message: {part}")
                    msg = await bot.send_message(chat_id=channel_id, text=part)
            reply_to_message_id = msg.message_id
        
        last_message_ids[symbol] = reply_to_message_id
        logging.info(f"Message sent to Telegram channel for {symbol}")
    except Exception as e:
        logging.exception(f"Error sending message to Telegram: {e}")
    finally:
        await bot.session.close()

def send_message(message, symbol, interval, image_file_name):
    try:
        asyncio.run(send_message_to_telegram(message, symbol, interval, image_file_name))
    except RuntimeError as e:
        if str(e) == 'Event loop is closed':
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(send_message_to_telegram(message, symbol, interval, image_file_name))