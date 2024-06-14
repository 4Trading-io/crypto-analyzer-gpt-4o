import logging
import asyncio
import os
import subprocess
import cv2
import base64
from datetime import datetime
from openai import OpenAI
from aiogram import Dispatcher, Bot
from youtube_rss import YoutubeFeedParser
from credentials import (
    telegram_bot_token_btc,
    telegram_channel_id,
    openai_api_key,
    arzineh_channel_id,
    altcoin_daily_channel_id,
    crypto_rover_channel_id,
    glassnode_channel_id,
    crypto_bureau_channel_id,
    crypto_jebb_channel_id,
    michael_wrubel_channel_id,
    arzineh_plus_channel_id,
    more_crypto_online_channel_id,
    bitboy_channel_id,
    bitcoin999_channel_id,
    cryptorus_channel_id,
    ivan_on_tech_channel_id
)

telegram_token = telegram_bot_token_btc
channel_id = telegram_channel_id
bot = Bot(token=telegram_token)
dp = Dispatcher()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI configuration
MODEL = "gpt-4o"
client = OpenAI(api_key=openai_api_key)

channel_id_post = telegram_channel_id # Channel ID for posting the final summary

# Function to download video and extract audio
def download_video_and_extract_audio(video_url, output_dir='downloads'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_output_path = os.path.join(output_dir, f'video_{current_time}.mp4')
    audio_output_path = os.path.join(output_dir, f'audio_{current_time}.mp3')

    # Download video in the lowest quality
    video_command = ['yt-dlp', '-f', 'worst', '-o', video_output_path, '--verbose', video_url]
    subprocess.run(video_command, check=True)
    logger.info(f"Video downloaded to {video_output_path} in the lowest quality available.")

    # Extract audio as MP3
    audio_command = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', audio_output_path, '--verbose', video_url]
    subprocess.run(audio_command, check=True)
    logger.info(f"Audio extracted to {audio_output_path}.")

    return video_output_path, audio_output_path

# Function to process video and extract frames
def process_video(video_path, max_frames=100):
    try:
        base64Frames = []
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError(f"Failed to open video file {video_path}")

        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_skip = max(1, total_frames // max_frames)
        curr_frame = 0

        logger.info(f"Processing video {video_path} with {total_frames} frames")

        while len(base64Frames) < max_frames and curr_frame < total_frames:
            video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
            success, frame = video.read()
            if not success:
                logger.warning(f"Failed to read frame at position {curr_frame}")
                break
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
            curr_frame += frames_to_skip

        video.release()
        logger.info(f"Extracted {len(base64Frames)} frames from the video")

        return base64Frames

    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        return []

# Function to send message to a Telegram channel
async def send_message_to_telegram_channel(message, channel_id, reply_to_message_id=None):
    try:
        logger.info(f"Attempting to send message to Telegram channel {channel_id}")
        message_chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]

        first_message_id = None
        for chunk in message_chunks:
            try:
                sent_message = await bot.send_message(chat_id=channel_id, text=chunk, reply_to_message_id=reply_to_message_id, parse_mode='Markdown')
            except:
                sent_message = await bot.send_message(chat_id=channel_id, text=chunk, reply_to_message_id=reply_to_message_id)

            if first_message_id is None:
                first_message_id = sent_message.message_id

            # Set reply_to_message_id to the ID of the last sent message to chain the messages
            reply_to_message_id = sent_message.message_id

        logger.info(f"Message sent to Telegram channel {channel_id}")
        return first_message_id
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {e}", exc_info=True)
    return None

# Function to send audio to Whisper for transcription and then summarize
async def send_audio_to_whisper_and_summarize(author, audio_path, video_frames, video_url, reply_to_message_id=None):
    try:
        # Transcribe the audio
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        logger.info(f"Transcription object: {transcription}a")
        transcription_text = transcription.text
        logger.info(f"Transcription: {transcription_text}")

        # Summarize the audio transcription in Farsi
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "شما یک خلاصه برای یک ویدیو تحلیل تکنیکال یا تحلیل فاندامنتال کریپتو است تولید می‌کنید. خلاصه را به فارسی بنویسید و نکات مهم را برجسته کنید."},
                {"role": "user", "content": f"رونویسی صوتی این است: {transcription_text}"}
            ],
            temperature=0,
        )
        audio_summary = response.choices[0].message.content
        logger.info(f"Audio Summary: {audio_summary}")

        # Summarize the video frames and audio transcription in Farsi
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": " شما در حال تولید خلاصه‌ای از یک ویدیو تحلیل تکنیکال یا بررسی کریپتو و اخبار آن هستید. تولید کننده ویدیو یک متخصص بازار کریپتو است.ویدیو را کمی خلاصه کنید خلاصه را به فارسی بنویسید و نکات مهم را برجسته کنید و از دیدن کل ویدیو مارا بی نیاز کنید و تاجای ممکن تمامی نکات و قیمت هارا بگو و همجنین بگو که چه فایده‌ای برای ما خواهد داشت این ویدیو."},
                {"role": "user", "content": [
                    "این‌ها فریم‌های ویدیو هستند.",
                    *map(lambda x: {"type": "image_url", "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "low"}}, video_frames),
                    {"type": "text", "text": f"رونویسی صوتی این است: {transcription_text}"}
                ]}
            ],
            temperature=0,
        )
        full_summary = response.choices[0].message.content
        logger.info(f"Full Summary: {full_summary}")

        # Add the video link and source text to the summary
        full_summary += f"\nمنبع: [{author}]({video_url})"

        # Send the summary to the Telegram channel as a reply
        await send_message_to_telegram_channel(full_summary, channel_id_post, reply_to_message_id)

    except Exception as e:
        logger.error(f"Error in summarization: {e}", exc_info=True)

# Callback function to handle new video
async def on_new_video(video):
    video_url = video.link
    author = video.author
    logger.info(f"New Video Received: {video.title} - {video_url}")
    video_path, audio_path = download_video_and_extract_audio(video_url)
    video_frames = process_video(video_path)

    # Send the audio to Whisper for transcription and summarization
    await send_audio_to_whisper_and_summarize(author, audio_path, video_frames, video_url)

# Main function to start the RSS feed parser and monitor for new videos
async def main():
    channel_ids = [
        arzineh_channel_id,
        arzineh_plus_channel_id,
        altcoin_daily_channel_id,
        crypto_rover_channel_id,
        crypto_bureau_channel_id,
        glassnode_channel_id,
        michael_wrubel_channel_id,
        crypto_jebb_channel_id,
        more_crypto_online_channel_id,
        bitboy_channel_id,
        bitcoin999_channel_id,
        cryptorus_channel_id,
        ivan_on_tech_channel_id
    ]

    feeds = [ YoutubeFeedParser(channel_id) for channel_id in channel_ids ]
    tasks = [ fp.check_always_async(on_new_video) for fp in feeds ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
