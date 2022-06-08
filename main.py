from urllib import response
from flask import Flask, request, render_template, redirect
from flask import abort, jsonify
from math import floor
import json
from sqlite3 import OperationalError
import string
import sqlite3
try:
    from urllib.parse import urlparse
    str_encode = str.encode
except ImportError:
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import base64


# Assuming urls.db is in your app root folder
app = Flask(__name__)

host = 'https://shortern-url.herokuapp.com/'
# host = 'http://localhost:5000/'


def table_check():
    create_table = """
        CREATE TABLE WEB_URL(
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        URL TEXT NOT NULL
        );
        """
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
        except OperationalError:
            pass


def toBase62(num, b=62):
    if b <= 0 or b > 62:
        return 0
    base = string.digits + ascii_lowercase + ascii_uppercase
    r = num % b
    res = base[r]
    q = floor(num / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res


def toBase10(num, b=62):
    base = string.digits + ascii_lowercase + ascii_uppercase
    limit = len(num)
    res = 0
    for i in range(limit):
        res = b * res + base.find(num[i])
    return res


def insertURLToDB(url):
    if urlparse(url).scheme == '':
        url = 'http://' + url
    else:
        url = url
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        try:
            res = cursor.execute(
                'INSERT INTO WEB_URL (URL) VALUES (?)',
                [base64.urlsafe_b64encode(bytes(url, 'utf-8'))]
            )
        except Exception as e:
            res = cursor.execute(
                'INSERT INTO WEB_URL (URL) VALUES (?)',
                [base64.urlsafe_b64encode(url)]
            )

        conn.commit()

        return toBase62(res.lastrowid)


@ app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = str_encode(request.form.get('url'))
        encoded_string = insertURLToDB(original_url)
        return render_template('home.html', short_url=host + encoded_string)

    return render_template('home.html')


@ app.route('/<short_url>')
def redirect_short_url(short_url):
    try:
        decoded = toBase10(short_url)
        url = host  # fallback if no URL is found
        with sqlite3.connect('urls.db') as conn:
            cursor = conn.cursor()
            res = cursor.execute(
                'SELECT URL FROM WEB_URL WHERE ID=?', [decoded])
            short = res.fetchone()
    except Exception as e:
        abort(500)

    if short is not None:
        redirectURL = base64.urlsafe_b64decode(short[0]).decode("utf-8")
        return redirect(redirectURL, code=302, Response=None)
    else:
        abort(404)


@ app.route('/api/', methods=['POST'])
def redirect_short_url_api():
    req_data = request.get_json(force=True)
    if str(req_data['token']) != 'RGFEAxTtAT5hkKum':
        abort(404)
    try:
        responseList = []
        urls = req_data['urls']
        for url in urls:
            id = insertURLToDB(url)
            responseList.append({'originalURL:': url, 'shortURL': host + id})
        return {'response': responseList}
    except Exception as e:
        abort(500)


@ app.errorhandler(404)
def error_404(e):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def error_500(e):
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    table_check()
    debugBol = False
    if 'localhost' in host:
        debugBol = True
    app.run(debug=debugBol)
