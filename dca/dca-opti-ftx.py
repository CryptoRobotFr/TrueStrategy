import ccxt
import pandas as pd
import json
import time

class cBot_spot_ftx():
    def __init__(self, apiKey=None, secret=None, subAccountName=None):
        ftxAuthObject = {
            "apiKey": apiKey,
            "secret": secret,
            'headers': {
                'FTX-SUBACCOUNT': subAccountName
            }
        }
        if ftxAuthObject['secret'] == None:
            self._auth = False
            self._session = ccxt.ftx()
        else:
            self._auth = True
            self._session = ccxt.ftx(ftxAuthObject)
        self.market = self._session.load_markets()

    def get_historical_from_api(self, symbol, timeframe, startDate):
        try:
            tempData = self._session.fetch_ohlcv(symbol, timeframe, int(
                time.time()*1000)-1209600000, limit=1000)
            dtemp = pd.DataFrame(tempData)
            timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])
        except:
            return None

        finished = False
        start = False
        allDf = []
        startDate = self._session.parse8601(startDate)
        while(start == False):
            try:
                tempData = self._session.fetch_ohlcv(
                    symbol, timeframe, startDate, limit=1000)
                dtemp = pd.DataFrame(tempData)
                timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])
                nextTime = int(dtemp.iloc[-1][0] + timeInter)
                allDf.append(dtemp)
                start = True
            except:
                startDate = startDate + 1209600000*2

        if dtemp.shape[0] < 1:
            finished = True
        while(finished == False):
            try:
                tempData = self._session.fetch_ohlcv(
                    symbol, timeframe, nextTime, limit=1000)
                dtemp = pd.DataFrame(tempData)
                nextTime = int(dtemp.iloc[-1][0] + timeInter)
                allDf.append(dtemp)
                # print(dtemp.iloc[-1][0])
                if dtemp.shape[0] < 1:
                    finished = True
            except:
                finished = True
        result = pd.concat(allDf, ignore_index=True, sort=False)
        result = result.rename(
            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        result = result.set_index(result['timestamp'])
        result.index = pd.to_datetime(result.index, unit='ms')
        del result['timestamp']
        return result

    def convert_amount_to_precision(self, symbol, amount):
        return self._session.amount_to_precision(symbol, amount)

    def convert_price_to_precision(self, symbol, price):
        return self._session.price_to_precision(symbol, price)

    def place_market_order(self, symbol, side, amount):
        try:
            return self._session.createOrder(
                symbol, 
                'market', 
                side, 
                self.convert_amount_to_precision(symbol, amount),
                None
            )
        except BaseException as err:
            print("An error occured", err)
            raise err

pairName = 'BTC/USD'
timeframe = '1d'
startDate = '2020-01-01T00:00:00'

weeklyAmount = 30

client = cBot_spot_ftx(apiKey='', secret='', subAccountName='')

df = client.get_historical_from_api(pairName, timeframe, startDate)

df['LAST_ATH'] = df['close'].cummax()

def return_buy_amount(row, baseAmount):
    buyAmount = 0
    if row['close'] <= 0.5 * row['LAST_ATH']:
        buyAmount = 2 * baseAmount
    elif row['close'] > 0.5 * row['LAST_ATH'] and row['close'] <= 0.8 * row['LAST_ATH']:
        buyAmount = 1 * baseAmount
    elif row['close'] > 0.8 * row['LAST_ATH']:
        buyAmount = 0.5 * baseAmount
    return buyAmount

quantityToBuy = return_buy_amount(df.iloc[-1], weeklyAmount) / df.iloc[-1]['close']
quantityToBuy = client.convert_amount_to_precision(pairName, quantityToBuy)
print(quantityToBuy)

buyOrder = client.place_market_order(symbol=pairName, side='buy', amount=quantityToBuy)
print(buyOrder)
