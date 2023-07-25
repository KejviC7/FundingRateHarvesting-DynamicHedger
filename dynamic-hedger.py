''''Strategy Name: Funding Rate Farming using Dynamic Hedging 
    Combination: Spot-Futures
    Farming Exchange: MEXC
    Hedge Exchange: MEXC
    Target Coin: CEEK
    '''

# Import libraries
#from os import PRIO_PGRP
#from ast import Return
#from binhex import LINELEN
#from os import PRIO_PGRP
#from turtle import position
#from turtle import position
#from mexc_sdk import Spot
import email
import ccxt
import time
#import numpy as np

AccessKey = ''
SecretKey = ''
#print(ccxt.exchanges)
# FUND PARAMETERS
FUND_BALANCE = 1000
TARGET_COIN = 'CEEKUSDT'
LEVERAGE = 35
TEMP_LEVERAGE = 35
SPOT_INVENTORY = 0
SYMBOL = 'CEEK_USDT'
COIN = 'CEEK'
LIQ_DISTANCE = 1.5 
EMERGENCY_LIQ_DISTANCE = 1.2
SAFETY_BUFFER = 1 / LIQ_DISTANCE
OVERCOL_BUFFER = 0.65 

# Create Spot object
#spot = Spot(api_key=AccessKey, api_secret=SecretKey)
mexc = ccxt.mexc({'apiKey': AccessKey, 'secret': SecretKey, 'options': {'defaultType': 'swap'}})
mexc_spot = ccxt.mexc({'apiKey': AccessKey, 'secret': SecretKey, 'options': {'defaultType': 'spot'}})

def open_close_spot_position(size, type='OPEN'): 
    orderbook = mexc_spot.fetch_order_book(SYMBOL)
    orderbook_bid_table = [(float(orderbook['bids'][i][0]), float(orderbook['bids'][i][1])) for i in range(len(orderbook['bids']))]
    orderbook_ask_table = [(float(orderbook['asks'][i][0]), float(orderbook['asks'][i][1])) for i in range(len(orderbook['asks']))]
    
    best_ask = orderbook_ask_table[0][0]
    best_ask_size = orderbook_ask_table[0][1]
    best_bid = orderbook_bid_table[0][0]
    best_bid_size = orderbook_bid_table[0][1]
    
    shares = size / best_ask if type == 'OPEN' else (size / best_bid) 
    if type == 'OPEN':
    
        if shares > best_ask_size:
            order_quantity = 0
            for idx, tuple in enumerate(orderbook_ask_table):
                if shares > order_quantity:
                    order_quantity += tuple[1]
                else:
                    buy_limit_price = orderbook_ask_table[idx][0]
                    print(f'Sending Limit Buy Order at Price {buy_limit_price} and quantity {shares}')
                    # Send Limit Buy Order with Limit Price of Price at Ask Table with idx
                    mexc_spot.create_order(SYMBOL, 'limit', 'buy', shares, buy_limit_price)
                    return
                    
        else:
            print(f'Sending Limit Buy Order at Price {best_ask} and quantity {shares}')
            mexc_spot.create_order(SYMBOL, 'limit', 'buy', shares, best_ask)
            
    elif type == 'CLOSE':
        if shares > best_bid_size:
            order_quantity = 0
            for idx, tuple in enumerate(orderbook_bid_table):
                if shares > order_quantity:
                    order_quantity += tuple[1]
                else:
                    sell_limit_price = orderbook_bid_table[idx][0]
                    print(f'Sending Limit Sell Order at Price {sell_limit_price} and quantity {shares}')
                    # Send Limit Buy Order with Limit Price of Price at Ask Table with idx
                    mexc_spot.create_order(SYMBOL, 'limit', 'buy', shares, sell_limit_price)
                    return
        else:
            print(f'Sending Limit Sell Order at Price {best_bid} and quantity {shares}')
            mexc_spot.create_order(SYMBOL, 'limit', 'buy', shares, best_bid)
    else:
        print('Incorrect Parameter Format!')
    
    return 


def open_close_futures_position(size, type='OPENSHORT'):
    orderbook = mexc.fetch_order_book(SYMBOL)
    orderbook_bid_table = [(float(orderbook['bids'][i][0]), float(orderbook['bids'][i][1])) for i in range(len(orderbook['bids']))]
    orderbook_ask_table = [(float(orderbook['asks'][i][0]), float(orderbook['asks'][i][1])) for i in range(len(orderbook['asks']))]
    
    
    best_ask = orderbook_ask_table[0][0]
    best_ask_size = orderbook_ask_table[0][1]
    best_bid = orderbook_bid_table[0][0]
    best_bid_size = orderbook_bid_table[0][1]
    
    shares = (size / best_bid) / 10 if type == 'OPENSHORT' else (size / best_ask) / 10  # Contract has 10 shares
    
    if type == 'OPENSHORT':
        if shares > best_bid_size:
            order_quantity = 0
            for idx, tuple in enumerate(orderbook_bid_table):
                if shares > order_quantity:
                    order_quantity += tuple[1]
                else:
                    sell_limit_price = orderbook_bid_table[idx][0]
                    print(f'Opening Short Futures Position. Sending Limit Sell Order at Price {sell_limit_price} and quantity {shares}')
                    # Send Limit Sell Order with Limit Price of Price at Ask Table with idx
                    # openType: 1 for Isolated Margin, 2 for Cross Margin
                    # positionType: 1 for Long and 2 for Short
                    # order side must be 1 open long, 2 close short, 3 open short or 4 close long
                    params = {'openType': 1, "leverage": LEVERAGE}
                    mexc.create_swap_order(SYMBOL, 1, 3, shares, sell_limit_price, params)
                    return
                    
        else:
            print(f'Opening Short Futures Position. Sending Limit Sell Order at Price {best_bid} and quantity {shares}')
            params = {'openType': 1, "leverage": LEVERAGE}
            mexc.create_swap_order(SYMBOL, 1, 3, shares, best_bid, params)
            
    elif type == 'CLOSESHORT':
        if shares > best_ask_size:
            order_quantity = 0
            for idx, tuple in enumerate(orderbook_ask_table):
                if shares > order_quantity:
                    order_quantity += tuple[1]
                else:
                    buy_limit_price = orderbook_ask_table[idx][0]
                    print(f'Closing Short Position. Sending Limit Buy Order at Price {buy_limit_price} and quantity {shares}')
                    # Send Limit Buy Order with Limit Price of Price at Ask Table with idx
                    params = {'openType': 1, "leverage": LEVERAGE}
                    mexc.create_swap_order(SYMBOL, 1, 2, shares, buy_limit_price, params)
                    return
        else:
            print(f'Closing Short Position. Sending Limit Buy Order at Price {best_ask} and quantity {shares}')
            params = {'openType': 1, "leverage": LEVERAGE}
            mexc.create_swap_order(SYMBOL, 1, 2, shares, best_ask, params)
    else:
        print('Incorrect Parameter Format!')
    
    return

def transfer_collateral_spot_to_swap(amount):
    # Check there is sufficient available USDT in SPOT for transfer
    balance = mexc_spot.fetch_balance()
    free_balance = balance['USDT']['free']
    print(f'Available USDT is: ${free_balance}')
    if free_balance > 0 and amount <= free_balance:
        mexc.transfer('USDT', round(amount, 3), 'spot', 'swap')
    
    return
    #else:
     #   print('There is not enough available USDT to transfer!')
def transfer_collateral_swap_to_spot(amount):
    # Check there is sufficient available USDT in SPOT for transfer
    balance = mexc.fetch_balance()
    free_balance = balance['USDT']['free']
    print(f'Available USDT is: ${free_balance}')
    if free_balance > 0 and amount <= free_balance:
        mexc.transfer('USDT', round(amount, 3), 'swap', 'spot')
    #else:
     #   print('There is not enough available USDT to transfer!')
    return 
def fetch_balance():
    balance = mexc.fetch_balance()
    free_balance = balance['USDT']['free']
    return free_balance

def get_liquidation_price():
    open_position = mexc.contractPrivateGetPositionOpenPositions()
    liqPrice = open_position['data'][0]['liquidatePrice']   
    return liqPrice

def get_latest_futures_price():
    orderbook_data = mexc.fetch_order_book(SYMBOL)
    best_ask, best_ask_size =  orderbook_data['asks'][0][0], orderbook_data['asks'][0][1]
    best_bid, best_bid_size = orderbook_data['bids'][0][0], orderbook_data['bids'][0][1]
    return best_bid

def get_latest_spot_price():
    orderbook_data = mexc_spot.fetch_order_book(SYMBOL)
    best_ask, best_ask_size =  orderbook_data['asks'][0][0], orderbook_data['asks'][0][1]
    best_bid, best_bid_size = orderbook_data['bids'][0][0], orderbook_data['bids'][0][1]
    return best_bid
    
def fetch_position_data():
    position_data = mexc.contractPrivateGetPositionOpenPositions()
    return position_data

def increase_decrease_margin(amount, type='INCREASE'):
    position_data = fetch_position_data()
    positionId = position_data['data'][0]['positionId']
    free_bal = fetch_balance()
    if type == 'INCREASE':
        if free_bal < amount:
            # There is not enough free USDT to add to Margin so we need to transfer some
            print(f'Not enough USDT for margin increase. Transferring some USDT from Spot to Swap')
            difference = amount - free_bal + 10 # An extra 10
            
            transfer_collateral_spot_to_swap(difference)
            
            # Now add collateral to Margin
            mexc.add_margin(SYMBOL, round(amount, 3), params={'positionId': positionId})
            print(f'${amount} Margin added.')
        else:
            mexc.add_margin(SYMBOL, round(amount, 3), params={'positionId': positionId})
    elif type == 'DECREASE':
        # Remove some collateral 
        mexc.reduce_margin(SYMBOL, round(amount, 3), params={'positionId': positionId})
        print(f'${amount} Margin removed.')
    return 

def compute_margin_amount():
    # Get latest price
    last_price = get_latest_futures_price()
    # Get current margin 
    position_data = fetch_position_data()
    
    current_margin = float(position_data['data'][0]['im'])
    #print(current_margin)
    current_margin_requirement = float(position_data['data'][0]['oim'])
    # Get entry price
    entry_price = float(position_data['data'][0]['holdAvgPrice'])
    #print(entry_price)
    # Get size
    position_size = float(position_data['data'][0]['holdVol']) * 10
    #print(position_size)
    # Formula for margin needed
    margin = position_size * ((LIQ_DISTANCE * last_price) - entry_price)
    amount = margin - current_margin

    if amount > current_margin - current_margin_requirement:
        amount = current_margin - current_margin_requirement - 1

    if abs(amount) < 1:
        amount = 1
    return amount


def check_positions_hedging():
    
    spot_balance = mexc_spot.fetch_balance()[COIN]['free']
    swap_balance = mexc.contractPrivateGetPositionOpenPositions()['data'][0]['holdVol']
    
    if abs(round(float(spot_balance), 0) - (round(float(swap_balance), 0) * 10)) < 5:
        print('Spot and Futures Positions are hedged.')
        return True
    else:
        print('Spot and Futures Positions need to be hedged properly! Adjusting positions...')
        difference = round(float(spot_balance), 0) - (round(float(swap_balance), 0) * 10)
        if difference > 0:
            amount_change = difference * get_latest_futures_price()
            if fetch_balance() > amount_change: 
                print('There is enough free USDT to increase the Futures Position.')
                open_close_futures_position(amount_change, type='OPENSHORT')
            else:
                print('Not enough free USDT. Trying to transfer some if possible.')
                try:
                    transfer_collateral_spot_to_swap(amount_change+1)
                except:
                    print('Not Enough USDT available in SPOT to transfer to Futures.')
                    print('Closing the equivalent of the SPOT position instead.')
                    open_close_spot_position(amount_change, type='CLOSE')
                    
        elif difference < 0:
            difference = abs(difference)
            amount_change = difference * get_latest_spot_price()
            if fetch_balance() > amount_change: 
                print('There is enough free USDT to increase the SPOT Position.')
                open_close_spot_position(amount_change, type='OPEN')
             
            else:
                print('Not enough free USDT. Trying to transfer some if possible.')
                try:
                    transfer_collateral_swap_to_spot(amount_change+1)
                except:
                    print('Not Enough USDT available in Futures to transfer to SPOT.')
                    print('Closing the equivalent of the Futures position instead.')
                    open_close_futures_position(amount_change, type='CLOSESHORT')
        
    return 
    

def check_spot_open_orders():
    open_orders = mexc_spot.fetch_open_orders(SYMBOL)
    if len(open_orders) > 0:
        print('There are currently a few open orders that haven not been filled yet!')
        return True
    return False

def check_swap_open_orders():
    open_orders = mexc.fetch_open_orders(SYMBOL)
    if len(open_orders) > 0:
        print('There are currently a few open orders that haven not been filled yet!')
        return True
    return False

def cancel_spot_orders():
    print('Cancelling All Orders!')
    mexc_spot.cancel_all_orders(SYMBOL)
    print('All orders have been cancelled.')

def cancel_swap_orders():
    print('Cancelling All Orders!')
    mexc.cancel_all_orders(SYMBOL)
    print('All orders have been cancelled.')
    
def dynamic_hedging():
    
    liqPrice = float(get_liquidation_price())
    latestPrice = float(get_latest_futures_price())
    amount = compute_margin_amount()
    position_data = fetch_position_data()
    required_margin = float(position_data['data'][0]['oim'])
    current_margin = float(position_data['data'][0]['im'])
    
    global TEMP_LEVERAGE
    global LIQ_DISTANCE
    if latestPrice / liqPrice > SAFETY_BUFFER:
        amount = abs(amount)
        # Adjust Margin Accordingly. In this case increase Margin:
        print(f'Increasing Position Margin by ${amount}')
        try:
            increase_decrease_margin(round(amount, 3), 'INCREASE')
        except:
            print('Leverage Adjustment Required. Increasing Leverage to decrease Maintenance Margin Requirement.')
            # Increment TEMP LEVERAGE BY 1 and pass it
            TEMP_LEVERAGE += 1
            if TEMP_LEVERAGE > 35:
                if LIQ_DISTANCE == EMERGENCY_LIQ_DISTANCE:
                    print('LIQ DISTANCE WAS ALREADY SET TO EMERGENCY LIQ DISTANCE and there is still not enough USDT to increase Position Margin within Requirements.')
                    print('Now I will start minimizing positions accordingly to avoid Liquidation!')
                    
                    print(f'Closing $ {amount} worth of the Futures Position and the same amount of the Spot Position')
                    open_close_futures_position(amount, 'CLOSESHORT')
                    open_close_spot_position(amount, 'CLOSE')
                    
                print('Leverage has already been increased significantly. Time to take other measures')
                print('Setting LIQUIDATION DISTANCE TO EMERGENCY LIQUDATION DISTANCE')
                LIQ_DISTANCE = EMERGENCY_LIQ_DISTANCE
            else:
                adjust_leverage(TEMP_LEVERAGE)
            
    elif latestPrice / liqPrice < 0.9 * SAFETY_BUFFER:
        # Since we will need to decrease margin the amount returned will be negative but we need a positive value to pass.  
        amount = abs(amount)
        print(f'Too much collateral allocated. Decreasing Position Margin by ${amount}')
        if abs(amount) > (current_margin - required_margin):
            new_amount = current_margin - required_margin - 10
            if new_amount < 1:
                new_amount = 0
            print(f'Amount of collateral to remove was greater than the allowed amount. New amount is: {new_amount}')
            if new_amount <= 0:
                print('Leverage Adjustment Required. Increasing Leverage to decrease Maintenance Margin Requirement.')
                # Increment TEMP LEVERAGE BY 1 and pass it
                TEMP_LEVERAGE += 1
                adjust_leverage(TEMP_LEVERAGE)
            else:
                increase_decrease_margin(round(new_amount, 3), 'DECREASE')
        else:
            increase_decrease_margin(round(amount, 3), 'DECREASE')
    else:
        
        print('No need to adjust margin. Prices within Safety Buffer. Monitoring!')
        
    return 

def adjust_leverage(leverage):
    
    position_data = fetch_position_data()
    positionId = position_data['data'][0]['positionId']
    params = {'openType': 1, "leverage": leverage, 'positionId': positionId}
    print(f'Setting new leverage to {leverage}')
    mexc.set_leverage(SYMBOL, 1, params)
    
    return 

def display():
    print(f'1. Starting the BOT!')
    time.sleep(1)
    print(f'2. Target Exchange is MEXC.')
    time.sleep(1)
    print(f'3. Target Coin is {SYMBOL}.')
    time.sleep(1)
    print(f'4. Allocating ${FUND_BALANCE} to the bot.')
    time.sleep(1)
    adjust_leverage(LEVERAGE)
    print(f'5. LEVERAGE has been set to {LEVERAGE}.')
    time.sleep(1)
    
if __name__ == '__main__':

    display()
    print(f'6. Opening Long and Short Positions for Funding Rate Farming!')
    #open_close_spot_position(800, 'OPEN')
    #open_close_futures_position(100, 'OPENSHORT')

    time.sleep(1)
    print(f'7. Activating Dynamic Hedging for Position Monitoring. Collateral will be adjusted if necessary!')
    time.sleep(1)
    while True:
        print('Monitoring the Positions. Dynamic Hedger is Active')
        # Check for Open Orders
        try:
            if check_spot_open_orders() == True:
                cancel_spot_orders()
            if check_swap_open_orders() == True:
                cancel_swap_orders
        except:
            print('Problem calling Open Orders Checking and Cancelling Logic. API timeout perhaps. Look into it.')
        check_positions_hedging()
        dynamic_hedging()
        time.sleep(5)



