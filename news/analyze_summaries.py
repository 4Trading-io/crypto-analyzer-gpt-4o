# analyzed_summaries.py

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SummarizedNews, AnalyzedNews
from openai import OpenAI
import schedule
import time
import re
from credentials import openai_api_key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
DATABASE_URL = 'sqlite:///news_data.db'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

def analyze_summaries_with_gpt4(summaries):
    try:
        logging.info("Sending summaries to GPT-4 for analysis")
        combined_summaries = " ".join(summaries)
        instruction = f"""
        شما یک تحلیلگر بنیادی رمز ارز هستید. بر اساس خلاصه اخبار رمز ارزهای زیر، یک تحلیل جامع و دقیق به زبان فارسی برای کانال تلگرام تهیه کنید. تحلیل شما باید شامل بخش‌های زیر باشد:

        1. **مرور کلی**:
           - یک نمای کلی از وضعیت فعلی بازار رمز ارزها ارائه دهید.

        2. **نکات کلیدی**:
           - مهمترین اخبار خلاصه‌ها را برجسته کنید.
           - تاثیرات بالقوه این اخبار بر بازار را توضیح دهید.

        3. **پیامدها**:
           - پیامدهای این اخبار برای سرمایه‌گذاران و معامله‌گران را بحث کنید.
           - استراتژی‌ها یا اقداماتی را بر اساس اخبار پیشنهاد دهید.

        4. **نتیجه‌گیری**:
           - تحلیل کلی خود را خلاصه کنید و هر گونه نکته نهایی را بیان کنید.

        5. **پیش‌بینی و توصیه‌ها**:
           - بر اساس تحلیل انجام‌شده، پیش‌بینی‌های خود را برای روندهای آینده بازار بیان کنید.
           - توصیه‌های عملی برای خوانندگان ارائه دهید.


        اینجا خلاصه اخبار هستند: {combined_summaries}
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a crypto fundamental analyzer."},
                {"role": "user", "content": instruction}
            ]
        )
        analysis = completion.choices[0].message.content
        logging.info("Received analysis from GPT-4")
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
        
        return analysis
    except Exception as e:
        logging.error(f"Error during GPT-4 analysis: {e}")
        return None

def process_summaries():
    session = Session()
    try:
        logging.info("Fetching summaries for analysis")
        # Fetch only summaries that have not been processed
        summaries = session.query(SummarizedNews).filter(SummarizedNews.processed == False).all()
        logging.info(f"Found {len(summaries)} summaries to analyze")

        if summaries:
            summaries_texts = [summary.summary for summary in summaries]
            analysis = analyze_summaries_with_gpt4(summaries_texts)
            if analysis:
                for summary in summaries:
                    # Store the analysis in AnalyzedNews
                    analyzed_news = AnalyzedNews(
                        summarized_news_id=summary.id,
                        analysis=analysis
                    )
                    session.add(analyzed_news)
                    # Mark the summary as processed
                    summary.processed = True
                session.commit()
                logging.info("Stored analysis for all new summaries")
            else:
                logging.warning("The analysis was empty")
    except Exception as e:
        logging.error(f"Error processing summaries: {e}")
        session.rollback()
    finally:
        session.close()

def job():
    logging.info("Starting scheduled job to analyze summaries")
    process_summaries()
    logging.info("Scheduled job completed")

if __name__ == "__main__":
    # Perform the initial run
    # job()

    # Schedule the job every 1 hour
    schedule.every(24).hours.at("21:00:00").do(job)

    # Keep the script running
    logging.info("Starting the scheduler")
    while True:
        schedule.run_pending()
        time.sleep(60)