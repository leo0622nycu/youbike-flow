import requests
import pandas as pd
import datetime as dt

URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"

def main() -> None:
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    print(df.head())
    print("rows:", len(df), "time:", dt.datetime.now())

if __name__ == "__main__":
    main()
