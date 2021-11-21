import ftx
import pandas as pd
import json
import time
import ta
from math import *
import discord
import telegram_send

def truncate(n, decimals=0):
    r = floor(float(n)*10**decimals)/10**decimals
    return str(r)

def getBalance(myclient, coin):
    jsonBalance = myclient.get_balances()
    if jsonBalance == []: 
        return 0
    pandaBalance = pd.DataFrame(jsonBalance)
    if pandaBalance.loc[pandaBalance['coin'] == coin].empty: 
        return 0
    else: 
        return float(pandaBalance.loc[pandaBalance['coin'] == coin]['free'])

pairSymbol = 'ETH/USD'
fiatSymbol = 'USD'
cryptoSymbol = 'ETH'
myTruncate = 3
i = 9
j = 21
goOn = True

client = ftx.FtxClient(
    api_key='',
    api_secret='', 
    subaccount_name=''
)
result = client.get_balances()

data = client.get_historical_data(
    market_name=pairSymbol, 
    resolution=3600, 
    limit=1000, 
    start_time=float(round(time.time()))-150*3600, 
    end_time=float(round(time.time())))
df = pd.DataFrame(data)


trixLength = 9
trixSignal = 21
df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
df['TRIX_PCT'] = df["TRIX"].pct_change()*100
df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'],trixSignal)
df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)
print(df)
messages = ""

actualPrice = df['close'].iloc[-1]
fiatAmount = getBalance(client, fiatSymbol)
cryptoAmount = getBalance(client, cryptoSymbol)
minToken = 5/actualPrice
print('coin price :',actualPrice, 'usd balance', fiatAmount, 'coin balance :',cryptoAmount)

def buyCondition(row, previousRow):
    if row['TRIX_HISTO'] > 0 and row['STOCH_RSI'] <= 0.82:
        return True
    else:
        return False

def sellCondition(row, previousRow):
    if row['TRIX_HISTO'] < 0 and row['STOCH_RSI'] >= 0.2:
        return True
    else:
        return False

if buyCondition(df.iloc[-2], df.iloc[-3]):
    if float(fiatAmount) > 5:
        quantityBuy = truncate(float(fiatAmount)/actualPrice, myTruncate)
        buyOrder = client.place_order(
            market=pairSymbol, 
            side="buy", 
            price=None, 
            size=quantityBuy, 
            type='market')
        print("BUY", buyOrder)
        messages = "Buy " + pairSymbol + " " + str(quantityBuy) + " at " + str(actualPrice)
    else:
        goOn = True
        print("If you  give me more USD I will buy more",cryptoSymbol) 
        messages = "If you  give me more USD I will buy more " + cryptoSymbol

elif sellCondition(df.iloc[-2], df.iloc[-3]):
    if float(cryptoAmount) > minToken:
        sellOrder = client.place_order(
            market=pairSymbol, 
            side="sell", 
            price=None, 
            size=truncate(cryptoAmount, myTruncate), 
            type='market')
        print("SELL", sellOrder)
        messages = "Sell " + pairSymbol + " " + str(cryptoSymbol)  + " at " + str(actualPrice)
    else:
        goOn = True
        print("If you give me more",cryptoSymbol,"I will sell it")
        messages = "If you  give me more "+ cryptoSymbol+" I will sell it " 
else :
    goOn = True
    print("No opportunity to take")
    messages = "No opportunity to take"

telegram_send.send(messages=[messages])

# ///////

TOKEN = ""
client = discord.Client()
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    channel = client.get_channel()
    await channel.send(messages)

    user = await client.fetch_user()
    await user.send(messages)

    await client.close()
    time.sleep(1)


client.run(TOKEN)
