from time import strftime, gmtime

import config
import telebot
from pymongo import MongoClient
from client import private_config

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

def save_sugar(message):
    user = login(message.chat.id)
    if user != None:
        try:
            value = message.text.replace(',', '.')
            value = float(value)
            current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            data = {'type': 'GL', 'value': float(value), 'user_id': str(user['_id']), 'time': current_time}
            bot.send_message(message.chat.id, text='Спасибо, я записал.')
            if value>=4 and value<=5.5:
                bot.send_message(message.chat.id, text='Уровень глюкозы в крови в норме.')
            elif value<4 and value>=3:
                bot.send_message(message.chat.id, text='Уровень глюкозы в крови ниже рекомендованного значение, вам необходимо его компенсировать.')
            elif value < 3:
                bot.send_message(message.chat.id,
                                 text='ВАМ СРОЧНО НЕОБХОДИМО КОМПЕНСИРОВАТЬ УРОВЕНЬ ГЛЮКОЗЫ!')
            else:
                bot.send_message(message.chat.id,
                                 text='Уровень глюкозы в крови выше нормы. Примите рекомендованную вам терапию, либо проконсультируйтесь со специалистом.')
            db['results'].insert_one(data)
        except:
            bot.send_message(message.chat.id, text='Я вас не понял, попробуйте еще раз :(')
            ask_sugar(message)


if __name__ == '__main__':
     bot.polling(none_stop=True)