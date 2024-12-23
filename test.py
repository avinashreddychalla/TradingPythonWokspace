from logzero import logger
import json
import datetime
import pandas as pd
import talib as ta
import pywhatkit as alert
import utils as util
import matplotlib.pyplot as plt

def get_volatile_trades(exchange, symbol, duration, interval, volatilityThreshold):
    candle_data_df = util.fetch_historical_data(exchange, symbol, duration, interval)
    volatile_trades = candle_data_df[
        (
            (candle_data_df["High"] - candle_data_df["Open"]) / candle_data_df["Open"] * 100
            <= volatilityThreshold
        )
        & (
            (candle_data_df["Open"] - candle_data_df["Low"]) / candle_data_df["Open"] * 100
            <= volatilityThreshold
        )
    ]
    return volatile_trades

def generate_signals(df):
  
    # 4. Bollinger Bands
    df["upper_band"], df["middle_band"], df["Lower_band"] = ta.BBANDS(
        df["close"], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
    )

    # 5. Stochastic Oscillator
    df["sLowk"], df["sLowd"] = ta.STOCH(
        df["High"],
        df["Low"],
        df["close"],
        fastk_period=14,
        sLowk_period=3,
        sLowd_period=3,
    )

    df['Signal'] = 0
    df.loc[(df['close'] < df['Lower_band']) & (df['RSI'] < 30), 'Signal'] = 1
    df.loc[(df['close'] > df['upper_band']) & (df['RSI'] > 70), 'Signal'] = -1
    
    # # Additional conditions using MACD
    df.loc[(df['MACD'] > df['MACD_signal']) & (df['RSI'] < 40), 'Signal'] = 1
    # df.loc[(df['MACD'] < df['MACD_signal']) & (df['RSI'] < 70), 'Signal'] = -1

    return df
    
def macd_indicator(data):
    data["MACD"], data["Signal_Line"], data['MACD_hist'] = ta.MACD(
        data["close"], fastperiod=12, slowperiod=26, signalperiod=9
    )
    data['Signal'] = 0
    data.loc[data['MACD'] > data['Signal_Line'], 'Signal'] = 1
    data.loc[data['MACD'] < data['Signal_Line'], 'Signal'] = -1
    
    return data

def rsi_strategy(data):
    data['RSI'] = ta.RSI(data['close'], timeperiod=14)
    if data['RSI'].iloc[-1] < 30:
        data['Signal'] = 1
    elif data['RSI'].iloc[-1] > 70:
        data['Signal'] = -1
        
    data['Signal'] = 0
    return data

def breakout_strategy(data):
    resistance = data['high'].rolling(window=10).max().iloc[-2]
    support = data['low'].rolling(window=10).min().iloc[-2]
    current_price = data['close'].iloc[-1]
    
    if current_price > resistance:
         data['Signal'] = 1
    elif current_price < support:
         data['Signal'] = -1
         
    data['Signal'] = 0
    return data

def volume_spike_strategy(data, volume_multiplier=1.5):
    data['Volume_MA'] = data['volume'].rolling(window=10).mean()
    data['Signal'] = 0
    buy = 0
    sell = 0
    for i in range(10, len(data)):
        if data['volume'].iloc[i] > volume_multiplier * data['Volume_MA'].iloc[i - 1]:
            if data['close'].iloc[i] > data['open'].iloc[i]:
                buy+=1
                data.loc[data.index[i], 'Signal'] = 1  # Buy signal
            else:
                sell+=1
                data.loc[data.index[i], 'Signal'] = -1  # Sell signal
    print('Tot Buy Signals: ', buy, 'Sell Signals: ', sell)
    return data

# Moving Average Crossover Strategy
def moving_average_crossover(data):
    data['SMA_Short'] = data['close'].rolling(window=10).mean()
    data['SMA_Long'] = data['close'].rolling(window=30).mean()
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1  # Buy Signal
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1  # Sell Signal
    return data

# Backtesting function
def backtest_with_risk_reward(data, strategy_function, initial_capital=100000, trade_size=100, risk_reward_ratio=2):
    
    print('\nStrategy', strategy_function)
    print('-------------------------------------')
    
    data = strategy_function(data)
    # Add necessary columns
    data['Position'] = 0
    data['PnL'] = 0.0
    data['Portfolio_Value'] = float(initial_capital)
    data['Stop_Loss'] = 0.0
    data['Take_Profit'] = 0.0
    
    current_position = 0
    entry_price = 0
    noTradeSignal = 0
    postitionPnLCheck = 0
    postitionTaken = 0

    for i in range(0, len(data)):
        if current_position == 0:  # No active trade
            if data['Signal'].iloc[i] == 1:  # Buy signal
                postitionTaken += 1
                current_position = 1
                entry_price = data['close'].iloc[i]
                stop_loss = entry_price * (1 - 0.01)  # 1% stop-loss
                take_profit = entry_price + 2 * (entry_price - stop_loss)  # RRR of 1:2
                data.at[data.index[i], 'Stop_Loss'] = stop_loss
                data.at[data.index[i], 'Take_Profit'] = take_profit
            
            elif data['Signal'].iloc[i] == -1:  # Sell signal
                postitionTaken += 1
                current_position = -1
                entry_price = data['close'].iloc[i]
                stop_loss = entry_price * (1 + 0.01)  # 1% stop-loss
                take_profit = entry_price - 2 * (stop_loss - entry_price)  # RRR of 1:2
                data.at[data.index[i], 'Stop_Loss'] = stop_loss
                data.at[data.index[i], 'Take_Profit'] = take_profit
            else:
                noTradeSignal+=1
                        
        elif current_position == 1:  # Long position
            postitionPnLCheck+=1
            if data['close'].iloc[i] >= take_profit:
                pnl = (take_profit - entry_price) * trade_size
                data.at[data.index[i], 'PnL'] = pnl
                print('Buy position pnl:', pnl,', taken at:', entry_price, ', closed at:', data.loc[data.index[i], ['open', 'close']])
                current_position = 0
            
            elif data['close'].iloc[i] <= stop_loss:
                pnl = (stop_loss - entry_price) * trade_size
                data.at[data.index[i], 'PnL'] = pnl
                print('Buy position pnl:', pnl,', taken at:', entry_price, ', closed at:', data['close'].iloc[i])
                current_position = 0
        
        elif current_position == -1:  # Short position
            postitionPnLCheck+=1
            if data['close'].iloc[i] <= take_profit:
                pnl = (entry_price - take_profit) * trade_size
                data.at[data.index[i], 'PnL'] = pnl
                print('Sell position pnl: ', pnl,', taken at: ', entry_price, ', closed at: ', data['close'].iloc[i])
                current_position = 0 
            
            elif data['close'].iloc[i] >= stop_loss:
                pnl = (entry_price - stop_loss) * trade_size
                data.at[data.index[i], 'PnL'] = pnl
                print('Sell position pnl: ', pnl,', taken at: ', entry_price, ', closed at: ', data['close'].iloc[i])
                current_position = 0

        # Update portfolio value
        data.at[data.index[i], 'Portfolio_Value'] = (
            data['Portfolio_Value'].iloc[i - 1] + data['PnL'].iloc[i]
        )
                
    print('Total Candles: ', len(data))
    print('Position Taken and square off check: ', postitionPnLCheck)
    print('Positon Not taken and No Trade Signal: ', noTradeSignal)
    print('Final Portfolio value', data['Portfolio_Value'].iloc[len(data)-1])
    return data

# Visualization
def plot_results(data):
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Portfolio_Value'], label='Portfolio Value', color='blue')
    plt.title('Strategy Performance')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    plt.legend()
    plt.show()
        

if __name__ == "__main__":
    smartApi = util.establish_connection()
    data = util.fetch_historical_data("NSE", "BRITANNIA", 3, "THREE_MINUTE", False)
    
    pd.set_option('display.max_rows', None)
       
    # print(data.loc[:,['open', 'close']])
    # print(data)
    results = backtest_with_risk_reward(data, volume_spike_strategy)
    
    results = backtest_with_risk_reward(data, macd_indicator)
    
    results = backtest_with_risk_reward(data, moving_average_crossover)
    
    results = backtest_with_risk_reward(data, rsi_strategy)
    
    results = backtest_with_risk_reward(data, breakout_strategy)
           
    # Plot results
    # plot_results(results)
    
    
    # https://nsearchives.nseindia.com/content/indices/ind_nifty50.pdf
    
    
    
    
