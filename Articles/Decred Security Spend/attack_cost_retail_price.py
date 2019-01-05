#import the correct libraries
import requests
import json
import datetime
import pandas as pd
from bs4 import BeautifulSoup

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError:
    return False
  return True


def blockRequest(i = 1):
    latestBlock_url = 'https://explorer.dcrdata.org/api/block/best/height'
    latestBlock = requests.get(latestBlock_url)
    blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/'+str(i)+'/'+latestBlock.text
    blockExplorer_response = requests.get(blockExplorer_url)
    #Error catch
    if blockExplorer_response.status_code != 200:
        print('Failed to get data:', blockExplorer_response.status_code)
        return
    else:
        jsonLoad = blockExplorer_response.text
        if is_json(jsonLoad):
            return jsonLoad
        else:
            unknownBlock = jsonLoad[jsonLoad.find("I don\'t know block"):]
            lastblock = int(''.join(list(filter(str.isdigit, unknownBlock))))
            jsonLoad = jsonLoad[:jsonLoad.find(unknownBlock)]
            last_jsonEntry = jsonLoad[jsonLoad.find(',{"height":'+str(lastblock-1)):]
            last_jsonEntry = last_jsonEntry.replace(',{"height":'+str(lastblock-1),'{"height":'+str(lastblock))
            return jsonLoad + last_jsonEntry + (blockRequest(lastblock+1))[1:]


#turning json string to dictionary and dataframe
block_data = json.loads(blockRequest())
dataframe = pd.DataFrame(block_data)

#cleaning up dataframe
dataframe = pd.concat([dataframe.drop(['ticket_pool'], axis=1), dataframe['ticket_pool'].apply(pd.Series)], axis=1)
dataframe = dataframe.drop(labels = ['hash', 'size', 'size', 'valavg','winners'], axis=1)
dataframe = dataframe.iloc[:,~dataframe.columns.duplicated()]
dataframe['time'] = pd.to_datetime(dataframe['time'],unit='s')
dataframe.columns = ['diff', 'height', 'sdiff', 'Date', 'value']
dataframe = dataframe[['Date', 'diff', 'height', 'sdiff', 'value']]
dataframe['Date'] = dataframe['Date'].dt.date

#historical Data
decredHistorical_url = "https://coinmarketcap.com/currencies/decred/historical-data/?start=20130428&end="+str(datetime.datetime.now().year)+str(datetime.datetime.now().month)+str(datetime.datetime.now().day)
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
Historical_df = Historical_df.drop(labels = ['Open','High','Low','Volume'], axis=1)
Historical_df['Date'] = Historical_df['Date'].dt.date
Historical_df.sort_index(inplace=True)

#add price data to original dataframe
dataframe= pd.merge(dataframe, Historical_df, on=['Date'], how='outer').fillna(method = 'bfill')
dataframe = dataframe.fillna(method = 'ffill')

#additional columns calculating attack cost
#dataframe['Cost to attack'] = dataframe.apply(lambda row: row.value * row.close), axis=1)

#cost to aquire 50% of stakepool, multiplies 50% of stakepool with closing price of the day  
def costS(df):
          return (df[4] *.5) * df[5]

dataframe['Cost of 50% stake'] = dataframe.apply(costS, axis=1)

#Cost to aquire 50% of hashpower by buying equipment from the market
def costh(df): 
    if (pd.to_datetime(df[0]).year == 2018):
        if (pd.to_datetime(df[0]).month < 12 and pd.to_datetime(df[0]).month >= 10):
            #df[1] is the difficulty column, then *4294967296/300000000000000 to get hashrate and $83.33 cost per TH based on Whatsminer D1 4000$ initially
            return df[1] * 4294967296/300000000000000 * 83.33 
        elif (pd.to_datetime(df[0]).month < 10 and pd.to_datetime(df[0]).month >= 4):
            return df[1] * 4294967296/300000000000000 * 1666.67 #ASIC miner Decred Master
        elif (pd.to_datetime(df[0]).month < 4):
            return df[1] * 4294967296/300000000000000 * 78947.37#GPU mining cost based on radeon r290x priced at 150$ and 1.9 gh/s
        else:
            return df[1] * 4294967296/300000000000000 * 58.82#Antminer DR5
    elif (pd.to_datetime(df[0]).year < 2018):
        return df[1] * 4294967296/300000000000000 * 78947.37 #gpu mining
    else:
        return df[1] * 4294967296/300000000000000 * 58.82 #Antminer DR5
    
dataframe['Cost of 50% hashpower'] = dataframe.apply(costh, axis=1)

def Totalc(df):
    return df[7] + df[8]

dataframe['total cost of attack/security spend'] = dataframe.apply(Totalc, axis=1)
#cost(dataframe['Date'],dataframe['diff'])

#dataframe['capital cost'] = cost(dataframe['Date'],dataframe['diff'])

#dataframe['Capital cost'] = dataframe.apply(cost, axis=1)
        

#write to csv
dataframe.to_csv('Attack_costretail.csv', encoding='utf-8', index=False)


'''
#Since problems in block explorer breaking on certain blocks. the data was saved to three csvs
#URL for get requests
#problems with block explorere not having values for certain blocks
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/1/280050'
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/280052/295545'
    #blockExplorer_url = 'https://explorer.dcrdata.org/api/block/range/295547/306052'
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
Combined_Data.to_csv('Attack_cost.csv', encoding='utf-8', index=False)'''
