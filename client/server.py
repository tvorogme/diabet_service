import os
import uuid

import tornado.ioloop
import tornado.web
import random
from pymongo import MongoClient
import private_config

client = MongoClient(private_config.mongo_connection)
db = client['diabetlab']

from time import gmtime, strftime

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', error='')
    def post(self):
        login = self.get_argument('login', '')
        password = self.get_argument('password', '')
        user = db['users'].find_one({'email': login, 'pass':password})
        if user != None:
            self.set_secure_cookie("user", str(user['_id']))
            self.redirect("/")
        else:
            self.render('login.html', error='Неверный пароль!')

def get_status_and_message_for_gl(value):
    ok = True
    text='Уровень глюкозы в крови в норме.'
    if value > 5.5:
        ok = False
        text = 'Уровень глюкозы в крови выше нормы. Примите рекомендованную вам терапию, либо проконсультируйтесь со специалистом.'
    elif value<4 and value>=3:
        ok = False
        text='Уровень глюкозы в крови ниже рекомендованного значение, вам необходимо его компенсировать.'
    elif value < 3:
        ok = False
        text='ВАМ СРОЧНО НЕОБХОДИМО КОМПЕНСИРОВАТЬ УРОВЕНЬ ГЛЮКОЗЫ!'
    print(ok, text)
    return (ok, text)

class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.render('client.html', message='', error='')
    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        type = self.get_argument('type')
        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        try:
            if type=='IK':
                value = str(self.get_argument('value')).replace(',','.')
                medicine = self.get_argument('medicine')
                data = {'type': 'IK', 'value':float(value), 'medicine':medicine, 'user_id': name, 'time': current_time}
            if type=='ID':
                value = str(self.get_argument('value')).replace(',','.')
                medicine = self.get_argument('medicine')
                data = {'type': 'ID', 'value':float(value), 'medicine':medicine, 'user_id': name, 'time': current_time}
            if type=='MD':
                value = str(self.get_argument('value')).replace(',','.')
                medicine = self.get_argument('medicine')
                data = {'type': 'MD', 'value':float(value), 'medicine':medicine, 'user_id': name, 'time': current_time}
            if type=='GL':
                value = str(self.get_argument('value')).replace(',','.')
                data = {'type': 'GL', 'value':float(value), 'user_id': name, 'time': current_time}
            if type=='FD':
                fileinfo = self.request.files['photo'][0]
                fname = fileinfo['filename']
                extn = os.path.splitext(fname)[1]
                if extn!='.png' and extn!='.jpg' and extn!='.jpeg':
                    raise "error file type"
                cname = str(uuid.uuid4()) + extn
                fh = open('images/' + cname, 'wb')
                fh.write(fileinfo['body'])
                data = {'type': 'FD', 'filename': cname, 'user_id': name, 'time': current_time}
            if type=='GG':
                value = str(self.get_argument('value')).replace(',', '.')
                data = {'type': 'GG', 'value': float(value), 'user_id': name, 'time': current_time}
            if type=='LC':
                ah_value = float(str(self.get_argument('ah_value')).replace(',', '.'))
                lpn_value = float(str(self.get_argument('lpn_value')).replace(',', '.'))
                lvn_value = float(str(self.get_argument('lvn_value')).replace(',', '.'))
                tg_value = float(str(self.get_argument('tg_value')).replace(',', '.'))

                data = {'type': 'AH', 'value': float(ah_value), 'user_id': name, 'time': current_time}
                db['results'].insert_one(data)
                data = {'type': 'LPN', 'value': float(lpn_value), 'user_id': name, 'time': current_time}
                db['results'].insert_one(data)
                data = {'type': 'LVN', 'value': float(lvn_value), 'user_id': name, 'time': current_time}
                db['results'].insert_one(data)
                data = {'type': 'TG', 'value': float(tg_value), 'user_id': name, 'time': current_time}
            if type=='AD':
                lvalue = str(self.get_argument('lvalue')).replace(',', '.')
                hvalue = str(self.get_argument('hvalue')).replace(',', '.')
                data = {'type': 'GLH', 'value': float(hvalue), 'user_id': name, 'time': current_time}
                db['results'].insert_one(data)
                data = {'type': 'GLL', 'value': float(lvalue), 'user_id': name, 'time': current_time}



            db['results'].insert_one(data)

            message = 'Данные сохранены! '
            is_ok = True
            if type=='GL': # если юзер заполнил глюкозу
                value = str(self.get_argument('value')).replace(',','.')
                is_ok, status_message = get_status_and_message_for_gl(float(value))
                message += status_message
            self.render('client.html', message_ok=is_ok, message=message, error='')
        except:
            self.render('client.html', message='', error='Проверьте правильность данных!')
app = tornado.web.Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),

], cookie_secret="ajidfjijIJIJDIFjmkdmfkm2348fhjn", debug=True)

app.listen(7777)
tornado.ioloop.IOLoop.current().start()