'''
This is a "hello world" flask webpage.
During the last 2 weeks of class,
we will be modifying this file to demonstrate all of flask's capabilities.
This file will also serve as "starter code" for your Project 5 Twitter webpage.

NOTE:
the module flask is not built-in to python,
so you must run pip install in order to get it.
After doing do, this file should "just work".
'''
import sqlite3
import os
import datetime
import re
import argparse
import requests # request img from web
import shutil # save img locally
parser = argparse.ArgumentParser(description='Create a database for the twitter project')
parser.add_argument('--db_file', default='twitter_clone.db')
args = parser.parse_args()
from flask import Flask, render_template, request, make_response
app = Flask(__name__)

@app.route('/')     
def root():
    print_debug_info()
    # check if logged in correctly
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)
    print('good_credentials=', good_credentials)

    con = sqlite3.connect(args.db_file)
    cur = con.cursor()

    cur.execute('''
        SELECT sender_id, message, created_at, id FROM messages ORDER BY created_at ASC;
    ''')
    rows = cur.fetchall()
    messages = []

    cur.execute('''
        SELECT id, username, age FROM users
    ''')
    users = cur.fetchall()

    id_info = {}

    for id, username, age in users:
        id_info[id] = (username, age)

    for row in rows:
        if row[3] in id_info:
            messages.append({'username': id_info[row[3]][0], 'text': row[1], 'created_at':row[2], 'id':row[3], 'age':id_info[row[3]][1]})
        else:
            messages.append({'username': row[0], 'text': row[1], 'created_at':row[2], 'id':row[3], 'age':None})
    messages.reverse()

    print(messages)

    return render_template('root.html', messages=messages, logged_in=good_credentials, username=username, password=password)

def print_debug_info():
    # GET method
    print('request.args.get("username")=', request.args.get("username"))
    print('request.args.get("password")=', request.args.get("password"))

    # POST method
    print('request.form.get("username")=', request.form.get("username"))
    print('request.form.get("password")=', request.form.get("password"))

    # cookies
    print('request.cookies.get("username")=', request.cookies.get("username"))
    print('request.cookies.get("password")=', request.cookies.get("password"))


def are_credentials_good(username, password):
    con = sqlite3.connect(args.db_file)
    users={}
    cur=con.cursor()
    cur.execute('SELECT username, password FROM users;')
    for user in cur.fetchall():
        users[user[0]] = user[1]
    return username in users and password == users[username]
#get users and check if username and password exist  

@app.route('/home', methods=['get', 'post'])
def home():

    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)
    print('good_credentials=', good_credentials)

    con = sqlite3.connect(args.db_file)
    cur = con.cursor()

    cur.execute('''
        SELECT sender_id, message, created_at, id FROM messages ORDER BY created_at DESC;
    ''')
    rows = cur.fetchall()
    messages = []

    cur.execute('''
        SELECT id, username, age FROM users
    ''')
    users = cur.fetchall()

    id_info = {}

    for id, username, age in users:
        id_info[id] = (username, age)

    cur.execute('''
        SELECT username FROM users
    ''')
    users2 = cur.fetchall()

    for user in users2:
        user = user[0]
        if os.path.exists(f"static/images/{user}"):
            continue
        else:
            res = requests.get(f"https://robohash.org/{user}", stream = True)
            if res.status_code == 200:
                with open(f"static/images/{user}",'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                print('Image sucessfully Downloaded')
            else:
                print('Image Couldn\'t be retrieved')

    for row in rows:
        if row[3] in id_info:
            messages.append({'username': id_info[row[3]][0], 'text': row[1], 'created_at':row[2], 'id':row[3], 'age':id_info[row[3]][1]})
        else:
            messages.append({'username': row[0], 'text': row[1], 'created_at':row[2], 'id':row[3], 'age':None})
    #finds urls and adds <a> tags 
    for message in messages:
        text = message['text']
        message['link'] = False
        matches = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for match in matches:
            text = text.replace(match, f"<a href='{match}'> {match} </a>")
            message['link'] = True
        message['text']=text
        
    if good_credentials:
        return render_template('home.html',username=request.cookies.get('username'), password=request.cookies.get('password'), messages=messages)
    else:
        return render_template('home.html', messages=messages)

@app.route('/login', methods=['GET', 'POST'])     
def login():
    print_debug_info()
    username = request.form.get('username')
    password = request.form.get('password')
    print('username=', username)
    print('password=', password)

    good_credentials = are_credentials_good(username, password)
    print('good_credentials=', good_credentials)

    if username is None:
        return render_template('login.html', bad_credentials=False)
    else:
        if not good_credentials:
            return render_template('login.html', bad_credentials=True)
        else:
            template = render_template(
                'login.html', 
                good_credentials=True,
                logged_in=True)

            response = make_response(template)
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response

@app.route('/logout')     
def logout():
    print_debug_info()

    response = make_response(render_template('logout.html'))
    response.set_cookie('username', '', expires=0) 
    response.set_cookie('password', '', expires=0)
    return response

@app.route('/create_message',methods=['GET','POST'])     
def create_message():
    if(request.cookies.get('username') and request.cookies.get('password')):
        if request.form.get('new_message'):
            con = sqlite3.connect(args.db_file)
            cur = con.cursor()
            cur.execute('''
                INSERT INTO messages (sender_id, message, created_at) values (?, ?, ?);
            ''', (request.cookies.get('username'), request.form.get('new_message'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            con.commit()
            return make_response(render_template('create_message.html', created=True, username=request.cookies.get('username'), password=request.cookies.get('password')))
        else:
            return make_response(render_template('create_message.html', created=False, username=request.cookies.get('username'), password=request.cookies.get('password')))
    else:
        return home()

@app.route('/create_user',methods=['GET','POST'])     
def create_user():
    print_debug_info()

    if request.form.get('username'):
        if request.form.get('password1') == request.form.get('password2'):
            con = sqlite3.connect('twitter_clone.db')
            cur = con.cursor()

            cur.execute('''
                SELECT username from users where username=?;
            ''', (request.form.get('username'),))
            rows = cur.fetchall()
            if len(rows) > 0:
                return make_response(render_template('create_user.html', exists=True)) 

            cur.execute('''
                INSERT INTO users (username, password) values (?, ?);
            ''', (request.form.get('username'), request.form.get('password1')))
            con.commit()

            response = make_response(render_template('create_user.html', successful = True))
            response.set_cookie('username', request.form.get('username'))
            response.set_cookie('password', request.form.get('password1'))
            return response
        else:
            return make_response(render_template('create_user.html', successful = False, wrongPass = True))
    else:
        return make_response(render_template('create_user.html'))

@app.route('/delete_message/<id>', methods=['GET'])
def delete_message(id):

    con = sqlite3.connect(args.db_file) 
    cur = con.cursor()
    cur.execute('''
        SELECT sender_id from messages WHERE id=?;
    ''', (id,))
    rows = cur.fetchall()
    if rows[0][0] == request.cookies.get('username'):
        cur.execute('''
            DELETE from messages WHERE id=?;
        ''', (id,))
        con.commit()
        return make_response(render_template('delete_message.html', not_user=False, username=request.cookies.get('username'), password=request.cookies.get('password')))
    else:
        return make_response(render_template('delete_message.html', not_user=True, username=request.cookies.get('username'), password=request.cookies.get('password')))

@app.route('/edit_message/<id>', methods=['GET', 'POST'])
def edit_message(id):
    new_message = request.form.get('new_message')
    con = sqlite3.connect(args.db_file) 
    cur = con.cursor()
    cur.execute('''
        SELECT sender_id, message, created_at from messages where id=?;
    ''', (id,))
    rows = cur.fetchall()
    if new_message is None:
        if rows[0][0] == request.cookies.get('username'):
            return make_response(render_template('edit_message.html', not_user=False, text=rows[0][1], id=id, username=request.cookies.get('username'), password=request.cookies.get('password')))
        else:
            return make_response(render_template('edit_message.html', not_user=True, username=request.cookies.get('username'), password=request.cookies.get('password')))
    else:
        if rows[0][0] != request.cookies.get('username'):
            return make_response(render_template('edit_message.html', not_user=True, username=request.cookies.get('username'), password=request.cookies.get('password')))
        else:
            cur.execute('''
                UPDATE messages
                SET message=?
                WHERE id=?
            ''', (new_message, id))

            created_at = rows[0][2]

            if " Edited" in created_at:
                created_at = created_at.split(" Edited")[0]

            cur.execute('''
                UPDATE messages
                SET created_at=?
                WHERE id=?
            ''', (created_at + " Edited at: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
            con.commit()
            template = render_template(
                'edit_message.html', 
                not_user=False,
                finished=True, 
                username=request.cookies.get('username'), 
                password=request.cookies.get('password'))
            response = make_response(template)
            
            return response


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    new_password1 = request.form.get('new_password1')
    new_password2 = request.form.get('new_password2')
    old_password = request.form.get('old_password')

    con = sqlite3.connect(args.db_file) 
    cur = con.cursor()
    cur.execute('''
        SELECT username, password 
        FROM users
        WHERE username=?
    ''', (request.cookies.get("username"),))
    rows = cur.fetchall()

    if len(rows) == 0:
        return make_response(render_template('change_password.html', not_logged=True))
    

    print("new password1", new_password1)
    if new_password1 is None and new_password2 is None and old_password is None:
        return make_response(render_template('change_password.html', username=request.cookies.get('username'), password=request.cookies.get('password'), reset_password=False))
    else:
        
        
        if old_password != rows[0][1]:
            return make_response(render_template('change_password.html', username=request.cookies.get('username'), password=request.cookies.get('password'), wrong_password=True))
        
        if new_password1 != new_password2:
            return make_response(render_template('change_password.html', username=request.cookies.get('username'), password=request.cookies.get('password'), mismatch=True))

        if new_password1 is None and new_password2 is None:
            return make_response(render_template('change_password.html', username=request.cookies.get('username'), password=request.cookies.get('password'), none=True))

        cur.execute('''
            UPDATE users
            SET password=?
            WHERE username=?
        ''', (new_password1, request.cookies.get("username")))
        con.commit()
        return make_response(render_template('change_password.html', username=request.cookies.get('username'), password=request.cookies.get('password'), good=True))


@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    confirm = request.form.get('confirm')

    con = sqlite3.connect(args.db_file) 
    cur = con.cursor()
    cur.execute('''
        SELECT username, password 
        FROM users
        WHERE username=?
    ''', (request.cookies.get("username"),))
    rows = cur.fetchall()

    if len(rows) == 0:
        return make_response(render_template('delete_account.html', not_logged=True))
    if confirm is None:
        return make_response(render_template('delete_account.html'))
    else:
        if confirm != "CONFIRM":
            return make_response(render_template('delete_account.html', wrong_confirm=True))
        
        cur.execute('''
            DELETE 
            FROM users
            WHERE username=? AND password=?
        ''', (request.cookies.get("username"), request.cookies.get("password")))
        con.commit()

        response = make_response(render_template('delete_account.html', deleted=True))
        response.set_cookie('username', '', expires=0) 
        response.set_cookie('password', '', expires=0)

        return response

app.run()
