import os
import uuid
from time import strftime, gmtime

import config
import telebot
from pymongo import MongoClient
from client import private_config
import requests
from PIL import Image

client = MongoClient(private_config.mongo_connection)
db = client['diabetlab']

bot = telebot.TeleBot(config.token)

temp_storage = {}

def password(message):
   temp_storage[message.chat.id] = message.text
   msg = bot.send_message(message.chat.id, text="Введите ваш пароль от DiaFriend:")
   bot.register_next_step_handler(msg, makeLogin)

def login(id):
    user = db['users'].find_one({'chat_id': id})
    if user != None:
        return user
    msg = bot.send_message(id, text="Введите ваш Email от DiaFriend:")
    bot.register_next_step_handler(msg,password)
    return None

def makeLogin(message):
    log = temp_storage[message.chat.id]
    pasw = message.text
    user = db['users'].find_one({'email': log, 'pass': pasw})
    if user == None:
        bot.send_message(message.chat.id, text='К сожалению, данные неверны. Попробуйте еще раз!')
        login(message.chat.id)
    else:
        user['chat_id'] = message.chat.id
        db['users'].update({'_id': user['_id']}, user)
        bot.send_message(message.chat.id, user['name']+', здравствуйте!')


@bot.message_handler(content_types=['photo'])
def start(message):
    user = login(message.chat.id)
    if user != None:
        file_id = message.photo[-1].file_id
        path = bot.get_file(file_id)
        print(path)
        extn = '.'+str(path.file_path).split('.')[-1]
        downloaded_file = bot.download_file(path.file_path)
        cname = str(uuid.uuid4()) + extn
        with open(os.path.dirname(os.path.realpath(__file__)) +'/../client/images/'+cname, 'wb') as new_file:
            new_file.write(downloaded_file)
        im = Image.open(os.path.dirname(os.path.realpath(__file__)) + '/../client/images/' + cname);
        im.thumbnail((300, 300), Image.ANTIALIAS)
        im.save(os.path.dirname(os.path.realpath(__file__)) + '/../client/images/' + cname)
        try:
            tvorog = requests.get('http://185.106.141.196:9991/roctbb?url=http://roctbb.net:5555/images/' + cname)
            food = tvorog.text
        except:
            food= ''
        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        data = {'type': 'FD', 'filename': cname, 'user_id': str(user['_id']), 'time': current_time, 'text': food}
        bot.send_message(message.chat.id, "Я записал это в дневник питания. Я думаю, что это - "+food)
        db['results'].insert_one(data)


@bot.message_handler(commands=['start'])
def start(message):
    user = login(message.chat.id)
    if user != None:
        bot.send_message(message.chat.id, user['name'] + ', вы уже авторизировались!')

@bot.message_handler(commands=['sugar'])
def ask_sugar(message):
    user = login(message.chat.id)
    if user != None:
        msg = bot.send_message(message.chat.id, text='Какой у вас сейчас уровень сахара?')
        bot.register_next_step_handler(msg, save_sugar)

def processSugar(message, value, user):
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    data = {'type': 'GL', 'value': float(value), 'user_id': str(user['_id']), 'time': current_time}
    bot.send_message(message.chat.id, text='Спасибо, я записал.')
    if value >= user['GL1'] and value <= user['GL2']:
        bot.send_message(message.chat.id, text='Уровень глюкозы в крови в норме.')
    elif value < user['GL1'] and value >= user['GH1']:
        bot.send_message(message.chat.id,
                         text='Уровень глюкозы в крови ниже рекомендованного значение, вам необходимо его компенсировать.')
    elif value < user['GH1']:
        bot.send_message(message.chat.id,
                         text='ВАМ СРОЧНО НЕОБХОДИМО КОМПЕНСИРОВАТЬ УРОВЕНЬ ГЛЮКОЗЫ!')
    else:
        bot.send_message(message.chat.id,
                         text='Уровень глюкозы в крови выше нормы. Примите рекомендованную вам терапию, либо проконсультируйтесь со специалистом.')
    db['results'].insert_one(data)
def save_sugar(message):
    user = login(message.chat.id)
    if user != None:
        try:
            value = message.text.replace(',', '.')
            value = float(value)
            processSugar(message, value, user)
        except:
            bot.send_message(message.chat.id, text='Я вас не понял, попробуйте еще раз :(')
            ask_sugar(message)

@bot.message_handler(content_types=["text"])
def textAnswer(message): # Название функции не играет никакой роли, в принципе
    user = login(message.chat.id)
    if user != None:
        text = str(message.text)
        if text.find('допустимый уровень')!=-1:
            bot.send_message(message.chat.id, "Ваш допустимый уровень глюкозы в крови от "+user['GH1']+" до "+user['GH2'])
        if text.find('целевой')!=-1 or text.find('рекомендуемый')!=-1 :
            bot.send_message(message.chat.id, "Ваш допустимый уровень глюкозы в крови от "+user['GL1']+" до "+user['GL1'])
        if text.lower().find('сахар') != -1:
            try:
                value = float(text.split()[1])
                processSugar(message, value, user)
            except:
                bot.send_message(message.chat.id, "Простисте, я вас не понял.")





if __name__ == '__main__':
     bot.polling(none_stop=True)