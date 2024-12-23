import pyotp
from SmartApi import SmartConnect
import json
import datetime
import pandas as pd
import talib as ta

def establish_connection():
    smartApi = SmartConnect(api_key="5dNbGH2e")
    totp_secret = "AVWXIETDWURFRRFE5FQFYGOEB4"
    totp = pyotp.TOTP(totp_secret)
    otp = totp.now()
    
    print(otp)
    smartApi.generateSession("S61546801", "9045", otp)
    return smartApi

def read_instrument_token(symbol):
    with open("instrument_data.json", "r") as file:
        data = json.load(file)
    instruments = [obj for obj in data if obj["name"] == symbol]

    for instrument in instruments:
        return instrument["token"]

def fetch_historical_data(exchange, symbol, duration, interval, exclude_current_date):
    symbol_token = read_instrument_token(symbol)
    from_date = datetime.datetime.now() - datetime.timedelta(days=duration)
    print(from_date.strftime("%Y-%m-%d %H:%M"))
    if exclude_current_date:
        to_date = datetime.datetime.now() - datetime.timedelta(days=1)
    else:
        to_date = datetime.datetime.now()

    historical_params = {
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": interval,
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M"),
    }
    candleData = establish_connection().getCandleData(historical_params)["data"]
    
    df = pd.DataFrame(
        candleData, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["Timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("Timestamp", inplace=True)
    return  df


def send_alert():
    alert.sendwhatmsg_instantly("+918121880678", "Hi Avinash!!", 10, True)

