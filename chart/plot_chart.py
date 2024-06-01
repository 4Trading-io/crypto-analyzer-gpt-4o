import regex as re
import pandas as pd
import numpy as np
from typing import Iterator
from credentials import chart_image_api_key
from fma_chart import fig
import requests
import logging
import json

PERSIAN_NUM = "۰۱۲۳۴۵۶۷۸۹"
def _normalize_number(n:str) -> float:
    
    if n[0] in PERSIAN_NUM:
        for i in range(10):
            n = n.replace(PERSIAN_NUM[i],str(i))
    
    return float(n)
        

def _parse_support_resistance(msg:str) -> tuple:
    """
        extract support and resistance price from GPT text response

        Args:
            msg (str): Chat GPT response that is created by template
            
        Returns:
            list[float], list[float]: support and resistance value
    """
    
    support = []
    resistance = []
    
    r = re.search("سطح حمایت\s*:\s*([0-9۰-۹.*_, ]+)", msg)
    if r: 
        support.extend([ x.strip() for x in r.group(1).replace("*","").replace("_","").strip().split(',') ])
        
        
    r = re.search("سطح مقاومت\s*:\s*([0-9۰-۹.*_, ]+)", msg)
    if r: 
        resistance.extend([ x.strip() for x in r.group(1).replace("*","").replace("_","").strip().split(',') ])
        
    return [ _normalize_number(x) for x in support ], [ _normalize_number(x) for x in resistance ]
    
def _get_sr_drawing_input(msg:str, data: pd.DataFrame) -> Iterator:
    now = np.datetime_as_string(np.datetime64('today'), unit='s') + '.000Z'
    
    supports, resistances = _parse_support_resistance(msg)
    for support in supports:
        for st in reversed(range(len(data))):
            if data['low'].iloc[st] <= support <= data['high'].iloc[st]: break

        body_end = max(data['open'].iloc[st], data['close'].iloc[st])
        body_start = min(data['open'].iloc[st], data['close'].iloc[st])
        
        if (
            data['low'].iloc[st] < support < body_start
            and (body_end - body_start) <= (body_start - data['low'].iloc[st])
        ):
            # the shadow in longer than the body and the level is inside the shadow
            lower = data['low'].iloc[st]
            upper = body_start
            dt =  data['timestamp'].iloc[st]
        elif st > 0:
            for ed in reversed(range(st)):
                if not (data['low'].iloc[ed] <= support <= data['high'].iloc[ed]): break
            ed += 1
            st += 1
            lower = data['low'].iloc[ed:st].min()
            upper = data['high'].iloc[ed:st].min()
            dt = data['timestamp'].iloc[ed] #str(data['timestamp'].iloc[ed+1]).replace(' ','T') + '.000Z'
        else:
            lower = support * 0.995
            upper = support * 1.005
            dt = data['timestamp'].iloc[0] # str(data['timestamp'].iloc[0]).replace(' ','T') + '.000Z'
            
        yield {
            "startDatetime":  dt,
            "startPrice": lower,
            "endDatetime": now,
            "endPrice": upper,
            "price": support,
            "text": "SUPPORT"
        }
            
    for resistance in resistances:
        for st in reversed(range(len(data))):
            if data['low'].iloc[st] <= resistance <= data['high'].iloc[st]: break

        body_end = max(data['open'].iloc[st], data['close'].iloc[st])
        body_start = min(data['open'].iloc[st], data['close'].iloc[st])
        
        if (
            body_end < resistance < data['high'].iloc[st]
            and (body_end - body_start) <= (data['high'].iloc[st] - body_end)
        ):
            # the shadow in longer than the body and the level is inside the shadow
            lower = body_end
            upper = data['high'].iloc[st]
            dt =  data['timestamp'].iloc[st]
        elif st > 0:
            for ed in reversed(range(st)):
                if not (data['low'].iloc[ed] <= resistance <= data['high'].iloc[ed]): break
            ed +=1
            st +=1
            lower = data['low'].iloc[ed:st].max()
            upper = data['high'].iloc[ed:st].max()
            dt = data['timestamp'].iloc[ed] # str(data['timestamp'].iloc[ed+1]).replace(' ','T') + '.000Z'
        else:
            lower = resistance * 0.995
            upper = resistance * 1.005
            dt = data['timestamp'].iloc[0] # str(data['timestamp'].iloc[0]).replace(' ','T') + '.000Z'
            
        yield {
            "startDatetime":  dt,
            "startPrice": lower,
            "endDatetime": now,
            "endPrice": upper,
            "price": resistance,
            "text": "RESISTANCE"
        }          
            

def get_SR_drawing(msg:str, data: pd.DataFrame) -> Iterator:
    for input in _get_sr_drawing_input(msg, data):
        support = True if input['text'] == 'SUPPORT' else False
        yield {
            "name": "Rectangle",
            "input": input,
            "override": {
                "fontBold": True,
                "showLabel": True,
                "fillBackground": True,
                "extendRight": True,
                "horzLabelAlign": "right",
                "vertLabelAlign": "middle",
                "lineColor": "rgba(0,0,0,0)",
                "backgroundColor": "rgba(40,200,40,0.2)" if support else "rgba(200,40,40,0.2)",
                "textColor": "rgba(100,255,100,0.9)" if support else "rgba(255,100,100,0.9)"
            }
        }

def generate_chart_PNG_chart_img(symbol: str, exchange: str, interval: str, msg:str, data: pd.DataFrame) -> str:
    """Generate chart image showing klines, EMA(200) and main Support & Resistance

    Args:
        symbol (str): symbol name, for example `BTCUSDT`
        exchange (str): exchange name, for example `BINANCE`
        interval (str): chart interval, for example `4h`
        msg (str): ChatGPT Analysis Response, it should be formatted
        data (pd.DataFrame): ohlc chart data, this should contains at least the following columns: timestamp, high, low

    Returns:
        str: generated file name
    """
    drawings = [ d for d in get_SR_drawing(msg, data) ]
    template = {
        "theme": "dark",
        "interval": interval,
        "symbol": f"{exchange}:{symbol}",
        "override": {
            "showStudyLastValue": False
        },
        "studies": [
            {
                "name": "Moving Average Exponential",
                "input": {
                    "length": 200,
                    "source": "close",
                    "offset": 0,
                    "smoothingLine": "SMA",
                    "smoothingLength": 200
                },
                "override": {
                    "Plot.visible": True,
                    "Plot.linewidth": 1,
                    "Plot.plottype": "line",
                    "Plot.color": "rgb(255,139,0)"
                }
            }
        ],
        "drawings": drawings
    }
    
    response =  requests.post("https://api.chart-img.com/v2/tradingview/advanced-chart", data=json.dumps(template), headers={
        "x-api-key": chart_image_api_key,
        "content-type": "application/json",
    })
    
    try:
        response.raise_for_status()
    except BaseException as e:
        logging.error(f"API Error ({response.status_code}): {response.text}")
        raise e
    
    filename = f"charts/{exchange}_{symbol}_{interval}_{np.datetime_as_string(np.datetime64('now'), unit='s')}.png"
    with open(filename, "wb") as f:
        f.write(response.content)
    
    import os
    from pathlib import Path
    link = f"charts/{exchange}_{symbol}_{interval}.png"
    if os.path.exists(Path(link)):
        os.unlink(link)
    os.link(filename, link)
    
    return filename
    

def generate_chart_PNG_mpl_finance(symbol: str, exchange: str, interval: str, msg:str, data: pd.DataFrame) -> str:
    """Generate chart image showing klines, EMA(200), BB, MACD, RSI and main Support & Resistance

    Args:
        symbol (str): symbol name, for example `BTCUSDT`
        exchange (str): exchange name, for example `BINANCE`
        interval (str): chart interval, for example `4h`
        msg (str): ChatGPT Analysis Response, it should be formatted
        data (pd.DataFrame): ohlc chart data, this should contains at least the following columns: timestamp, high, low

    Returns:
        str: generated file name
    """
    drawings = [ d for d in _get_sr_drawing_input(msg, data) ]
    
    fig(symbol, exchange, interval, data, drawings)

    
    filename = f"charts/{exchange}_{symbol}_{interval}.png"
    link = f"charts/{exchange}_{symbol}_{interval}_{np.datetime_as_string(np.datetime64('now'), unit='s')}.png"
    
    import os
    from pathlib import Path
    if os.path.exists(Path(link)):
        os.unlink(link)
    os.link(filename, link)
    
    return filename
    


def test():
    sample = """
    **تحلیل ارز دیجیتال توسط فرخنده یک هوش مصنوعی**

    **نماد:** ETHUSDT  
    **بازه زمانی:** 1d  
    **قیمت فعلی :** 3898  
    **تاریخ:** 2024-05-27

    **شاخص‌های تکنیکال:**
    - خرید یا فروش EMA: خرید  
    - خرید یا فروش MACD: خرید  
    - خرید یا فروش RSI: خرید
    - خرید یا فروش SMA : خرید
    - خرید یا فروش Stochastic: خرید
    - سیگنال CCI: 89
    - سیگنال ATR: 180
    - سیگنال OBV: 6923325
    - خرید یا فروش Williams %R: خرید

    **تحلیل بر اساس فیبوناچی، خط روند و پیوت‌های اصلی و فرعی:**  
    قیمت فعلی نزدیک به سطوح فیبوناچی 61.8٪ و 38.2٪ قرار دارد که نشان می‌دهد در یک مقاومت مهم قرار دارد. خط روند صعودی با ایستایی پیوت‌های اصلی در سطوح 3813 و 3896 و حمایت در 3743 و 3966 همراه است.

    **سطوح حمایت و مقاومت:**
    - سطح حمایت: 3743
    - سطح مقاومت: ۴۰۹۷

    **پیش‌بینی یک روز آینده و یک هفته آینده:**  
    برای یک روز آینده، احتمال حرکت اتریوم به سمت سطح مقاومت 4097 بالا است. اما ممکن است بازگشت قیمتی به سطح حمایت 3743 نیز مشاهده شود. برای یک هفته آینده، اتریوم ممکن است به مقاومت بالاتر 4219 برخورد کند و اگر شکسته شود، حرکت به سمت 4540 شروع می‌شود.

    در مورد امواج الیوت: نشانه‌هایی از پایان موج پنجم (5) صعودی دیده می‌شود، که ممکن است اصلاح قیمتی در موج A و B و سپس ادامه به سمت موج C (صعود) را داشته باشیم.

    با ما همراه باشید برای تحلیل‌های بیشتر!

    #ارز_دیجیتال #تحلیل_تکنیکال #بیت_کوین
    """
    
    s, r = _parse_support_resistance(sample)

    from tvDatafeed import TvDatafeed, Interval
    import talib
    data = TvDatafeed().get_hist(symbol='ETHUSDT', exchange='BINANCE', interval=Interval.in_4_hour, n_bars=1000 )
    data['timestamp'] = data.index
    
    # Calculate technical indicators
    data['ema_50'] = talib.EMA(data['close'], timeperiod=50)
    data['ema_200'] = talib.EMA(data['close'], timeperiod=200)
    data['bollinger_hband'], data['bollinger_mband'], data['bollinger_lband'] = talib.BBANDS(data['close'], timeperiod=20)
    data['rsi'] = talib.RSI(data['close'])
    data['macd'], data['macd_signal'], data['macd_diff'] = talib.MACD(data['close'])

    
    # print([x for x in get_SR_drawing(sample, data)])
    
    print(generate_chart_PNG_mpl_finance('ETHUSDT','BINANCE','4h',sample,data))
    

# test()