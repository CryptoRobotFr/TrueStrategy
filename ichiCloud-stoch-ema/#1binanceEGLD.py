# -- coding: utf-8 --
import pandas as pd
from math import *
import time
from binance.client import Client
import ta 
### API
binance_api_key = ''    #Enter your own API-key here
binance_api_secret = '' #Enter your own API-secret here

### CONSTANTS
client = Client(api_key=binance_api_key, api_secret=binance_api_secret)

# Parameters
pairSymbol = 'EGLDUSDT'
fiatSymbol = 'USDT'
cryptoSymbol = 'EGLD'
myTruncate = 2

def truncate(n, decimals=0):
  r = floor(float(n)*10**decimals)/10**decimals
  return str(r)

def getHistorical(symbole):
  klinesT = client.get_historical_klines(symbole, Client.KLINE_INTERVAL_15MINUTE, "2 day ago UTC")
  dataT = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
  dataT['close'] = pd.to_numeric(dataT['close'])
  dataT['high'] = pd.to_numeric(dataT['high'])
  dataT['low'] = pd.to_numeric(dataT['low'])
  dataT['open'] = pd.to_numeric(dataT['open'])
  dataT['volume'] = pd.to_numeric(dataT['volume'])
  dataT.drop(dataT.columns.difference(['open','high','low','close','volume']), 1, inplace=True)
  return dataT


df = getHistorical(pairSymbol)

df['EMA50']=ta.trend.ema_indicator(df['close'], 50)
df['STOCH_RSI']=ta.momentum.stochrsi(df['close'])
df['SSA'] = ta.trend.ichimoku_a(df['high'],df['low'],3,38).shift(periods=48)
df['SSB'] = ta.trend.ichimoku_b(df['high'],df['low'],38,46).shift(periods=48)

# print(df)
actualPrice = df['close'].iloc[-1]
fiatAmount = client.get_asset_balance(asset=fiatSymbol)['free']
cryptoAmount = client.get_asset_balance(asset=cryptoSymbol)['free']
minToken = 5/actualPrice

print(pairSymbol,'price :',actualPrice)
print(fiatSymbol,'blance :',fiatAmount)
print(cryptoSymbol,'blance :',cryptoAmount)

if df['close'].iloc[-2] > df['SSA'].iloc[-2] and df['close'].iloc[-2] > df['SSB'].iloc[-2] and df['STOCH_RSI'].iloc[-2] < 0.8 and df['close'].iloc[-2] > df['EMA50'].iloc[-2]:
    if float(fiatAmount) > 5:
        quantityBuy = truncate(float(fiatAmount)/actualPrice, myTruncate)
        buyOrder = client.order_market_buy(
            symbol=pairSymbol,
            quantity=quantityBuy)
        print("BUY",buyOrder)
    else:
        print("If you give me more",fiatSymbol,"I will use them to BUY")

elif (df['close'].iloc[-2] < df['SSA'].iloc[-2] or df['close'].iloc[-2] < df['SSB'].iloc[-2]) and df['STOCH_RSI'].iloc[-2] > 0.2:
    if float(cryptoAmount) > minToken:
        sellOrder = client.order_market_sell(
            symbol=pairSymbol,
            quantity=truncate(cryptoAmount,myTruncate))
        print("SELL",sellOrder)
    else:
        print("If you give me more",cryptoSymbol,"I will SELL them")
else :
  print("No opportunity to take")


