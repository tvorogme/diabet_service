import datetime

from pymongo import MongoClient
import random


client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = db['users'].find_one({'email':'roctbb@gmail.com'})

name = str(user['_id'])

now_date = datetime.datetime(2017, 2,15,0,0);

while now_date.day<26:
    interval = random.randint(60, 180)
    now_date += datetime.timedelta(minutes=interval)
    if (now_date.hour<7):
        continue

    print(now_date.strftime("%Y-%m-%d %H:%M:%S"))
    if random.randint(1,5)==1:
        db['results'].insert_one({
            "value": random.randint(10, 40),
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "ID",
            "user_id": name
        })
        continue
    if random.randint(1,5)==2:
        db['results'].insert_one({
            "value": random.randint(10, 40),
            'medicine': 'Сахаропонижел',
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "MD",
            "user_id": name
        })
        continue
    if random.randint(1,3)==1:
        db['results'].insert_one({
            "value": random.randint(5, 20),
            "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "IK",
            "user_id": name
        })
        continue

    db['results'].insert_one({
        "value": random.randint(30,100)/10,
        "time": now_date.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "GL",
        "user_id": name
    })
