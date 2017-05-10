import shutil
from flask import Flask, redirect, render_template, url_for, jsonify
import pandas as pd
from threading import Thread
import datetime
import sqlite3
import os
import time

pd.options.display.float_format = 'R${:,.2f}'.format

app = Flask(__name__)


@app.route("/restartdrive")
def restartdrive():
    os.system("onedrive-d restart")
    return "server restartando"    

def load_db():
    print("Loading db..")
    c = 1
    try:
        os.remove('Banco.db')
    except Exception as e:
        print(e)

    print("Copiando arquivo do Banco")
    shutil.copyfile('../OneDrive/Documentos/Banco.db', 'Banco.db')
    print("Banco copiado")

    conn = sqlite3.connect('Banco.db')

    df_contas = pd.read_sql_query("SELECT * from CONTAS", conn)
    df_contas.DATA = pd.to_datetime(df_contas.DATA, format='%d/%m/%Y %H:%M:%S')
    df_prods = pd.read_sql_query("SELECT * from PRODUTOS", conn, parse_dates=False)
    print("Tudo certo nas queries")
    # Clean data
    df_contas.DATA = pd.to_datetime(df_contas.DATA)
    df_contas = df_contas[df_contas.NOME != 'Excluido']
    df_contas.index = pd.to_datetime(df_contas.DATA, dayfirst=False, yearfirst=True)
    # print('Cleaning data')
    df_contas = df_contas[df_contas.DATA >= '2016-01-01']
    df_contas.to_csv('data.csv', quoting=2, index=False)

    with open("static/log.txt", "a") as f:
        f.write(", ".join([str(c), "Tamanho:", str(len(df_contas)), str(datetime.datetime.now())]))
        f.write("\n")
   
    print("Pronto")
    return True


def get_report(tempo, qtd):
    df_contas = read_treat_data()
    print("dados tratados")
    if tempo == 1:
        tempo_encoded = 'd'
    elif tempo == 2:
        tempo_encoded = 'w'
    elif tempo == 3:
        tempo_encoded = 'm'
    else:
        return dict()

    rp = pd.DataFrame(df_contas.resample(tempo_encoded).sum()['Preço'].tail(qtd).fillna(0))
    rp.index = rp.index.date
    rp.columns = ['Total']
    report = rp.T.to_html(classes=['table', 'table-hover'])
    rp.index = rp.index.astype(str)
    report_json = rp.Total.to_json()
    return report, report_json

    # report = df_contas.tail(50).sort_index(ascending=False)[['Conta', 'Código Produto', 'Produto', 'Preço']]\
    #    .to_html(classes=['table', 'table-hover', 'highchart'])


def read_treat_data():
    df_contas = pd.read_csv('data.csv')
    print("read csv funfou")
    df_contas.columns = ['ID', 'Conta', 'Código Produto', 'Produto', 'Preço', 'Data']
    df_contas.Data = pd.to_datetime(df_contas.Data)
    df_contas.set_index('Data', inplace=True)
    return df_contas


@app.route("/time/<int:tempo>/qtd/<int:qtd>")
def rest_report(tempo, qtd): 
    try:
        print("lendo rest")
        if os.path.exists('data.csv'):
            print("path exists")
            #df = read_treat_data()
            report, report_json = get_report(tempo, qtd)

        else:
            return "nao achei o arquivo"
        return jsonify(
            {
                "tempo": tempo,
                "qtd": qtd,
                "report": report,
                "report_json": report_json
             }
        )
    except Exception as e:
#        print(e)
        return repr(e)

@app.route("/debug")
def debug():
    with open("nohup.out", "r") as f:
        t = f.readlines()
    return t

@app.route("/")
def hello():
    t = Thread(target=load_db)
    t.daemon = True    
    t.start()
    return render_template('main.html')


@app.route('/log')
def root():
    if os.path.exists("static/log.txt"):
        with open('static/log.txt', 'r') as f:
            lines = f.readlines()
        return '\n\n, '.join(lines[::-1][:1])

#        return app.send_static_file('log.txt')
    else:
        return "No logs"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

