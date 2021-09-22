import ftx
import pandas as pd
import ta
import time
import json
from math import *
import pandas_ta as pda

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
    limit=100, 
    start_time=float(
    round(time.time()))-100*3600, 
    end_time=float(round(time.time())))
df = pd.DataFrame(data)

df['EMA90']=ta.trend.ema_indicator(df['close'], 90)
df['STOCH_RSI']=ta.momentum.stochrsi(df['close'])

ST_length = 20
ST_multiplier = 3.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION1'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 20
ST_multiplier = 4.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION2'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 40
ST_multiplier = 8.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION3'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]
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

if df['SUPER_TREND_DIRECTION1'].iloc[-2]+df['SUPER_TREND_DIRECTION2'].iloc[-2]+df['SUPER_TREND_DIRECTION3'].iloc[-2] >= 1 and df['close'].iloc[-2] > df['EMA90'].iloc[-2] and df['STOCH_RSI'].iloc[-2] < 0.8:
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

elif df['SUPER_TREND_DIRECTION1'].iloc[-2]+df['SUPER_TREND_DIRECTION2'].iloc[-2]+df['SUPER_TREND_DIRECTION3'].iloc[-2] < 1 and df['STOCH_RSI'].iloc[-2] > 0.2:
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
