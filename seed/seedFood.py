import datetime

from pymongo import MongoClient
import random


client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = db['users'].find_one({'email':'diab@diab.ru'})

print(user['_id'])

now_date = datetime.datetime(2017, 2,15,0,0);

while now_date.day<=26:
    interval = random.randint(240, 300)
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
