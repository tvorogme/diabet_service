import json
import os
import uuid
from time import strftime, gmtime

import config
import datetime
import telebot
from telebot import types
from bson import ObjectId
from pymongo import MongoClient
import requests

from PIL import Image

client = MongoClient(config.mongo_connection)
db = client['diabetlab']

bot = telebot.TeleBot(config.token)

id_to_user = {}

temp_storage = {}
temp_food_storage = {}

color_to_rec = {}
color_to_type = {}

color_to_rec["red"]="Продукты, употребляемые в минимальном количестве или исключаемые из рациона"
color_to_rec["green"]="Продукты,употребляемые без ограничений"
color_to_rec["yellow"]="Продукты, употребляемые в умеренном количестве или по принципу \"дели пополам\""

def password(message):
   temp_storage[message.chat.id] = message.text
   msg = bot.send_message(message.chat.id, text="Введите ваш пароль от DiaFriend:")
   bot.register_next_step_handler(msg, makeLogin)

def login(id):
    '''
    user = db['users'].find_one({'chat_id': id})
    if user != None:
        return user
    '''
    if id in id_to_user.keys():
        user = db['users'].find_one({'_id': ObjectId(id_to_user[id])})
        return user
    msg = bot.send_message(id, text="Введите ваш Email от DiaFriend:")
    bot.register_next_step_handler(msg,password)
    return None

def makeLogin(message):
    log = temp_storage[message.chat.id]
    pasw = message.text
    user = db['users'].find_one({'email': str(log).lower(), 'pass': str(pasw).lower()})
    if user == None:
        bot.send_message(message.chat.id, text='К сожалению, данные неверны. Попробуйте еще раз!')
        login(message.chat.id)
    else:
        #user['chat_id'] = message.chat.id
        #db['users'].update({'_id': user['_id']}, user)
        id_to_user[message.chat.id]=str(user['_id'])
        bot.send_message(message.chat.id, user['name']+', здравствуйте!')

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message.chat.id not in temp_food_storage.keys():
        return
    if 'file' not in temp_food_storage[call.message.chat.id].keys():
        bot.send_message(call.message.chat.id, "Пожалуйста, загрузите фотографию еще раз.")
        return
    if call.message:
        user = login(call.message.chat.id)
        if str(call.data).find('weight')==-1:
            temp_food_storage[call.message.chat.id]["food"] = call.data
            if call.data == "none":
                foodNotFoundHandler(call.message)
            else:
                with open(os.path.dirname(os.path.realpath(__file__)) + '/food.json', 'r') as file:
                    cls = json.loads(file.read())
                    food = cls[call.data]
                    temp_food_storage[call.message.chat.id]["name"] = food["name"]
                    message1 = "Спасибо! На 100 грамм данного блюда белков - {0} г, жиров - {1} г, углеводов - {2} г, {3} Ккал, {4} - ХЕ. Данный продукт относится к категории \"{5}\".".format(food["prot"],food["fat"],food["ugl"], food["cals"], food["xe"], color_to_rec[food["color"]])
                    bot.send_message(call.message.chat.id, message1)
                    showWeight(call.message)
                    #msg = bot.send_message(call.message.chat.id, message2)
                    #bot.register_next_step_handler(msg, foodWeightHandler)
        else:
            if call.data == "weight_none":
                askWeight(call.message)
            else:
                weight = str(call.data)[6:]
                saveFood(call.message.chat.id, weight)


def foodWeightHandler(message):
    if message.chat.id not in temp_food_storage.keys():
        return
    saveFood(message.chat.id, message.text)


def saveFood(id, weight):
    if id not in temp_food_storage.keys():
        return
    user = login(id)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {'type': 'FD', 'filename': temp_food_storage[id]['file'], 'user_id': str(user['_id']),
            'otime': datetime.datetime.now(),
            'time': current_time, 'food': temp_food_storage[id]["food"],'weight': weight,'text': temp_food_storage[id]["name"]}
    bot.send_message(id, "Спасибо! Я записал это в дневник питания.")
    db['results'].insert_one(data)
    temp_food_storage[id] = {}

#просит ввести название еды
def foodNotFoundHandler(message):
    if message.chat.id not in temp_food_storage.keys():
        return
    temp_food_storage[message.chat.id]["food"] = "none"
    #bot.send_message(message.chat.id, "К сожалению, я не нашел описание данного продукта в моей базе, но я обязательно уточню его у моих создателей!")
    msg = bot.send_message(message.chat.id,
                     "Вы не могли бы подсказать, что это?")
    bot.register_next_step_handler(msg, newFoodHandler)

#показать варианты весов
def showWeight(message):
    keyboard = types.InlineKeyboardMarkup()
    weights = ["10","25", "50", "100", "150", "200"]
    for weight in weights:
        callback_button = types.InlineKeyboardButton(text=weight+"г", callback_data="weight"+weight)
        keyboard.add(callback_button)
    callback_button = types.InlineKeyboardButton(text="Другой", callback_data="weight_none")
    keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Спасибо! А сколько оно примерно весит?", reply_markup=keyboard)


#показать варианты весов
def askWeight(message):
    msg = bot.send_message(message.chat.id, "Укажите вес в граммах:")
    bot.register_next_step_handler(msg, foodWeightHandler)

#сохраняет введенное вручную название еду
def newFoodHandler(message):
    if message.chat.id not in temp_food_storage.keys():
        return
    temp_food_storage[message.chat.id]["name"]=message.text
    showWeight(message)

@bot.message_handler(content_types=['photo'])
def photo(message):
    user = login(message.chat.id)
    if user != None:
        file_id = message.photo[-1].file_id
        path = bot.get_file(file_id)
        extn = '.'+str(path.file_path).split('.')[-1]
        downloaded_file = bot.download_file(path.file_path)
        cname = str(uuid.uuid4()) + extn
        with open(os.path.dirname(os.path.realpath(__file__)) +'/../images/'+cname, 'wb') as new_file:
            new_file.write(downloaded_file)
        im = Image.open(os.path.dirname(os.path.realpath(__file__)) + '/../images/' + cname);
        im.thumbnail((300, 300), Image.ANTIALIAS)
        im.save(os.path.dirname(os.path.realpath(__file__)) + '/../images/' + cname)
        try:
            tvorog = requests.get('http://74.117.183.182:8081/?url=http://roctbb.net:5555/images/' + cname)
            food = json.loads(tvorog.text)
            with open(os.path.dirname(os.path.realpath(__file__)) + '/food.json', 'r') as file:
                cls = json.loads(file.read())
                keyboard = types.InlineKeyboardMarkup()
                for var in food:
                    callback_button = types.InlineKeyboardButton(text=cls[var]['name'], callback_data=var)
                    keyboard.add(callback_button)
                callback_button = types.InlineKeyboardButton("Другое", callback_data="none")
                keyboard.add(callback_button)
                bot.send_message(message.chat.id,
                                 "Выберите продукт из списка ниже или кнопку \"Другое\", если я не отгадал. ", reply_markup=keyboard)

        except Exception as e:
            foodNotFoundHandler(message)
        temp_food_storage[message.chat.id]={}
        temp_food_storage[message.chat.id]["file"] = cname
        #current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        #data = {'type': 'FD', 'filename': cname, 'user_id': str(user['_id']), 'time': current_time, 'text': food}
        #bot.send_message(message.chat.id, "Я записал это в дневник питания. Я думаю, что это - "+food)
        #db['results'].insert_one(data)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    if message.chat.id in id_to_user.keys():
        user = db['users'].find_one({'_id': ObjectId(id_to_user[message.chat.id])})
    else:
        user = None
    if user != None:
        bot.send_message(message.chat.id, 'Рад вас видеть, ' + user['name'] + '! Сообщайте мне ваш уровень сахара и присылайте фото еды - я помогу вам вести удобный дневник самоконтрля и питания. Если возникнет вопрос - всегда на связи.')
    else:
        bot.send_message(message.chat.id,text='Здравствуйте! Меня зовут Бот DiaFriend, я помогу вам просто вести дневник самоконтроля и питания, а также буду всегда на связи, если у вас появится вопрос.')
        login(message.chat.id)

@bot.message_handler(commands=['sugar'])
def ask_sugar(message):
    user = login(message.chat.id)
    if user != None:
        msg = bot.send_message(message.chat.id, text='Какой у вас сейчас уровень сахара?')
        bot.register_next_step_handler(msg, save_sugar)

def processSugar(message, value, user):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {'type': 'GL', 'value': float(value), 'user_id': str(user['_id']), 'time': current_time, 'otime': datetime.datetime.now()}
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
    if message.chat.id in temp_food_storage.keys() and 'file' in temp_food_storage[message.chat.id]:
        return
    if message.chat.id not in id_to_user.keys():
        return
    user = db['users'].find_one({'_id': ObjectId(id_to_user[message.chat.id])})
    if user != None:
        text = str(message.text)
        if text.lower().find('допустимый')!=-1:
            bot.send_message(message.chat.id, "Ваш допустимый уровень глюкозы в крови от "+str(user['GH1'])+" до "+str(user['GH2']))
            return
        if text.lower().find('целевой')!=-1 or text.find('рекомендуемый')!=-1 :
            bot.send_message(message.chat.id, "Ваш допустимый уровень глюкозы в крови от "+str(user['GL1'])+" до "+str(user['GL2']))
            return
        try:
            value = float(message.text.replace(',', '.'))
            processSugar(message, value, user)
        except:
            try:
                r = requests.post('http://185.106.141.196:9000/ask', data={'question': message.text})
                bot.send_message(message.chat.id, r.text)
            except:
                bot.send_message(message.chat.id, "Простите, я вас не понял.")







if __name__ == '__main__':
     bot.polling(none_stop=True)