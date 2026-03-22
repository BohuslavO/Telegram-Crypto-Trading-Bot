

import telebot
from binance.client import Client
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import time
user_data={}

TOKEN = '6888896361:AAHTTTYVrFQv5yJcctXmzoDs_tola-5sZYo'
bot = telebot.TeleBot(TOKEN, parse_mode=None)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    msg = bot.send_message(message.chat.id, f'Привіт! Це CP-bot. Для початку торгівлі, будь ласка, введи кількість USD, які ти виділив мені.\n Використовуй команду /balance, щоб перевірити свій баланс.\n Щоб ввести свої API-ключі, скористайся командою /apikeys')

@bot.message_handler(commands=['balance'])
def Bal(message):
    chat_id = message.chat.id
    msg = bot.send_message(message.chat.id, 'Будь ласка, введіть суму в USD, якою ви хочете оперувати:')
    bot.register_next_step_handler(msg, get_bal)

def get_bal(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'balance': int(message.text)}
    msg = bot.send_message(message.chat.id, 'Дякую! Тепер введіть API-ключі за допомогою команди /apikeys')
    bot.register_next_step_handler(msg, api_keys)
@bot.message_handler(commands=['apikeys'])
def api_keys(message):
    chat_id = message.chat.id
    msg = bot.send_message(message.chat.id, 'Будь ласка, введіть свій API ключ Binance:')
    bot.register_next_step_handler(msg, save_api_key)

def save_api_key(message):
    chat_id = message.chat.id
    user_data[chat_id]['api_key'] =  message.text
    msg = bot.send_message(chat_id, 'Тепер введіть свій API-Secret Binance:')
    bot.register_next_step_handler(msg, save_api_secret)

def save_api_secret(message):

    chat_id = message.chat.id
    if chat_id not in user_data or 'balance' not in user_data[chat_id]:
        bot.send_message(chat_id, "Спочатку напишіть ваш баланс використовуючи команду /balance")
        return

    api_secret = message.text
    user_data[chat_id]['api_secret'] = api_secret
    bot.send_message(chat_id, 'Дякую! Ваші API ключі збережено.')

    client = Client(user_data[chat_id]['api_key'], user_data[chat_id]['api_secret'])
    balance = user_data[chat_id]['balance']
    def top_coin():

        all_tickers = pd.DataFrame(client.get_ticker())
        usdt = all_tickers[all_tickers.symbol.str.contains('USDT')]
        work = usdt[~((usdt.symbol.str.contains('UP')) | (usdt.symbol.str.contains('DOWN')))]
        top_coin = work[work.priceChangePercent == work.priceChangePercent.max()]
        top_coin = top_coin.symbol.values[0]
        return top_coin

    inter = {1: Interval.INTERVAL_1_MINUTE,
             15: Interval.INTERVAL_15_MINUTES,
             30: Interval.INTERVAL_30_MINUTES,
             60: Interval.INTERVAL_1_HOUR}

    def res(top_coin_data):
        output1 = TA_Handler(
            symbol=top_coin_data,
            screener='Crypto',
            exchange='Binance',
            interval=inter[15])
        result15 = output1.get_analysis().summary

        output2 = TA_Handler(
            symbol=top_coin_data,
            screener='Crypto',
            exchange='Binance',
            interval=inter[30])
        result30 = output2.get_analysis().summary

        output3 = TA_Handler(
            symbol=top_coin_data,
            screener='Crypto',
            exchange='Binance',
            interval=inter[60])
        result60 = output3.get_analysis().summary

        if (result15['RECOMMENDATION']=='BUY' or result15['RECOMMENDATION']=='STRONGBUY') and (result30['RECOMMENDATION']=='BUY' or result30['RECOMMENDATION']=='STRONGBUY') and (result60['RECOMMENDATION']=='BUY' or result60['RECOMMENDATION']=='STRONGBUY'):
            return result15
        else:
            if (result15['RECOMMENDATION']!='BUY' or result15['RECOMMENDATION']!='STRONGBUY'):
                return result15
            elif (result30['RECOMMENDATION']!='BUY' or result30['RECOMMENDATION']!='STRONGBUY'):
                return result30
            elif (result60['RECOMMENDATION']!='BUY' or result60['RECOMMENDATION']!='STRONGBUY'):
                return result60
    def last_pros(asset):
        time.sleep(1)
        output = TA_Handler(
            symbol=asset,
            screener='Crypto',
            exchange='Binance',
            interval=inter[15])
        result = output.get_analysis().summary
        return result['RECOMMENDATION'] == 'SELL' or result['RECOMMENDATION'] == 'NEUTRAL'

    def last_data(symbol, interval, lookback):

        frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'min ago UTC'))
        frame = frame.iloc[:, :6]
        frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
        return frame


    last_coins = []
    last_coins_qty = []

    def rec(asset):
        time.sleep(10)
        output = TA_Handler(
            symbol=asset,
            screener='Crypto',
            exchange='Binance',
            interval=inter[15])
        result = output.get_analysis().summary
        return result['RECOMMENDATION'] == 'SELL' or result['RECOMMENDATION'] == 'NEUTRAL'

    def strategy(buy_amt, SL=0.95, Target=1.05, open_position=False):

        @bot.message_handler(commands=['tcoin'])
        def info(message):
            chat_id = message.chat.id

            df_btc = last_data('BTCUSDT', '1m', '2')
            df_eth = last_data('ETHUSDT', '1m', '2')
            df_ltc = last_data('LTCUSDT', '1m', '2')

            btc_lp = df_btc['Close'].iloc[-1]
            btc_vol = df_btc['Volume'].iloc[-1]

            eth_lp = df_eth['Close'].iloc[-1]
            eth_vol = df_eth['Volume'].iloc[-1]

            ltc_lp = df_ltc['Close'].iloc[-1]
            ltc_vol = df_ltc['Volume'].iloc[-1]

            msg = bot.send_message(message.chat.id,
                                   f'---------------------- BTC ---------------------- \n Volume - {btc_vol} \n Price - {btc_lp} \n---------------------------------------------------')
            msg = bot.send_message(message.chat.id,
                                   f'---------------------- ETH ---------------------- \n Volume - {eth_vol} \n Price - {eth_lp} \n---------------------------------------------------')
            msg = bot.send_message(message.chat.id,
                                   f'---------------------- LTC ---------------------- \n Volume - {ltc_vol} \n Price - {ltc_lp} \n---------------------------------------------------')

        chat_id = message.chat.id
        # Отримуємо рекомендацію
        try:
            result = res(top_coin())
            asset = top_coin()
            print(result,asset)
            bot.send_message(chat_id,f"{asset}\nRECOMMENDATION - {result['RECOMMENDATION']}")
            df = last_data(asset, '1m', '120')

        except:
            time.sleep(61)
            result = res(top_coin())
            asset = top_coin()
            df = last_data(asset, '1m', '120')
        info = client.get_symbol_info(asset)

        #_entryPrice = df.rstrip("0").rstrip(".") if "." in df else df
        #decimal_count = len(str(_entryPrice).split(".")[1])

        #min_qty = (info['filters'][1]['minQty'])
        #qty = float(round(buy_amt / df.Close.iloc[-1],decimal_count))
        # Кількість
        qty = round(buy_amt / df.Close.iloc[-1],1)
        print(qty)
        # Якщо рекомендація позитивна
        if result['RECOMMENDATION'] == 'BUY' or result['RECOMMENDATION'] == 'STRONG_BUY':
            # Створення ордера
            order = client.create_order(symbol=asset, side='BUY', type='MARKET', quantity=qty)

            last_coins.append(asset)
            last_coins_qty.append(qty)

            if len(last_coins)==10: last_coins.pop()
            #bot.send_message(chat_id, f"MIN-QTY - {min_qty} \nQTY - {qty}")

            bot.send_message(chat_id,f'-------------------- ORDER --------------------')
            print(str('--------------------' + 'ORDER' + '--------------------'))
            buyprice = float(order['fills'][0]['price'])
            open_position = True
            #Якщо немає помилки -->
            print(last_coins[0], last_coins_qty[0])
            while open_position:
                try:
                    # Отримуємо датафрейм
                    df = last_data(asset, '1m', '2')
                except:
                    bot.send_message(chat_id, 'Restart after 1 min')
                    time.sleep(61)
                    df = last_data(asset, '1m', '2')
                # -----------------------------------------------------------------------------------------------
                Price = str('Price ---> ' + str(df['Close'].iloc[-1]))
                target = str('Target ---> ' + str(round(buyprice * Target, 4)))
                Stop = str('Stop ---> ' + str(round(buyprice * SL, 4)))
                Profit = str(
                    'Profit ---> ' + str(round(df['Close'].iloc[-1] * qty - buyprice * qty, 3)) + ' ' + str(
                        round((df['Close'].iloc[-1]) * 100 / buyprice - 100, 3)) + '%')
                Close_Order = str('ОРДЕР ЗАКРИТО ---> ПРИБУТОК ' + str(
                    round(df['Close'].iloc[-1] * qty - buyprice * qty, 3)) + 'USD' + ' ' + str(
                    round((df['Close'].iloc[-1]) * 100 / buyprice - 100, 3)) + '%')
                # -----------------------------------------------------------------------------------------------
                bot.send_message(chat_id,
                                 f'--------------------------------------------- \n {Price} \n {target} \n {Stop} \n {Profit} \n ---------------------------------------------')
                print(
                    f'--------------------------------------------- \n {Price} \n {Target} \n {Stop} \n {Profit} \n ---------------------------------------------')

                # Пришвидчуємо перевірку до 1 секунди
                if (df['Close'].iloc[-1] >= buyprice * 1.02) or (df['Close'].iloc[-1] <= buyprice * 0.98):
                    check_sell = last_pros(asset)
                else:
                    check_sell = rec(asset)

                # Перевірка стоп-лос і тейк-профіт
                if (df['Close'].iloc[-1] <= buyprice * SL) or (df['Close'].iloc[-1] >= buyprice * Target) or (
                        check_sell):
                    order = client.create_order(symbol=asset, side='SELL', type='MARKET', quantity=qty)
                    bot.send_message(chat_id,
                                         f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! \n {Close_Order} \n !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print(
                            f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! \n {Close_Order} \n !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    break

        else:
            bot.send_message(chat_id,'SEARCH FOR THE NEXT COIN...')
            time.sleep(5)

    while True:
        try:
            strategy(balance)
            time.sleep(20)
        except Exception as e:
            if str(e) == 'APIError(code=-1013): Filter failure: LOT_SIZE':
                bot.send_message(chat_id,f"LOT_SIZE...SEARCH FOR THE NEXT COIN...")
            else:
                bot.send_message(chat_id,f"Помилка: {e}")
                print(e)
                bot.send_message(chat_id,
                                     f'-----ОРДЕР ЗАКРИТО ЧЕРЕЗ ПОМИЛКУ-----')
                try:
                    order = client.create_order(symbol=last_coins.pop(0), side='SELL', type='MARKET',
                                                quantity=last_coins_qty.pop(0))
                except Exception:
                    continue

            time.sleep(30)
            continue

bot.polling(none_stop=True)

