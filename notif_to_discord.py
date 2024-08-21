import os
import pandas as pd
import numpy as np
import yfinance as yf
import discord
import asyncio
import schedule
import time
from datetime import datetime
from datetime import timedelta
import pytz
from tabulate import tabulate

intents = discord.Intents.default()
intents.messages = True

class MyClient(discord.Client):
    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        channel = self.get_channel(os.getenv('DAILY_CHANNEL_ID'))  # YOUR_DISCORD_CHANNEL_ID yerine kendi kanal ID'nizi yazın
        await channel.send(self.message)
        await self.close()

async def send_discord_message(message):
    client = MyClient(message, intents=intents)
    await client.start(os.getenv('DISCORD_TOKEN'))
# EMA hesaplama fonksiyonu
def calculate_ema(prices, window):
    return prices.ewm(span=window, adjust=False).mean().iloc[-1]

def calculate_buying(cnt, current_price, ema):
    if cnt == 0:
        if ema == 50:
            buying_count = np.ceil(1250/current_price)
        elif ema == 100:
            buying_count = np.ceil(2500/current_price)
        elif ema == 200:
            buying_count = np.ceil(3750/current_price)
        else:
            buying_count = np.ceil(5000/current_price)
    else:
        if ema == 50:
            buying_count = np.ceil(cnt*0.25)
        elif ema == 100:
            buying_count = np.ceil(cnt*0.5)
        elif ema == 200:
            buying_count = np.ceil(cnt*0.75)
        else:
            buying_count = np.ceil(cnt)
    buying_price = buying_count * current_price

    return buying_price, buying_count

# Ticker listesini işleme fonksiyonu
async def process_tickers():
    df = pd.read_csv('discord.csv')
    tickers = df['ticker'].unique().tolist()
    report = []

    for ticker in tickers:
        try:
            print(f"Program is calculating for {ticker}")
            cnt = df.loc[df.ticker == ticker, "stock_count"].values[0]
            buy_all_emas = df.loc[df.ticker == ticker, "buy_all_emas"].values[0]
            stock_data = yf.download(ticker, period='1y', progress=False)
            current_price = stock_data['Close'].iloc[-1]
            ema50 = calculate_ema(stock_data['Close'], 50)
            ema100 = calculate_ema(stock_data['Close'], 100)
            ema200 = calculate_ema(stock_data['Close'], 200)
            ema250 = calculate_ema(stock_data['Close'], 250)
            
            print(f"Calculation is done for {ticker}")

            if current_price < ema250:
                buying_price, buying_count = calculate_buying(cnt, current_price, 250)
                print(f"EMA 250 is detected for {ticker}, adding to report")
                report.append([ticker, current_price, "EMA250"])
            elif buy_all_emas == 1:  # Tüm EMA'lara göre işlem yap
                if current_price < ema200:
                    buying_price, buying_count = calculate_buying(cnt, current_price, 200)
                    print(f"EMA 200 is detected for {ticker}, adding to report")
                    report.append([ticker, current_price, "EMA200"])
                elif current_price < ema100:
                    buying_price, buying_count = calculate_buying(cnt, current_price, 100)
                    print(f"EMA 100 is detected for {ticker}, adding to report")
                    report.append([ticker, current_price, "EMA100"])
                elif current_price < ema50:
                    buying_price, buying_count = calculate_buying(cnt, current_price, 50)
                    print(f"EMA 50 is detected for {ticker}, adding to report")
                    report.append([ticker, current_price, "EMA50"])
        except Exception as e:
            print(f"An error occurred for {ticker}: {e}")
            continue

    if report:
        report.append(["TOTAL", "", ""])
        table = tabulate(report, headers=["Ticker", "Current Price (TL)", "EMA"], tablefmt="github")
        await send_discord_message(f"```\n{table}\n```")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_tickers())