import binance
from binance.client import Client
import config, os


def order(client, data):
    ticker = data['ticker']
    order_action = config.ORDER_ACTION_TO_POSITION[data['strategy']['order_action']]
    order_id = data['strategy']['order_id'].lower()
    price_market = float(client.get_symbol_ticker(symbol=ticker)['price'])
    print('------ Order Info ------')
    print(f"Ticker: {ticker}")
    print(f"Order Action: {order_action}")
    print(f"Order ID: {order_id}")
    print(f"Price: {price_market}")

    print('----- Current Postion Info ------')
    current_position, current_quatity = get_current_position_info(client, ticker)
    available_balance = get_available_balance(client)
    print(f'Current Position: {current_position}')
    print(f'Available Balance: {available_balance}')

    open_quantity = (available_balance * config.RISK_RATE * config.LEVERAGE)/price_market
    open_quantity = round(open_quantity*config.BOUND, 2)
    print(f'Open Quantity: {open_quantity}')

    lower_bound = round(price_market * (1 - config.STOPLOSS), 2)
    upper_bound = round(price_market * (1 + config.STOPLOSS), 2)
    try:
        if current_position.lower() == '':
            # open theo file json gửi đến
            if order_action.lower() == 'short':
                # open stoploss short 
                create_order_stoploss(order_type='short', 
                                    client=client, 
                                    symbol=ticker, 
                                    quantity=open_quantity, 
                                    lower_bound=lower_bound, 
                                    upper_bound=upper_bound)

            elif order_action.lower() == 'long':
                create_order_stoploss(order_type='long', 
                                    client=client, 
                                    symbol=ticker, 
                                    quantity=open_quantity, 
                                    lower_bound=lower_bound, 
                                    upper_bound=upper_bound)            
        elif (current_position.lower() == 'long') and (order_action.lower() == 'short'):
            # close current long postion and orders
            client.futures_create_order(symbol=ticker, type='MARKET',
                                        side='SELL', positionSide='LONG', 
                                        quantity=current_quatity*config.CLOSE_RATE)
            client.futures_cancel_all_open_orders(symbol=ticker)
            if 'close' not in order_id.lower():
                create_order_stoploss(order_type='short', 
                                    client=client, 
                                    symbol=ticker, 
                                    quantity=open_quantity, 
                                    lower_bound=lower_bound, 
                                    upper_bound=upper_bound)
        elif (current_position.lower() == 'short') and (order_action.lower() == 'long'):
        # close short
            client.futures_create_order(symbol=ticker, type='MARKET',
                                        side='BUY', positionSide='SHORT', 
                                        quantity=-current_quatity*config.CLOSE_RATE)
            client.futures_cancel_all_open_orders(symbol=ticker)
            if 'close' not in order_id.lower():
                create_order_stoploss(order_type='long', 
                                    client=client, 
                                    symbol=ticker, 
                                    quantity=open_quantity, 
                                    lower_bound=lower_bound, 
                                    upper_bound=upper_bound)
        return "Sucess"
    except:
        return "Fail"




def get_current_position_info(client, ticker):
    all_position = [record for record in client.futures_position_information(symbol=ticker) \
                                      if record['positionSide'].upper() in ['LONG', 'SHORT']]
    for position in all_position:
        if float(position['entryPrice']) > 0:
            current_position = position['positionSide']
            current_quatity = float(position['positionAmt'])
            return current_position, current_quatity
    return '', 0

def create_order_stoploss(order_type, client, symbol, quantity, lower_bound, upper_bound):
    if order_type.lower() == 'long':
        # mở lệnh market long
        client.futures_create_order(symbol=symbol, type='MARKET',
                                    side='BUY', positionSide='LONG',
                                    quantity=quantity)
        # đặt stoploss cho lệnh long
        client.futures_create_order(symbol=symbol, type='STOP_MARKET',
                                    side='SELL', positionSide='LONG',
                                    quantity=quantity, stopPrice=lower_bound)
        # đặt take profit cho lệnh long
        client.futures_create_order(symbol=symbol, type='TAKE_PROFIT_MARKET',
                                    side='SELL', positionSide='LONG',
                                    quantity=quantity, stopPrice=upper_bound)
    elif order_type.lower() == 'short':
        # mở lệnh market short
        client.futures_create_order(symbol=symbol, type='MARKET',
                                    side='SELL', positionSide='SHORT', 
                                    quantity=quantity)
        # đặt stoploss cho lệnh short: stopPrice truyền vào phải >= marketPrice
        client.futures_create_order(symbol=symbol, type='STOP_MARKET',
                                    side='BUY', positionSide='SHORT',
                                    quantity=quantity, stopPrice=upper_bound)
        # đặt take profit cho lệnh short
        client.futures_create_order(symbol=symbol, type='TAKE_PROFIT_MARKET',
                                    side='BUY', positionSide='SHORT',
                                    quantity=quantity, stopPrice=lower_bound)
    return

def get_available_balance(client):
    available_balance = float([record for record in client.futures_account_balance(isolated=False)\
                 if record['asset']=='USDT'][0]['withdrawAvailable'])
    return available_balance