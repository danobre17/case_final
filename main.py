import requests
from datetime import datetime
import pandas as pd
import time
import json
import os
import pickle
from ta import add_all_ta_features
from flask import flask
from flask import Flask, jsonify, request

app=flask(__name__)



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
    
  

@app.route("/")
def index():
    return "Robo Cripto Marvin 42"

@app.route('/wakeup', methods=["POST"])
def wakeup():
    """
    Exemplo de Utilização:
    
    import requests
    url = 'http://127.0.0.1:5000/wakeup'
    try:
        x = requests.post(, data = {'time': 10}, timeout=6) 
    except requests.exceptions.ReadTimeout: 
        pass
    """

    token = os.environ.get('MARVIN_TOKEN')

    tempo = int(request.form.get("time"))
    if not tempo:
        return "Group token must be provided", None
    
    # my_robot é a função com o loop que realiza as compras/ vendas (conforme notebook 2_my_robot.ipynb)
    robot(tempo, token)
    
