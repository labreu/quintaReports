from flask import Flask, redirect, render_template, url_for
import pandas as pd
import threading
import datetime
import sqlite3
import os
pd.options.display.float_format = 'R${:,.2f}'.format


app = Flask(__name__)


def load_db(t):
    if t is not None:
        print('Esperando sincronizacao anterior')
        t.join()
        return
    # Load
    print('Loading data')
    conn = sqlite3.connect('../OneDrive/Documentos/Banco.db')


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
    modified_at = datetime.datetime.fromtimestamp(os.path.getmtime('Banco.db')).strftime('%d/%m/%Y %H:%M')

    return modified_at


def get_report(df_contas):

    reports = dict()
    df_contas.Data = pd.to_datetime(df_contas.Data)
    df_contas.set_index('Data', inplace=True)

    report = df_contas.tail(50).sort_index(ascending=False).to_html(classes=['table', 'table-hover'])
    reports['last_n'] = report


    for i in ['d', 'w', 'm']:
        rp = pd.DataFrame(df_contas.resample(i).sum()['Preço'].tail(7).fillna(0))
        rp.index = rp.index.date
        rp.columns = ['Total']
        reports[i] = rp.T\
            .to_html(classes=['table', 'table-hover'])
        # reports[i] = rp.T.style.background_gradient('winter', axis=1).render()

    return reports


@app.route("/")
def hello():
    global t
    t = threading.Thread(target=load_db, args=(t,))
    t.daemon = True
    t.start()

    data = dict()

    if os.path.exists('data.csv'):
        df_contas = pd.read_csv('data.csv')
        df_contas.columns = ['ID', 'Conta', 'Código Produto', 'Produto', 'Preço', 'Data']
        data['modified_at'] = get_last_modified()
        data['reports'] = get_report(df_contas)
        return render_template('main.html', data=data)
    else:
        data['msg'] = 'Carregando..Tente novamente em alguns segundos'
        return render_template('main.html', data=data)

t = None
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
