import ftx
import pandas as pd
import ta
import time
import json
from math import *

accountName = 'Ytb-Tester'
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
    round(time.time()))-100*3600, 
    end_time=float(round(time.time())))
df = pd.DataFrame(data)

df['EMA28']=ta.trend.ema_indicator(df['close'], 28)
df['EMA48']=ta.trend.ema_indicator(df['close'], 48)
df['STOCH_RSI']=ta.momentum.stochrsi(df['close'])
print(df)

def getBalance(myclient, coin):
    jsonBalance = myclient.get_balances()
    pandaBalance = pd.DataFrame(jsonBalance)
    if pandaBalance.loc[pandaBalance['coin'] == coin].empty : return 0
    else : return float(pandaBalance.loc[pandaBalance['coin'] == coin]['free'])

def truncate(n, decimals=0):
    r = floor(float(n)*10**decimals)/10**decimals
    return str(r)
    

actualPrice = df['close'].iloc[-1]
fiatAmount = getBalance(client, fiatSymbol)
cryptoAmount = getBalance(client, cryptoSymbol)
print(actualPrice, fiatAmount, cryptoAmount)

if float(fiatAmount) > 5 and df['EMA28'].iloc[-2] > df['EMA48'].iloc[-2] and df['STOCH_RSI'].iloc[-2] < 0.8:
    quantityBuy = truncate(float(fiatAmount)/actualPrice, myTruncate)
    buyOrder = client.place_order(
        market=pairSymbol, 
        side="buy", 
        price=None, 
        size=quantityBuy, 
        type='market')
    print(buyOrder)

if float(cryptoAmount) > 0.001 and df['EMA28'].iloc[-2] < df['EMA48'].iloc[-2] and df['STOCH_RSI'].iloc[-2] > 0.2:
    buyOrder = client.place_order(
        market=pairSymbol, 
        side="sell", 
        price=None, 
        size=truncate(cryptoAmount, myTruncate), 
        type='market')
    print(buyOrder)
