import ftx
import pandas as pd
import ta
import time
import json
from math import *

accountName = ''
pairSymbol = 'ETH/USD'
fiatSymbol = 'USD'
cryptoSymbol = 'ETH'
myTruncate = 3

client = ftx.FtxClient(api_key='',
                   api_secret='', subaccount_name=accountName)

data = client.get_historical_data(
    market_name=pairSymbol, 
    resolution=3600, 
    limit=1000, 
    start_time=float(
    round(time.time()))-220*3600, 
    end_time=float(round(time.time())))
df = pd.DataFrame(data)

df['EMA1']=ta.trend.ema_indicator(close=df['close'], window=7)
df['EMA2']=ta.trend.ema_indicator(close=df['close'], window=30)
df['EMA3']=ta.trend.ema_indicator(close=df['close'], window=50)
df['EMA4']=ta.trend.ema_indicator(close=df['close'], window=100)
df['EMA5']=ta.trend.ema_indicator(close=df['close'], window=121)
df['EMA6']=ta.trend.ema_indicator(close=df['close'], window=200)
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)
#print(df)

def getBalance(myclient, coin):
    jsonBalance = myclient.get_balances()
    if jsonBalance == []: 
        return 0
    pandaBalance = pd.DataFrame(jsonBalance)
    print(pandaBalance)
    if pandaBalance.loc[pandaBalance['coin'] == coin].empty: 
        return 0
    else: 
        return float(pandaBalance.loc[pandaBalance['coin'] == coin]['total'])

def truncate(n, decimals=0):
    r = floor(float(n)*10**decimals)/10**decimals
    return str(r)
    
fiatAmount = getBalance(client, fiatSymbol)
cryptoAmount = getBalance(client, cryptoSymbol)
actualPrice = df['close'].iloc[-1]
minToken = 5/actualPrice
print('coin price :',actualPrice, 'usd balance', fiatAmount, 'coin balance :',cryptoAmount)

def buyCondition(row, previousRow):
    if row['EMA1'] > row['EMA2'] and row['EMA2'] > row['EMA3'] and row['EMA3'] > row['EMA4'] and row['EMA4'] > row['EMA5'] and row['EMA5'] > row['EMA6'] and row['STOCH_RSI']<0.82:
        return True
    else:
        return False

def sellCondition(row, previousRow):
    if row['EMA6'] > row['EMA1'] and row['STOCH_RSI']>0.2:
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
    else:
        print("If you  give me more USD I will buy more",cryptoSymbol)

elif sellCondition(df.iloc[-2], df.iloc[-3]):
    if float(cryptoAmount) > minToken:
        sellOrder = client.place_order(
            market=pairSymbol, 
            side="sell", 
            price=None, 
            size=truncate(cryptoAmount, myTruncate), 
            type='market')
        print("SELL", sellOrder)
    else:
        print("If you give me more",cryptoSymbol,"I will sell it")
else :
  print("No opportunity to take")
