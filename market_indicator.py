import talib as ta
import utils as util

def calculate_indicators(df):
    # ADX (Average Directional Index) to measure trend strength
    df['ADX'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)
    
    # ATR (Average True Range) to measure volatility
    df['ATR'] = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
    
    # Short and Long Moving Averages (to identify trends)
    df['EMA_20'] = ta.EMA(df['Close'], timeperiod=20)
    df['EMA_50'] = ta.EMA(df['Close'], timeperiod=50)
    
    return df

# Step 3: Define Trending vs. Choppy Market
def identify_market_condition(df):
    market_condition = []
    
    for i in range(len(df)):
        # Trending Market: ADX above 25 and EMA_20 > EMA_50 (uptrend), EMA_20 < EMA_50 (downtrend)
        if df['ADX'][i] > 25:
            if df['EMA_20'][i] > df['EMA_50'][i]:
                market_condition.append('Trending Up')
            elif df['EMA_20'][i] < df['EMA_50'][i]:
                market_condition.append('Trending Down')
            else:
                market_condition.append('Choppy')
        # Choppy Market: ADX below 20 (or a small range between 20-25)
        else:
            market_condition.append('Choppy')
    
    df['Market_Condition'] = market_condition
    return df

# Step 4: Plot Results (Optional)
def plot_market_conditions(df):
    plt.figure(figsize=(14, 8))
    
    # Plot Closing Price
    plt.plot(df.index, df['Close'], label='Close Price', color='blue', alpha=0.5)
    
    # Highlight Trending and Choppy Markets
    trending_up = df[df['Market_Condition'] == 'Trending Up']
    trending_down = df[df['Market_Condition'] == 'Trending Down']
    choppy = df[df['Market_Condition'] == 'Choppy']
    
    plt.scatter(trending_up.index, trending_up['Close'], color='green', label='Trending Up', marker='^', lw=3)
    plt.scatter(trending_down.index, trending_down['Close'], color='red', label='Trending Down', marker='v', lw=3)
    plt.scatter(choppy.index, choppy['Close'], color='orange', label='Choppy', marker='x', lw=3)
    
    plt.title('Market Conditions: Trending vs. Choppy')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(loc='best')
    plt.show()

# Main Execution
if __name__ == "__main__":
    # Step 1: Fetch Data (Using 1-year daily data for example)
    ticker = "AAPL"  # You can change to any stock or asset
    df = fetch_data(ticker, period='1y', interval='1d')
    
    # Step 2: Calculate Indicators
    df = calculate_indicators(df)
    
    # Step 3: Identify Market Conditions
    df = identify_market_condition(df)
    
    # Print the last few rows with market condition info
    print(df[['Close', 'ADX', 'ATR', 'EMA_20', 'EMA_50', 'Market_Condition']].tail(20))
    
    # Step 4: Plot Market Conditions
    plot_market_conditions(df)