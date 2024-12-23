import pandas as pd
import numpy as np
import utils as util
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema

def calculate_pivot_points(df):
    df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['R1'] = 2 * df['Pivot'] - df['Low']
    df['S1'] = 2 * df['Pivot'] - df['High']
    df['R2'] = df['Pivot'] + (df['High'] - df['Low'])
    df['S2'] = df['Pivot'] - (df['High'] - df['Low'])
    return df

def find_local_extrema(df, order=5):
    # Local minima (Support)
    df['Support'] = df['Low'].iloc[argrelextrema(df['Low'].values, np.less_equal, order=order)[0]]
    # Local maxima (Resistance)
    df['Resistance'] = df['High'].iloc[argrelextrema(df['High'].values, np.greater_equal, order=order)[0]]
    
    return df

def plot_support_resistance(df):
    plt.figure(figsize=(14, 8))
    
    # Plot Closing Price
    plt.plot(df.index, df['Close'], label='Close Price', color='blue', alpha=0.5)
    
    # Plot Pivot Points
    plt.plot(df.index, df['Pivot'], label='Pivot', linestyle='--', color='purple')
    plt.plot(df.index, df['R1'], label='Resistance 1', linestyle='--', color='red')
    plt.plot(df.index, df['S1'], label='Support 1', linestyle='--', color='green')
    
    # Plot Local Minima (Support) and Maxima (Resistance)
    plt.scatter(df.index, df['Support'], label='Local Support', color='green', marker='^', lw=3)
    plt.scatter(df.index, df['Resistance'], label='Local Resistance', color='red', marker='v', lw=3)
    
    plt.title('Support and Resistance Levels')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(loc='best')
    plt.show()

if __name__ == "__main__":
    # Step 1: Fetch Data (Using 1-year daily data for example)
    df = util.fetch_historical_data("NSE", "BANKNIFTY", 200, "ONE_DAY")
    
    # Step 2: Calculate Pivot Points
    df = calculate_pivot_points(df)
    
    # Step 3: Find Local Minima/Maxima
    df = find_local_extrema(df, order=5)  # Adjust 'order' to change sensitivity
    
    # Print the last few rows of the DataFrame to see support/resistance levels
    print(df[['Close', 'Pivot', 'R1', 'S1', 'R2', 'S2', 'Support', 'Resistance']].tail(20))
    
    # Step 4: Plot Support and Resistance Levels
    plot_support_resistance(df)
