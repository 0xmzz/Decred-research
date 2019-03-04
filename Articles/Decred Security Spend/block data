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


def Hashrate(df):
    return df[1] * 4294967296/300000000000000
dataframe['Hashrate'] = dataframe.apply(Hashrate, axis=1)


#write to csv
dataframe.to_csv('block data.csv', encoding='utf-8', index=False)
