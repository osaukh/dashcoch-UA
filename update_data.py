# -*- coding: utf-8 -*-
import re
import pandas as pd
from urllib import request
from datetime import date


URL = 'https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html'
STATES = {
    'Burgenland': 'B',
    'K&auml;rnten': 'K',
    'Nieder&ouml;sterreich': 'NÖ',
    'Ober&ouml;sterreich': 'OÖ',
    'Salzburg': 'S',
    'Steiermark': 'ST',
    'Tirol': 'T',
    'Vorarlberg': 'V',
    'Wien': 'W'
}
FILE_FATALITIES = 'data_AT/covid19_fatalities_austria.csv'
FILE_CASES = 'data_AT/covid19_cases_austria.csv'


def retrieve():
    r = request.urlopen(URL).read().decode().replace('\n', '').replace('\t', '').replace('&nbsp;', '')
    regex_cases = re.compile('<p><strong>Best(.*)Todes')
    regex_fatalities = re.compile('<p><strong>Todes(.*)</p>')
    regex = re.compile('([\w&;]+) \(([\d.]+)\)')

    cases = regex.findall(regex_cases.search(r).group(1))
    fatalities = regex.findall(regex_fatalities.search(r).group(1))

    return cases, fatalities


def append_csv(filename, data):
    df = pd.read_csv(filename)

    values = {k[1]:0 for k in STATES.items()}
    for d in data: 
        values[STATES[d[0]]] = int(d[1].replace('.', ''))

    values['AT'] = sum([v[1] for v in values.items()])   
    values['Date'] = date.today().strftime('%Y-%m-%d')

    df = df.append(values, ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df.to_csv(filename)


def update_data():
    cases, fatalities = retrieve()
    append_csv(FILE_CASES, cases)
    append_csv(FILE_FATALITIES, fatalities)


if __name__ == "__main__":
    update_data()
