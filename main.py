import requests
from datetime import datetime
import pandas as pd
import time
import json
import os
import pickle
from ta import add_all_ta_features

urlbase = 'https://mighty-bastion-45199.herokuapp.com/'

def get_result(x):
    try:
        result = pd.DataFrame.from_dict(x.json())
    except:
        result = x.text
    return result

def api_post(route, payload):
    url = urlbase + route
    x = requests.post(url, data = payload)
    df = get_result(x)
    return df

def api_get(route):
    url = urlbase + route
    x = requests.get(url)
    df = get_result(x)
    return df


def meu_modelo_linear_dummy(df):
  if random.randint(0,1) == 1:
    return 30
  else:
    return -30

def tratamento_df(df):
  return df.tail(1)
 
def feature_eng(df):
  df['valor_ma_15'] = df['close'].rolling(window=15).mean()
  df['valor_ma_60'] = df['close'].rolling(window=60).mean()
  df['diff_15_60']=df['valor_ma_15'] - df['valor_ma_60']
  
  df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)
  return df


def robot():
  
  while True:
    
    print(datetime.now())
    time.sleep(60)
    
  
if __name__ == '__main__':
    robot()
