from telethon import TelegramClient, events
import os
from datetime import datetime
import logging
import re
from credentials import telegram_api_hash, telegram_api_id, phone_number, telegram_group_id
# Use your own values here
api_id = telegram_api_id
api_hash = telegram_api_hash
phone_number = phone_number
group_id = telegram_group_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the client and connect
client = TelegramClient('session_name', api_id, api_hash)

# Folder to save images
output_folder = 'images'
os.makedirs(output_folder, exist_ok=True)

# Set the image counter based on existing files
existing_files = os.listdir(output_folder)
existing_numbers = [
    int(re.match(r'(\d+)', f).group()) for f in existing_files if re.match(r'(\d+)', f)
]
image_counter = max(existing_numbers) + 1 if existing_numbers else 1

async def download_image(event_or_message, date):
    global image_counter

    # Ensure the filename has a proper extension if it doesn't already
    extension = os.path.splitext(event_or_message.file.name or '')[1]
    if not extension:
        extension = '.png'
    
    filename = f'{image_counter:04d}_{date}{extension}'
    image_path = os.path.join(output_folder, filename)
    
    try:
        logger.info(f"Attempting to download media to {image_path}...")
        result = await event_or_message.download_media(file=image_path)
        if result:
            logger.info(f"Downloaded {filename} to {image_path}")
        else:
            logger.error(f"Failed to download media: No result returned")
    except Exception as e:
        logger.error(f"Failed to download media: {e}")

    image_counter += 1

@client.on(events.NewMessage(chats=group_id))
async def handler(event):
    logger.info(f"New message received. Message ID: {event.id}")
    if event.file:
        file_name = event.file.name or ''
        if file_name.endswith('.png') or event.file.mime_type == 'image/png':
            logger.info(f"Message has a .png file. Downloading...")
            date = event.date.strftime('%Y-%m-%d')
            await download_image(event, date)
    elif event.photo:
        file_name = await event.download_media(file=bytes)
        if file_name.endswith(b'.png'):
            logger.info(f"Message has a .png photo. Downloading...")
            date = event.date.strftime('%Y-%m-%d')
            await download_image(event, date)

async def check_last_messages(group):
    async for message in client.iter_messages(group, limit=7):  # Adjust the limit as needed
        logger.info(f"Checking message ID: {message.id}")
        if message.file:
            file_name = message.file.name or ''
            if file_name.endswith('.png') or message.file.mime_type == 'image/png':
                logger.info(f"Message has a .png file. Downloading...")
                date = message.date.strftime('%Y-%m-%d')
                await download_image(message, date)
        elif message.photo:
            file_name = await message.download_media(file=bytes)
            if file_name.endswith(b'.png'):
                logger.info(f"Message has a .png photo. Downloading...")
                date = message.date.strftime('%Y-%m-%d')
                await download_image(message, date)

async def main():
    await client.start(phone_number)

    logger.info("Client created and running. Checking for messages...")

    try:
        group = await client.get_entity(group_id)
    except ValueError as e:
        logger.error(f"Could not find the group entity: {e}")
        async for dialog in client.iter_dialogs():
            logger.info(f"{dialog.id}: {dialog.name}")
        return

    await check_last_messages(group)

    logger.info("Listening for new messages...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())