import requests
from datetime import datetime
import pandas as pd
import time
import json
import os
import pickle
from ta import add_all_ta_features
from flask import Flask
from flask import Flask, jsonify, request
import numpy as np
import statsmodels.api as sm
import math


app=Flask(__name__)



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

def compute_quantity(coin_value, invest_value, significant_digits):
    a_number = invest_value/coin_value
    rounded_number =  round(a_number, significant_digits - int(math.floor(math.log10(abs(a_number)))) - 1)
    return rounded_number.iloc[0]


def tratamento_df(df):
  return df.tail(1)
 

def feature_eng(df):
    # Cria variáveis:
    df['valor_ma_15'] = df['close'].rolling(window=15).mean()
    df['valor_ma_60'] = df['close'].rolling(window=60).mean()
    df['diff_15_60']=df['valor_ma_15'] - df['valor_ma_60']

    df = add_all_ta_features(
        df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)

    # Um contador de minutos desde o início da série
        
    # Tratamentos básicos de datas
    #data['datetime'] = data['DATE'] + ' ' + data['TIME']
    #data['datetime'] = pd.to_datetime(data['datetime'])
    df.sort_values(by = 'datetime', inplace = True)
    #df = df[['datetime', 'volume', 'close']]

    # Renomeando coluna
    df.rename(columns = {'close':'valor'}, inplace = True)
    df.loc[:,'target_num'] = df['valor'].shift(-5)
    df.loc[:,'target_diff'] = df['target_num']  - df['valor']
    df.loc[:,'target'] = df['target_diff'].apply(lambda x: 1 if x>=10 else 0)

    df = df.drop(columns = ['target_num', 'target'])

    df=df.dropna()
    return df
	
    
def how_much_i_have(ticker, token):
    status = api_post('status', payload = {'token': token})
    status_this_coin = status.query(f"ticker == '{ticker}'")
    if status_this_coin.shape[0] > 0:
        return status_this_coin['quantity'].iloc[0]
    else:
        return 0

def robot(tempo, token):
    model = pickle.load(open('best_model.pkl', 'rb'))
    ticker = 'BTCUSDT'
    count_iter = 0
    valor_compra_venda = 10
   
    
    while count_iter < tempo:
        
       
        # Pegando o OHLC dos últimos 500 minutos
        df = api_post('cripto_quotation', {'token': token, 'ticker': ticker})
        

        # Realizando a engenharia de features
        df = feature_eng(df)

        # Isolando a linha mais recente
        df_last = df.iloc[[np.argmax(df['datetime'])]]

        
        df_last2=df_last[[ 'open', 'high', 'low', 'valor',
            'volume', 'number_of_trades', 'valor_ma_15', 'valor_ma_60',
            'diff_15_60', 'volume_adi', 'volume_obv', 'volume_cmf', 'volume_fi',
            'volume_mfi', 'volume_em', 'volume_sma_em', 'volume_vpt', 'volume_nvi',
            'volume_vwap', 'volatility_atr', 'volatility_bbm', 'volatility_bbh',
            'volatility_bbl', 'volatility_bbw', 'volatility_bbp', 'volatility_bbhi',
            'volatility_bbli', 'volatility_kcc', 'volatility_kch', 'volatility_kcl',
            'volatility_kcw', 'volatility_kcp', 'volatility_kchi',
            'volatility_kcli', 'volatility_dcl', 'volatility_dch', 'volatility_dcm',
            'volatility_dcw', 'volatility_dcp', 'volatility_ui', 'trend_macd',
            'trend_macd_signal', 'trend_macd_diff', 'trend_sma_fast',
            'trend_sma_slow', 'trend_ema_fast', 'trend_ema_slow', 'trend_adx',
            'trend_adx_pos', 'trend_adx_neg', 'trend_vortex_ind_pos',
            'trend_vortex_ind_neg', 'trend_vortex_ind_diff', 'trend_trix',
            'trend_mass_index', 'trend_cci', 'trend_dpo', 'trend_kst',
            'trend_kst_sig', 'trend_kst_diff', 'trend_ichimoku_conv',
            'trend_ichimoku_base', 'trend_ichimoku_a', 'trend_ichimoku_b',
            'trend_visual_ichimoku_a', 'trend_visual_ichimoku_b', 'trend_aroon_up',
            'trend_aroon_down', 'trend_aroon_ind', 'trend_psar_up',
            'trend_psar_down', 'trend_psar_up_indicator',
            'trend_psar_down_indicator', 'trend_stc', 'momentum_rsi',
            'momentum_stoch_rsi', 'momentum_stoch_rsi_k', 'momentum_stoch_rsi_d',
            'momentum_tsi', 'momentum_uo', 'momentum_stoch',
            'momentum_stoch_signal', 'momentum_wr', 'momentum_ao', 'momentum_kama',
            'momentum_roc', 'momentum_ppo', 'momentum_ppo_signal',
            'momentum_ppo_hist', 'others_dr', 'others_dlr', 'others_cr'
            ]]
                


        # Calculando tendência, baseada no modelo linear criado
        diff = model.predict(df_last2)[0]





        # A quantidade de cripto que será comprada/ vendida depende do valor_compra_venda e da cotação atual
        qtdade = compute_quantity(coin_value = df_last['close'], invest_value = valor_compra_venda, significant_digits = 2)

        # Print do datetime atual
        print('-------------------')
        print(f"@{pd.to_datetime('now')}")

        if diff < 5:
            # Modelo detectou uma diff negativa
            print(f"Tendência negativa de {str(diff)}")

            # Verifica quanto dinheiro tem em caixa
            qtdade_money = how_much_i_have('money', token)

            if qtdade_money>0:
                # Se tem dinheiro, tenta comprar o equivalente a qtdade ou o máximo que o dinheiro permitir
                max_qtdade = compute_quantity(coin_value = df_last['close'], invest_value = qtdade_money, significant_digits = 2)
                qtdade = min(qtdade, max_qtdade)

                # Realizando a compra
                print(f'Comprando {str(qtdade)} {ticker}')
                api_post('sell', payload = {'token': token, 'ticker': ticker, 'quantity': qtdade})

        elif diff > 5:
            # Modelo detectou diff positiva
            print(f"Tendência positiva de {str(diff)}")

            # Verifica quanto tem da moeda em caixa
            qtdade_coin = how_much_i_have(ticker, token)

            if qtdade_coin>0:
                # Se tenho a moeda, vou vender!
                qtdade = min(qtdade_coin, qtdade)
                print(f'Vendendo {str(qtdade)} {ticker}')
                api_post('buy', payload = {'token': token, 'ticker': ticker, 'quantity':qtdade})
        else:
            # Não faz nenhuma ação, espera próximo loop
            print(f"Tendência neutra de {str(diff)}. Nenhuma ação realizada")

        # Print do status após cada iteração
        print(api_post('status', payload = {'token': token}))       
        count_iter +=1
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
    
