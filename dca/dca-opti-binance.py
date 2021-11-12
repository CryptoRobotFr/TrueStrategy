# -- Import --
import pandas as pd
from binance.client import Client

# -- Define Binance Client --
client = Client(
    api_key='',
    api_secret=''
)

weeklyAmount = 30

# -- You can change the crypto pair ,the start date and the time interval below --
pairName = "BTCUSDT"
startDate = "01 january 2017"
timeInterval = Client.KLINE_INTERVAL_1WEEK

# -- Load all price data from binance API --
klinesT = client.get_historical_klines(pairName, timeInterval, startDate)

# -- Define your dataset --
df = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

# -- Set the date to index --
df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']

print("Data loaded 100%")

# -- Drop all columns we do not need --
df.drop(columns=df.columns.difference(['open','high','low','close','volume']), inplace=True)

# -- Indicators, you can edit every value --
df['LAST_ATH'] = df['close'].cummax()

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
quantityToBuy = convert_amount_to_precision(pairName, quantityToBuy)
print(quantityToBuy)

buyOrder = client.order_market_buy(
            symbol=pairName,
            quantity=quantityToBuy
        )
print("BUY",buyOrder)
