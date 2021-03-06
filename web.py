from bottle import route, run, request, response
from jinja2 import Environment, FileSystemLoader
from pymongo.errors import DuplicateKeyError
from random import SystemRandom
import sqlite3
from baseconv import BaseConverter
import sys
import re

GOOD_CHARS = 'abcdefghkmnpqrstwxyz'
GOOD_DIGITS = '23456789'
CRYPTO_CHARS = GOOD_CHARS + GOOD_CHARS.upper() + GOOD_DIGITS
DB = sqlite3.connect('var/sbin.sqlite')
ENV = Environment(loader=FileSystemLoader('templates'))
CONV = BaseConverter(CRYPTO_CHARS)


def render(tpl_name, **kwargs):
    tpl = ENV.get_template(tpl_name)
    return tpl.render(**kwargs)


def create_dump(data):
    gen = SystemRandom() 
    for x in range(10):
        new_id = gen.randint(1, sys.maxsize)
        try:
            DB.execute('''
                INSERT INTO dump (id, data)
                VALUES (?, ?)
            ''', (new_id, data))
            DB.commit()
        except sqlite3.IntegrityError:
            pass
        else:
            return new_id
    raise Exception('Could not generate unique ID for new dump')


@route('/')
def home_page():
    return render('home.html')


@route('/add', ['GET', 'POST'])
def home_page():
    if request.method == 'GET':
        return render('home.html')
    else:
        data = request.forms.get('data')
        if not data:
            return render('home.html', data_error='Data is empty')
        dump_id = create_dump(data)
        short_id = CONV.encode(dump_id)
        response.headers['location'] = '/%s' % short_id
        response.status = 302
        return response


@route('/<short_id:re:[a-zA-Z0-9]{1,20}>')
def dump_page(short_id):
    if not re.compile('^[%s]+$' % CRYPTO_CHARS).match(short_id):
        response.status = 404
        return '<h3 style="color: red">Invalid dump ID</h3>'
    dump_id = CONV.decode(short_id)
    res = DB.execute('''
        SELECT data FROM dump
        WHERE id = ?
    ''', (dump_id,))
    row = res.fetchone()
    if row is None:
        response.status = 404
        return '<h3 style="color: red">Invalid dump ID</h3>'
    else:
        data = row[0]
        return render('dump.html', data=data) 
        #response.headers['content-type'] = 'text/plain'
        #return row[0]


if __name__ == '__main__':
    run(host='localhost', port=9000, debug=True, reloader=True)
