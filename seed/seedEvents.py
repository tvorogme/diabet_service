import datetime

from pymongo import MongoClient
import random

client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = db['users'].find_one({'email': 'diab@diab.ru'})

name = str(user['_id'])

today = datetime.datetime.now().date()
now_date = today + datetime.timedelta(days=-30)
year = today+ datetime.timedelta(days=30*12)


# seed insuline and ad

events = []

while now_date<year:

    # suger
    hours = [9, 12, 15, 18];
    for hour in hours:
        time = datetime.datetime.combine(now_date, datetime.time(hour, 0))
        event = {
            'time': time,
            'type': 'GL',
            'title': 'Измерение уровня глюкозы',
            'user': name
        }
        events.append(event)

    #bolus (food)
    hours = [9,12,18];
    for hour in hours:
        time = datetime.datetime.combine(now_date, datetime.time(hour,30))
        event = {
            'time': time,
            'type': 'FD',
            'title': 'Прием пищи',
            'description': '',
            'user': name
        }
        events.append(event)

    #basal
    hours = [8, 20];
    for hour in hours:
        time = datetime.datetime.combine(now_date, datetime.time(hour, 0))
        event = {
            'time': time,
            'type': 'ID',
            'title': 'Базальный инсулин',
            'description': '',
            'user': name
        }
        events.append(event)

    #ad
    hours = [8, 20];
    for hour in hours:
        time = datetime.datetime.combine(now_date, datetime.time(hour, 40))
        event = {
            'time': time,
            'type': 'AD',
            'title': 'Измерение артериального давления',
            'description': '',
            'user': name
        }
        events.append(event)

    now_date += datetime.timedelta(days=1)

#seed disp
now_date = today
for i in range(2):
    time = datetime.datetime.combine(now_date, datetime.time(12, 00))
    event = {
        'time': time,
        'type': 'DS',
        'title': 'Диспансеризация: общий анализ крови, биохимия, ЭКГ, осмотр ног, рентген грудной клетки, осмотр офтальмолога.',
        'description': '',
        'user': name
    }
    now_date += datetime.timedelta(days=30*12)
    events.append(event)

now_date = today
for i in range(10):
    time = datetime.datetime.combine(now_date, datetime.time(12, 00))
    event = {
        'time': time,
        'type': 'GG',
        'title': 'Анализ крови на гликированный гемоглобин.',
        'description': '',
        'user': name
    }
    now_date += datetime.timedelta(days = 30*3)
    events.append(event)

now_date = today
for i in range(20):
    time = datetime.datetime.combine(now_date, datetime.time(12, 00))
    event = {
        'time': time,
        'type': 'WE',
        'title': 'Измерение веса.',
        'description': '',
        'user': name
    }
    now_date += datetime.timedelta(days = 7)
    events.append(event)


db['events'].insert(events)