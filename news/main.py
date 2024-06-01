# main.py

import schedule
import time
import logging
from fetch_news import fetch_and_store_news, process_news
from analyze_summaries import job as analyze_summaries_job
from telegram_bot import fetch_and_send_latest_analysis
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def job():
    fetch_and_store_news()
    process_news()
    analyze_summaries_job()
    fetch_and_send_latest_analysis()

def start_fetch_news_scheduler():
    schedule.every(1).days.at("09:00:00").do(job)
    schedule.every(1).days.at("21:00:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(10)

def main():
    # Use threading to run the schedulers concurrently
    fetch_thread = threading.Thread(target=start_fetch_news_scheduler)
    # telegram_thread = threading.Thread(target=start_telegram_bot_scheduler)

    # Start the threads
    fetch_thread.start()
    # telegram_thread.start()

    # Join the threads
    fetch_thread.join()
    # telegram_thread.join()

if __name__ == "__main__":
    main()