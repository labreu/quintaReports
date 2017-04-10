import shutil
from flask import Flask, redirect, render_template, url_for, jsonify
import pandas as pd
import threading
import datetime
import sqlite3
import os
import time

pd.options.display.float_format = 'R${:,.2f}'.format

app = Flask(__name__)


def call_load_db():
    print("Iniciando loop")
    c = 0
    while True:
        load_db(c)
        c += 1


def load_db(c):

    print("Loading db..")
    os.system("onedrive-d restart")
    print("Onedrive restartado")
    os.remove('Banco.db')
    print("Copiando arquivo do Banco")
    shutil.copyfile('../OneDrive/Documentos/Banco.db', 'Banco.db')
    print("Banco copiado")
    print('Conectando ao banco local copiado')
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
    print("Sleeping")
    time.sleep(60)
    print("Pronto")
    return True


def get_report(tempo, qtd):
    df_contas = read_treat_data()

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
    df_contas.columns = ['ID', 'Conta', 'Código Produto', 'Produto', 'Preço', 'Data']
    df_contas.Data = pd.to_datetime(df_contas.Data)
    df_contas.set_index('Data', inplace=True)
    return df_contas


@app.route("/time/<int:tempo>/qtd/<int:qtd>")

def rest_report(tempo, qtd):
    try:
        if os.path.exists('data.csv'):
            df = read_treat_data()
            report, report_json = get_report(tempo, qtd)

        return jsonify(
            {
                "tempo": tempo,
                "qtd": qtd,
                "report": report,
                "report_json": report_json
             }
        )
    except Exception as e:
        print(e)
        return "erro"


@app.route("/")
def hello():
    return render_template('main.html')


@app.route('/log')
def root():
    if os.path.exists("static/log.txt"):
        return app.send_static_file('log.txt')
    else:
        return "No logs"

# t = threading.Thread(target=call_load_db)
# t.daemon = True
# t.start()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
