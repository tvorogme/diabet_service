from pymongo import MongoClient

client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = {'name': "Василий Пупкин", "phone": "+79150187307", "email": "admin@diabetlab.ru", "pass": "adminPassword"}

user_id = db['users'].insert_one(user).inserted_id

print(user_id)