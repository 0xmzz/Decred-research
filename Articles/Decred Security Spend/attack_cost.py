#import the correct libraries
import requests
import json
import pandas as pd

#URL for get requests
#problems with block explorere not having values for certain blocks
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/1/280050'
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/280052/295545'
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/295547/306052'
blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/1/306052'
blockExplorer_response = requests.get(blockExplorer_url)

#Error catch
if blockExplorer_response.status_code != 200:
    print('Failed to get data:', blockExplorer_response.status_code)    
    
#turning json string to dictionary and dataframe
block_data = json.loads(blockExplorer_response.text)
dataframe = pd.DataFrame(block_data)

#cleaning up dataframe
dataframe = pd.concat([dataframe.drop(['ticket_pool'], axis=1), dataframe['ticket_pool'].apply(pd.Series)], axis=1)
dataframe = dataframe.drop(labels = ['hash', 'sdiff', 'size', 'size', 'valavg','winners'], axis=1)
dataframe = dataframe.iloc[:,~dataframe.columns.duplicated()]
dataframe['time'] = pd.to_datetime(dataframe['time'],unit='s')
dataframe.columns = ['diff', 'height', 'Date', 'value']
dataframe = dataframe[['Date', 'diff', 'height', 'value']]
dataframe['Date'] = dataframe['Date'].dt.date

#historical Data
from bs4 import BeautifulSoup

decredHistorical_url = "https://coinmarketcap.com/currencies/decred/historical-data/?start=20130428&end=20181231"
Historical_content = requests.get(decredHistorical_url).content
soup = BeautifulSoup(Historical_content,'html.parser')
table = soup.find('table', {'class': 'table'})

Historical_data = [[td.text.strip() for td in tr.findChildren('td')] 
        for tr in table.findChildren('tr')]

Historical_df = pd.DataFrame(Historical_data)
Historical_df.drop(Historical_df.index[0], inplace=True) # first row is empty
Historical_df[0] =  pd.to_datetime(Historical_df[0]) # date
for i in range(1,7):
    Historical_df[i] = pd.to_numeric(Historical_df[i].str.replace(",","").str.replace("-","")) # some vol is missing and has -
Historical_df.columns = ['Date','Open','High','Low','Close','Volume','Market Cap']
Historical_df = Historical_df.drop(labels = ['Open','High','Low','Volume','Market Cap'], axis=1)
Historical_df['Date'] = Historical_df['Date'].dt.date
Historical_df.sort_index(inplace=True)

#add price data to original dataframe
#dataframe = pd.concat([Historical_df.set_index('Date'), dataframe.set_index('Date')], axis=1).fillna(method='ffill')
dataframe= pd.merge(dataframe, Historical_df, on=['Date'], how='outer').fillna(-1)

#write to csv
dataframe.to_csv('Attack_cost.csv', encoding='utf-8', index=False)



#Since problems in block explorer breaking on certain blocks. the data was saved to three csvs

#getting all the data
dataset1 = pd.read_csv('Attack_cost_1.csv')
dataset2 = pd.read_csv('Attack_cost_2.csv')
dataset3 = pd.read_csv('Attack_cost_3.csv')

#removing unwanted variables
dataset1 = dataset1[dataset1.height != -1]
dataset2 = dataset2[dataset2.height != -1]
dataset3 = dataset3[dataset3.height != -1]

#combining data into one
Combined_Data = pd.DataFrame()
Combined_Data = Combined_Data.append(dataset1, sort=False)
Combined_Data = Combined_Data.append(dataset2, sort=False)
Combined_Data = Combined_Data.append(dataset3, sort=False)

#writing all to csv
Combined_Data.to_csv('Attack_cost.csv', encoding='utf-8', index=False)
