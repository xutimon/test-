#!/usr/bin/python3
'''
Create a database for the Twitter project.
'''

# sqlite3 is built in python3, no need to pip3 install
import sqlite3
import datetime

# process command line arguments
import argparse
parser = argparse.ArgumentParser(description='Create a database for the twitter project')
parser.add_argument('--db_file', default='twitter_clone.db')
# there is no standard file extension; people use .db .sql .sql3 .database
args = parser.parse_args()

# connect to the database
con = sqlite3.connect(args.db_file)   # con, conn = connection; always exactly 1 of these variables per python project
cur = con.cursor()                    # cur = cursor; for our purposes, exactly 1 of these per python file

from madlibs2 import generate_comment

new_users = []

import random
import string

for i in range(210):
    new_users.append(''.join(random.choices(string.ascii_lowercase, k=5)))

new_users = list(set(new_users))
#inserts users
for user in new_users:
    pw = ''.join(random.choices(string.ascii_lowercase, k=5))
    cur.execute(f"insert into users (username, password) values ('{user}', '{pw}');")
    con.commit()
#creates messages    
for i in range(201):
    for user in new_users:
        comment = generate_comment()
        cur.execute('''
                INSERT INTO messages (sender_id, message, created_at) values (?, ?, ?);
            ''', (user, comment, (datetime.datetime.now() - datetime.timedelta(5)).strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()

