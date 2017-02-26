import datetime

from pymongo import MongoClient
import random


client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = db['users'].find_one({'email':'roctbb@gmail.com'})

print(user['_id'])

name = str(user['_id'])

now_date = datetime.datetime(2016, 9,15,0,0);
today = datetime.datetime.now()
date_copy = now_date

while date_copy<today:
    interval = random.randint(30, 40)
    date_copy += datetime.timedelta(days=interval)
    print(date_copy.strftime("%Y-%m-%d %H:%M:%S"))
    db['results'].insert_one({
        "value": random.randint(80, 100),
        "time": date_copy.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "WE",
        "user_id": name,
        "name": 'Вес'
    })

now_date = datetime.datetime(2016, 3,15,0,0);
today = datetime.datetime.now()
date_copy = now_date

while date_copy<today:
    interval = random.randint(60, 90)
    date_copy += datetime.timedelta(days=interval)
    print(date_copy.strftime("%Y-%m-%d %H:%M:%S"))
    db['results'].insert_one({
        "value": random.randint(1,20),
        "time": date_copy.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "GG",
        "user_id": name,
        "name": 'Гликированный гемоглобин'
    })
now_date = datetime.datetime(2016, 12,15,0,0);
today = datetime.datetime.now()
date_copy = now_date
while date_copy<today:
    interval = random.randint(1, 4)
    date_copy += datetime.timedelta(days=interval)
    print(date_copy.strftime("%Y-%m-%d %H:%M:%S"))
    db['results'].insert_one({
        "lvalue": random.randint(50, 90),
        "hvalue": random.randint(80, 130),
        "time": date_copy.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "AD",
        "user_id": name,
        "name": 'Артериальное давление'
    })

now_date = datetime.datetime(2016, 3,15,0,0);
today = datetime.datetime.now()
date_copy = now_date