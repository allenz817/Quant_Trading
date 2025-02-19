import requests
import pandas as pd

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=9UA3EPW059YLXFOB'
r = requests.get(url)
data = r.json()
df = pd.DataFrame(data)

print(df)