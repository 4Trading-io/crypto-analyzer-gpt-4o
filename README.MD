# 4Trading AI Technical and Fundamental Analyzer 

This project is a comprehensive tool for fetching, analyzing, and visualizing cryptocurrency data and news. It also downloads and summarizes daily analysis from well-known technical analysts. It integrates data from Binance, performs technical analysis, fetches news from various sources, summarizes it using NLP, downloads YouTube videos, and uses ChatGPT-4o to perform technical and fundamental analysis and summarize YouTube videos. Finally, it posts updates to a Telegram channel.

## Features
### Fetch Historical Cryptocurrency Data
- **Source:** Binance API, using the client historical kline method to fetch historical data from Binance. API Key and Secret Key are optional but allow for more data to be downloaded at once.
- **Data:** Historical price data including open, high, low, close prices, and volume.
- **Intervals:** Supports multiple intervals (e.g., 15m, 4h, 1d).
- **Storage:** Data is stored in a SQLAlchemy database for efficient retrieval and analysis.

### Calculate Technical Indicators
- **Indicators:** RSI, MACD, Bollinger Bands, EMA (25, 50, 100, 200), SMA (50, 200), Stochastic, CCI, ATR, OBV, Williams %R, Pivot Points, Fibonacci levels, and more.
- **Pattern Detection:** Includes detection of EMA crosses, major and minor pivots, Fibonacci retracements, head and shoulders patterns, harmonic patterns, wedge patterns, triangle patterns, double top and bottom patterns, and fair value gaps (FVG).

### Summarize and Categorize News Articles
- **Sources:** NewsAPI and CryptoPanic.
- **Summarization:** Uses NLP and machine learning models to generate concise summaries of news articles.
- **Categorization:** Utilizes spaCy for entity recognition and categorization of news content.

### Analyze Summarized News
- **Model:** GPT-4o from OpenAI.
- **Analysis:** Generates comprehensive analysis in Farsi, including market overview, key points, potential impacts, investor strategies, conclusions, predictions, and recommendations based on summarized news.
- **Customization:** Analysis template can be customized to include additional sections or specific formats.

### Post Updates to Telegram Channel
- **Chart Analysis:** Posts detailed technical analysis charts including candlesticks, EMAs, RSI, and volume.
- **News Analysis:** Posts summarized and analyzed news articles with comprehensive market insights.
- **Scheduling:** Automated scheduling to post updates at regular intervals.

### Visualization
- **Charts:** Generates high-resolution candlestick charts with overlays of technical indicators and pivot points.
- **Customization:** Charts can be customized to include additional indicators or patterns as needed.

### Scheduling and Automation
- **Scheduler:** Uses `schedule` library to automate data fetching, analysis, and posting tasks.
- **Concurrency:** Manages concurrent tasks using threading to ensure efficient execution without blocking.

### YouTube Famous Videos Summarization 
- **YouTube_Download:** Download expert crypto analyzer youtube videos as soon as get uploaded on youtube. 
- **Summarization:** Using Whisper and ChatGPT-4o to summarize youtube video and provide a telegram message with emphasized important points of the video. 

## Prerequisites
- Python 3.8+
- Binance API account
- OpenAI API account
- NewsAPI account
- CryptoPanic API account
- Telegram bot and channel

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Analyzer_Bot_GPT-4o.git
    cd Analyzer_Bot_GPT4o
    ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Download NLTK data:
    ```python
    import nltk
    nltk.download('punkt')
    ```
4. Install OpenCV on Ubuntu Server:
    ```bach
    apt install -y libopencv-dev python3-opencv ffmpeg
    ```
5. Create a file in name of credentials.py and put it under chart/ , news/ , youtube/ and chart/photo_download: 
    ```
    # Binance API Key
    binance_api_key = ""
    binance_secret_key = ""

    # OpenAI API Key
    openai_api_key = ''

    # Telegram Telethon Credentials
    telegram_api_id = ''
    telegram_api_hash = ''
    phone_number = ''

    # Telegram Aiogram Credentials
    telegram_bot_token_btc = ''
    telegram_channel_id = ''
    telegram_bot_token_news = ''

    # New Credentials 
    newsapi_api_key = ''
    newsapi_url = 'https://newsapi.org/v2/everything'
    cryptopanic_api_key = ''
    cryptopanic_url = 'https://cryptopanic.com/api/v1/posts/'

    # YouTube Credentials
    arzineh_channel_id = "UCGWSVnCaJOiKlOSpK8SSqbg"
    altcoin_daily_channel_id = "UCbLhGKVY-bJPcawebgtNfbw"
    ```

## Usage
1. Run main.py on chart and news folder for technical and fundamental analysis. 
2. Run download_and_analyze.py in youtube folder for youtube summarization
2. Run the main script:
    ```bash
    cd crypto-analyzer-gpt-4o/chart
    python main.py

    cd ../news
    python main.py

    cd ../youtube
    python download_and_analyze.py
    ```

### MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Folder Structure

The following is the structure of the project:

```plaintext
.
├── chart
│   ├── __init__.py
│   ├── fetch_data.py
│   ├── credentials.py
│   ├── analyze.py
│   ├── telegram_bot.py
│   ├── main.py
│   ├── plot_chart.py
│   ├── indicators.db
│   └── charts
│       └── BTCUSDT_1d_chart.jpeg
├── photo_download
│   ├── fire_chart_download.py
│   ├── photo_analyze.py
│   └── images
│       └── fire_chart.jpeg
├── tests
│   ├── __init__.py
│   ├── test_fetch_data.py
│   ├── test_analyze.py
│   └── test_telegram_bot.py
├── news
│   ├── __init__.py
│   ├── credentials.py 
│   ├── fetch_news.py
│   ├── analyze_summaries.py
│   ├── models.py
│   ├── main.py
│   ├── telegram_bot.py
│   └── news_data.db
├── youtube
│   ├── youtube_rss.py
│   ├── download_and_analyze.py
│   └── credentials.py
├── requirements.txt
└── README.md
```


# TODOs 

**Memory Adding:** Adding short time memory for Technical and Fundamental Analysis to remember previous analysis and refer to them in new analyze. 

**Consider YouTube:** Using YouTube video summaries as a data providing to ChatGPT-4o to use for analyzing market. 

**Adding Twitter:** Do something like YouTube for few famous and expert account on twitter. 
