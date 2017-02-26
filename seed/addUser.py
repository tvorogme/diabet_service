from pymongo import MongoClient

client = MongoClient('mongodb://roctbb:rcw000000@ds161029.mlab.com:61029/diabetlab')

db = client['diabetlab']

user = {'name': "Василий Пупкин", "phone": "+79150187307", "email": "admin@diabetlab.ru", "pass": "adminPassword",
        'GL1': 4, 'GL2': 7, 'GH1': 4, 'GH2': 10, 'IK_name': 'Рапидра', 'ID_name': 'Рапидра Базальный' }

user_id = db['users'].insert_one(user).inserted_id

print(user_id)


user = {'name': "Бородин Ростислав", "phone": "+79150187307", "email": "roctbb@gmail.com", "pass": "rcw000000",
        'GL1': 4, 'GL2': 7, 'GH1': 4, 'GH2': 10, 'IK_name': 'Рапидра', 'ID_name': 'Рапидра Базальный' }

user_id = db['users'].insert_one(user).inserted_id

print(user_id)