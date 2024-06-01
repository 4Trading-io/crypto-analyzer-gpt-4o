import os
import logging
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ReceivedNews, SummarizedNews
import spacy
import nltk
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import schedule
import time
import warnings
from credentials import newsapi_api_key, cryptopanic_api_key

# Suppress specific FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# Ensure NLTK data is downloaded
nltk_data_dir = os.path.expanduser('~/nltk_data')
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)
nltk.download('punkt', download_dir=nltk_data_dir)
nltk.data.path.append(nltk_data_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
DATABASE_URL = 'sqlite:///news_data.db'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Load the summarization model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

# API keys
NEWS_API_KEY = newsapi_api_key
CRYPTOPANIC_API_KEY = cryptopanic_api_key

def fetch_news_from_newsapi():
    try:
        logging.info("Fetching news from NewsAPI")
        url = f'https://newsapi.org/v2/everything?q=cryptocurrency&apiKey={NEWS_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        logging.info(f"Fetched {len(articles)} articles from NewsAPI")
        return [{
            'title': article['title'],
            'published_at': article['publishedAt'],
            'url': article['url'],
            'source': article['source']['name'],
            'content': article.get('content')
        } for article in articles]
    except Exception as e:
        logging.error(f"Error fetching news from NewsAPI: {e}")
        return []

def fetch_news_from_cryptopanic():
    try:
        logging.info("Fetching news from CryptoPanic")
        url = f'https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&public=true'
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('results', [])
        logging.info(f"Fetched {len(articles)} articles from CryptoPanic")
        return [{
            'title': article['title'],
            'published_at': article['created_at'],
            'url': article['url'],
            'source': article['source']['title'],
            'content': article.get('body')
        } for article in articles]
    except Exception as e:
        logging.error(f"Error fetching news from CryptoPanic: {e}")
        return []

def summarize_text(text):
    try:
        logging.info("Summarizing text")
        summaries = summarizer(text, max_length=130, min_length=30, do_sample=False)
        summary = summaries[0]['summary_text']
        logging.info("Text summarized successfully")
        return summary
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return ""

def categorize_text(text):
    try:
        logging.info("Categorizing text")
        doc = nlp(text)
        categories = set()
        for ent in doc.ents:
            categories.add(ent.label_)
        logging.info(f"Text categorized into: {categories}")
        return categories
    except Exception as e:
        logging.error(f"Error categorizing text: {e}")
        return set()

def store_received_news(article):
    session = Session()
    try:
        logging.info(f"Storing received news article: {article['title']}")
        received_news = ReceivedNews(
            id=article['url'],  # Using URL as unique ID
            title=article['title'],
            published_at=article['published_at'],
            url=article['url'],
            source=article['source'],
            content=article['content']
        )
        session.merge(received_news)
        session.commit()
        logging.info(f"Stored received news article: {article['title']}")
    except Exception as e:
        logging.error(f"Error storing received news article {article['title']}: {e}")
        session.rollback()
    finally:
        session.close()

def process_article(article):
    session = Session()
    try:
        logging.info(f"Processing article: {article.title}")

        # Using the content of the article if available, otherwise fallback to title + URL
        news_content = article.content if article.content else f"{article.title}\n{article.url}"

        # Check if the news content is empty
        if not news_content.strip():
            logging.warning(f"Empty content for article: {article.title}")
            return

        # Summarize the news content
        summary = summarize_text(news_content)

        # Check if the summary is empty
        if not summary.strip():
            logging.warning(f"Empty summary for article: {article.title}")
            return

        # Categorize the news content
        categories = categorize_text(news_content)
        category = ', '.join(categories)

        # Check if the category is empty
        if not category.strip():
            logging.warning(f"Empty category for article: {article.title}")
            return

        # Store summarized news in SummarizedNews table
        summarized_article = SummarizedNews(
            received_news_id=article.id,
            title=article.title,
            summary=summary,
            category=category
        )
        session.add(summarized_article)

        # Mark the received article as processed
        article.sent = True

        session.commit()
        logging.info(f"Stored summarized article: {article.title} with category: {category} and summary: {summary}")
    except Exception as e:
        logging.error(f"Error processing article {article.title}: {e}")
        session.rollback()
    finally:
        session.close()

# Fetch news from sources
def fetch_and_store_news():
    logging.info("Starting job to fetch and store news")
    newsapi_articles = fetch_news_from_newsapi()
    cryptopanic_articles = fetch_news_from_cryptopanic()

    # Store received news in the database
    for article in newsapi_articles + cryptopanic_articles:
        store_received_news(article)
    logging.info("Finished fetching and storing news")

def process_news():
    logging.info("Starting job to process news for summarization and categorization")
    session = Session()
    try:
        news_articles = session.query(ReceivedNews).filter(ReceivedNews.sent == False).all()
        logging.info(f"Found {len(news_articles)} articles to process")
        for article in news_articles:
            process_article(article)
    finally:
        session.close()
    logging.info("Finished processing news")

def job():
    fetch_and_store_news()
    process_news()

if __name__ == "__main__":
    # Schedule the job every 1 minute
    schedule.every(2).minutes.do(job)

    # Keep the script running
    logging.info("Starting the scheduler")
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_fetch_news_scheduler():
    # Schedule the job every 1 minute
    schedule.every(4).hours.do(job)

    # Keep the script running
    logging.info("Starting the fetch news scheduler")
    while True:
        schedule.run_pending()
        time.sleep(1)