from flask import Flask, redirect, render_template, url_for
import pandas as pd
import threading
import datetime
import sqlite3
import os

app = Flask(__name__)


def load_db(t):
    if t is not None:
        print('Esperando sincronizacao anterior')
        t.join()
        return
    # Load
    print('Loading data')
    conn = sqlite3.connect('Banco.db')
    df_contas = pd.read_sql_query("SELECT * from CONTAS", conn)
    df_contas.DATA = pd.to_datetime(df_contas.DATA, format='%d/%m/%Y %H:%M:%S')
    df_prods = pd.read_sql_query("SELECT * from PRODUTOS", conn, parse_dates=False)

    # Clean data
    df_contas.DATA = pd.to_datetime(df_contas.DATA)
    df_contas = df_contas[df_contas.NOME != 'Excluido']
    df_contas.index = pd.to_datetime(df_contas.DATA, dayfirst=False, yearfirst=True)
    print('Cleaning data')
    df_contas = df_contas[df_contas.DATA >= '2016-01-01']
    df_contas.to_csv('data.csv', quoting=2, index=False)
    print('OK')
    return


def get_last_modified():
    modified_at = datetime.datetime.fromtimestamp(os.path.getmtime('Banco.db'))
    modified_at = modified_at.replace(hour=modified_at.hour-3)
    modified_at = modified_at.strftime('%d/%m/%Y %H:%M')
    return modified_at


def get_report(df_contas):
    report = df_contas.tail(50).set_index('DATA').to_html(classes=['table', 'table-hover'])
    return report


@app.route("/")
def hello():
    global t
    t = threading.Thread(target=load_db, args=(t,))
    t.daemon = True
    t.start()

    data = dict()

    if os.path.exists('data.csv'):
        modified_at = get_last_modified()
        df_contas = pd.read_csv('data.csv')
        print(len(df_contas))
        data['modified_at'] = modified_at
        data['table'] = get_report(df_contas)
        return render_template('main.html', data=data)
    else:
        data['msg'] = 'Carregando..Tente novamente em alguns segundos'
        return render_template('main.html', data=data)

t = None
if __name__ == "__main__":
    app.run(debug=True)