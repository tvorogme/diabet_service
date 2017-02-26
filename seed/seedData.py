import datetime

from pymongo import MongoClient
import random


client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = db['users'].find_one({'email':'diab@diab.ru'})

name = str(user['_id'])

now_date = datetime.datetime(2017, 2,15,0,0);

while now_date.day<=26:
    interval = random.randint(60, 180)
    now_date += datetime.timedelta(minutes=interval)
    if (now_date.hour<7):
        continue

    print(now_date.strftime("%Y-%m-%d %H:%M:%S"))
    if random.randint(1,7)==1:
        db['results'].insert_one({
            "value": random.randint(10, 40),
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "ID",
            "user_id": name
        })
        continue
    if random.randint(1,7)==2:
        db['results'].insert_one({
            "value": random.randint(10, 40),
            'medicine': 'Сахаропонижел',
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "MD",
            "user_id": name
        })
        continue
    if random.randint(1,5)==1:
        db['results'].insert_one({
            "value": random.randint(5, 20),
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "IK",
            "user_id": name
        })
        continue

    db['results'].insert_one({
        "value": random.randint(30,130)/10,
        "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "GL",
        "user_id": name
    })
now_date = datetime.datetime(2016, 9,15,0,0);
today = datetime.datetime.now()
date_copy = now_date

while date_copy<today:
    interval = random.randint(30, 40)
    date_copy += datetime.timedelta(days=interval)
    print(date_copy.strftime("%Y-%m-%d %H:%M:%S"))
    db['results'].insert_one({
        "value": random.randint(70, 100),
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
now_date = datetime.datetime(2017, 2,15,0,0);

while now_date.day<=26:
    interval = random.randint(300, 400)
    now_date += datetime.timedelta(minutes=interval)
    if (now_date.hour<7):
        continue

    print(now_date.strftime("%Y-%m-%d %H:%M:%S"))

    db['results'].insert_one({
        "filename": str(random.randint(1,4))+'.jpg',
        "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "FD",
        "text": 'Ужасная жирная еда!',
        "user_id": str(user['_id'])
    })
