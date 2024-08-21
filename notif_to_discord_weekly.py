import os
import pandas as pd
import numpy as np
import yfinance as yf
import discord
import asyncio
from tabulate import tabulate

intents = discord.Intents.default()
intents.messages = True

class MyClient(discord.Client):
    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        channel = self.get_channel(os.getenv('WEEKLY_CHANNEL_ID'))  # YOUR_DISCORD_CHANNEL_ID yerine kendi kanal ID'nizi yazın
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
            buying_count = np.ceil(1250 / current_price)
        elif ema == 100:
            buying_count = np.ceil(2500 / current_price)
        elif ema == 200:
            buying_count = np.ceil(5000 / current_price)
    else:
        if ema == 50:
            buying_count = np.ceil(cnt * 0.25)
        elif ema == 100:
            buying_count = np.ceil(cnt * 0.5)
        elif ema == 200:
            buying_count = np.ceil(cnt * 0.75)
            
    buying_price = buying_count * current_price
    return buying_price, buying_count

def get_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="max")
    df.reset_index(inplace=True)
    df["week_no"] = df.Date.dt.isocalendar().week
    df["year_no"] = df.Date.dt.isocalendar().year
    df_weekly = df.groupby(["year_no", "week_no"]).agg({"Open": "mean", "Close": "mean", 
                                                        "High": "max", "Low": "min"}).reset_index()
    df_weekly.sort_values(by=["year_no", "week_no"], ascending=True, inplace=True)
    df_weekly["ema_50"] = calculate_ema(df_weekly['Close'], 50)
    df_weekly["ema_100"] = calculate_ema(df_weekly['Close'], 100)
    df_weekly["ema_200"] = calculate_ema(df_weekly['Close'], 200)
    
    return df_weekly

async def process_tickers():
    df = pd.read_csv('discord.csv')
    tickers = df['ticker'].unique().tolist()
    report = []
    for ticker in tickers:
        df_weekly = get_data(ticker)
        current_price = df_weekly['Close'].iloc[-1]
        ema200 = df_weekly['ema_200'].iloc[-1]
        ema100 = df_weekly['ema_100'].iloc[-1]
        ema50 = df_weekly['ema_50'].iloc[-1]
        buy_all_emas = df.loc[df.ticker == ticker, 'buy_all_emas'].iloc[-1]
        cnt = df.loc[df.ticker == ticker, "stock_count"].values[0]
        if current_price < ema200:
            buying_price, buying_count = calculate_buying(cnt, current_price, 200)
            print(f"EMA200 is detected for {ticker}, adding to report")
            report.append([ticker, current_price, "EMA200"])
        elif buy_all_emas == 1:  # Tüm EMA'lara göre işlem yap
            if current_price < ema100:
                buying_price, buying_count = calculate_buying(cnt, current_price, 100)
                print(f"EMA 100 is detected for {ticker}, adding to report")
                report.append([ticker, current_price, "EMA100"])
            elif current_price < ema50:
                buying_price, buying_count = calculate_buying(cnt, current_price, 50)
                print(f"EMA 50 is detected for {ticker}, adding to report")
                report.append([ticker, current_price, "EMA50"])
    if report:
        report.append(["TOTAL", "", ""])
        table = tabulate(report, headers=["Ticker", "Current Price (TL)", "EMA"], tablefmt="github")
        await send_discord_message(f"```\n{table}\n```")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_tickers())
