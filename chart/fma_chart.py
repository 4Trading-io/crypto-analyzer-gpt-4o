import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.dates import DateFormatter
import matplotlib.patches as patches

def fig(symbol: str, exchange: str, interval: str, data : pd.DataFrame, support_resistance_areas: list):

    space = 0.2
    
    df = data

    # cut older data but last 200 candles
    df = data.iloc[-120:]
    df.set_index('timestamp', inplace=True)

    # Create the plot
    fig, (ax1, axv, ax2, ax3) = plt.subplots(4, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [6,1, 2, 2]})

    # Plot candlestick chart
    mpf.plot(df, 
             type='candle', 
             ax=ax1, 
             volume=axv, 
             volume_alpha=0.6, 
             style='tradingview', 
             addplot=[
                mpf.make_addplot(df['ema_50'], color='orange', ax=ax1, width=0.8),
                mpf.make_addplot(df['ema_200'], color='blue', ax=ax1, width=0.9),
                mpf.make_addplot(df['bollinger_hband'], color='red', ax=ax1, width=0.5),
                mpf.make_addplot(df['bollinger_mband'], color='gray', ax=ax1, width=0.5),
                mpf.make_addplot(df['bollinger_lband'], color='green', ax=ax1, width=0.5)
             ],
             show_nontrading=True,
             scale_width_adjustment=dict(volume=1, candle=1.6)
    )
    
    ax1.fill_between(df.index, df['bollinger_hband'], df['bollinger_lband'], facecolor='blue', alpha=0.02)

    # Plot RSI
    ax2.plot(df.index, df['rsi'], label='RSI', color='purple', linewidth=0.8)
    ax2.fill_between(df.index, 70, df['rsi'], where=(df['rsi'] >= 70), facecolor='green', alpha=0.1, interpolate=True)
    ax2.fill_between(df.index, 30, df['rsi'], where=(df['rsi'] <= 30), facecolor='red', alpha=0.1, interpolate=True)
    ax2.axhspan( 30, 70, xmin=0, xmax=1, facecolor='purple', alpha=0.06)
    # ax2.set_ylim([0, 100])
    ax2.axhline(70, color='purple', linestyle='--', linewidth=0.6, dashes=(5,5))
    ax2.axhline(50, color='#606060', linestyle='--', linewidth=0.5, dashes=(5,5))
    ax2.axhline(30, color='purple', linestyle='--', linewidth=0.6, dashes=(5,5))
    ax2.set_ylabel('RSI')
    ax2.legend()

    # Plot MACD
    macd_colors = []
    for i in range(len(df['macd_diff'])):
        macdi = df['macd_diff'].iloc[i]
        macdo = df['macd_diff'].iloc[i-1] if i > 0 else None
        if macdi > 0:
            if macdo and macdi < macdo:  # Crossing from negative to positive
                macd_colors.append('lightgreen')
            else:
                macd_colors.append('green')
        else:
            if macdo and macdi > macdo:  # Crossing from positive to negative
                macd_colors.append('lightcoral')
            else:
                macd_colors.append('red')
            
    ax3.plot(df.index, df['macd'], label='MACD', color='blue', linewidth=0.6)
    ax3.plot(df.index, df['macd_signal'], label='MACD Signal', color='orange', linewidth=0.6)
    ax3.bar(df.index, df['macd_diff'], label='MACD Hist', color=macd_colors, alpha=0.8, width={
            '1d': 0.9,
            '4h': 0.14,
            '15m': 0.01
        }[interval]
    )
    ax3.set_ylabel('MACD')
    ax3.legend()

    ax1.xaxis.set_major_formatter(DateFormatter('%b %d'))
    # ax1.tick_params(axis='x', rotation=45)

    # Set x-axis for all subplots
    xlim = [df.index[0], df.index[-1] + (df.index[-1] - df.index[0]) * space]
    for ax in [ax1, axv, ax2, ax3]:
        ax.set_xlim(xlim)
        if ax == ax1 or ax == axv :
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)    

    # Plot support and resistance areas as rectangles
    for a1 in support_resistance_areas:
        for a2 in support_resistance_areas:
            if a1['text'] != a2['text'] and (
                a1['startPrice'] < a2['startPrice'] < a1['endPrice'] or
                a2['startPrice'] < a1['startPrice'] < a2['endPrice']
            ):
                a1['conflict'] = True
                a2['conflict'] = True
     
    # Add the last price dashed line and box
    last_price = df['close'].iloc[-1]
    # color = 'green' if df['close'].iloc[-1] >= df['open'].iloc[-1] else 'red'
    ax1.axhline(last_price, color='black', linestyle='dashed', linewidth=0.5)
    ax1.text(df.index[-1] + (df.index[-1] - df.index[0]) * space, last_price, f'{last_price:.2f}', color='white', backgroundcolor='#ffffff', ha='left', va='center', bbox=dict(facecolor='#202020', edgecolor='#202020', alpha=0.8))

    # Add support and resistance line to the chart
    scale = df.high.max() - df.low.min()
    for area in support_resistance_areas:
        color = 'green' if area['text'] == 'SUPPORT' else 'red'
        start_time = area['startDatetime']
        width = pd.to_datetime(xlim[1]) - pd.to_datetime(start_time)  # Set the width to extend to the right edge
        
        if 'conflict' not in area or not area['conflict']:
            rect = patches.Rectangle((start_time, area['startPrice']), width, area['endPrice'] - area['startPrice'],
                                    linewidth=0, edgecolor=None, facecolor=color, alpha=0.3)
            ax1.add_patch(rect)
            
        price = area['price']
        
        y = price
        p = last_price
        if abs(y - p) / scale < 0.075:
            if area['text'] == 'SUPPORT':
                y = p - scale * 0.075
            else:
                y = p + scale * 0.075

        
        ax1.axhline(price, color=color, linestyle='dashed', linewidth=0.5)
        ax1.text(df.index[-1]+ (df.index[-1] - df.index[0]) * space, y, f'{price:.2f}', color='white', backgroundcolor=color, ha='left', va='center', bbox=dict(facecolor=color, edgecolor='none', alpha=0.8))

    # Add title text at the top corner
    fig.text(0.01, 0.97, f"{symbol}  |  {exchange}  |  {interval}", fontsize=14, fontweight='bold', ha='left', color="gray")

    # Adjust layout and show plot
    plt.tight_layout()
    # plt.show()
    # Save the plot as an image
    fig.savefig(f"charts/{exchange}_{symbol}_{interval}.png")
    plt.close(fig)

# fig("BTCUSDT","BINANCE","4h",None)