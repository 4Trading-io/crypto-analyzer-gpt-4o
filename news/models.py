# models.py

from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ReceivedNews(Base):
    __tablename__ = 'received_news'
    id = Column(String, primary_key=True)
    title = Column(String)
    published_at = Column(String)
    url = Column(String)
    source = Column(String)
    kind = Column(String)
    domain = Column(String)
    votes = Column(Integer)
    comments = Column(Integer)
    sent = Column(Boolean, default=False)
    content = Column(Text)  # Field for full text content of the article

class SummarizedNews(Base):
    __tablename__ = 'summarized_news'
    id = Column(Integer, primary_key=True, autoincrement=True)
    received_news_id = Column(String, ForeignKey('received_news.id'))
    title = Column(String)
    summary = Column(Text)  # Field for summary
    category = Column(String)  # Field for categorization
    processed = Column(Boolean, default=False)  # New field to track if the summary has been analyzed
    received_news = relationship('ReceivedNews')

class AnalyzedNews(Base):
    __tablename__ = 'analyzed_news'
    id = Column(Integer, primary_key=True, autoincrement=True)
    summarized_news_id = Column(Integer, ForeignKey('summarized_news.id'))
    analysis = Column(Text)  # Field for storing GPT-4 analysis
    summarized_news = relationship('SummarizedNews')
    sent = Column(Boolean, default=False)

# Database configuration
DATABASE_URL = 'sqlite:///news_data.db'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)