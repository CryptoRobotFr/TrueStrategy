from binance.client import Client
import pandas as pd
import json
import time
import ta
from math import *


# CONSTANTS
pairSymbol = 'ETHUSDT'
fiatSymbol = 'USDT'
cryptoSymbol = 'ETH'
trixLength = 9
trixSignal = 21

# API
binance_api_key = ''  # Enter your own API-key here
binance_api_secret = ''  # Enter your own API-secret here


client = Client(api_key=binance_api_key, api_secret=binance_api_secret)


def getHistorical(symbole):
    klinesT = client.get_historical_klines(
        symbole, Client.KLINE_INTERVAL_1HOUR, "5 day ago UTC")
    dataT = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    dataT['close'] = pd.to_numeric(dataT['close'])
    dataT['high'] = pd.to_numeric(dataT['high'])
    dataT['low'] = pd.to_numeric(dataT['low'])
    dataT['open'] = pd.to_numeric(dataT['open'])
    dataT['volume'] = pd.to_numeric(dataT['volume'])
    dataT.drop(dataT.columns.difference(['open','high','low','close','volume']), 1, inplace=True)
    return dataT

def getBalance(myclient, coin):
    jsonBalance = myclient.get_balances()
    if jsonBalance == []:
        return 0
    pandaBalance = pd.DataFrame(jsonBalance)
    if pandaBalance.loc[pandaBalance['coin'] == coin].empty:
        return 0
    else:
        return float(pandaBalance.loc[pandaBalance['coin'] == coin]['free'])

def get_step_size(symbol):
    stepSize = None
    for filter in client.get_symbol_info(symbol)['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            stepSize = float(filter['stepSize'])
    return stepSize

def get_price_step(symbol):
    stepSize = None
    for filter in client.get_symbol_info(symbol)['filters']:
        if filter['filterType'] == 'PRICE_FILTER':
            stepSize = float(filter['tickSize'])
    return stepSize

def convert_amount_to_precision(symbol, amount):
    stepSize = get_step_size(symbol)
    return (amount//stepSize)*stepSize

def convert_price_to_precision(symbol, price):
    stepSize = get_price_step(symbol)
    return (price//stepSize)*stepSize

df = getHistorical(pairSymbol)

df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
df['TRIX_PCT'] = df["TRIX"].pct_change()*100
df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'],trixSignal)
df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=15, smooth1=3, smooth2=3)
print(df)

actualPrice = df['close'].iloc[-1]
fiatAmount = float(client.get_asset_balance(asset=fiatSymbol)['free'])
cryptoAmount = float(client.get_asset_balance(asset=cryptoSymbol)['free'])
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
        quantityBuy = convert_amount_to_precision(pairSymbol, 0.98 * (float(fiatAmount)/actualPrice))
        buyOrder = client.order_market_buy(
            symbol=pairSymbol,
            quantity=quantityBuy)
        print("BUY", buyOrder)
    else:
        pass
        print("If you  give me more USD I will buy more",cryptoSymbol) 

elif sellCondition(df.iloc[-2], df.iloc[-3]):
    if float(cryptoAmount) > minToken:
        sellOrder = client.order_market_sell(
            symbol=pairSymbol,
            quantity=convert_amount_to_precision(pairSymbol, cryptoAmount))
        print("SELL", sellOrder)
    else:
        pass
        print("If you give me more",cryptoSymbol,"I will sell it")
else :
    pass
    print("No opportunity to take")
