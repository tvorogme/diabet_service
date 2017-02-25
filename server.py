import os
import uuid
import time

import sys
import tornado.ioloop
import tornado.web
import random
import json
from pymongo import MongoClient

import private_config

client = MongoClient(private_config.mongo_connection)
db = client['diabetlab']

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', error='')

    def post(self):
        login = self.get_argument('login', '')
        password = self.get_argument('password', '')
        user = db['users'].find_one({'email': login, 'pass': password})
        if user != None:
            self.set_secure_cookie("user", str(user['_id']))
            self.redirect("/")
        else:
            self.render('login.html', error='Неверный пароль!')

class TherapyHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        self.render('therapy.html')
    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return
        self.render('therapy.html')

class MainHandler(BaseHandler):
    def get(self):

        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        print(name)
        results = db['results'].find({'user_id': name}).sort('time')
        times = {}
        values = {}
        times['gl']=[]
        times['ik'] = []
        times['id'] = []
        values['gl']=[]
        values['ik']=[]
        values['id'] = []
        ad_times = []
        adh_values = []
        adl_values = []

        images = []
        pills = []
        analysis = []

        for result in results[:]:
            if result['type']=='GL':
                times['gl'].append(result['time'])
                values['gl'].append(result['value'])
            elif result['type']=='IK':
                times['ik'].append(result['time'])
                values['ik'].append(result['value'])
            elif result['type']=='ID':
                times['id'].append(result['time'])
                values['id'].append(result['value'])
            elif result['type']=='FD':
                images.append(result)
            elif result['type'] == 'MD':
                pills.append(result)
            elif result['type'] == 'AD':
                ad_times.append(result['time'])
                adh_values.append(result['hvalue'])
                adl_values.append(result['lvalue'])
            else:
                analysis.append(result)



        self.render('dashboard.html', gl_times=json.dumps(times['gl']), gl_values=json.dumps(values['gl']),
                    ik_times=json.dumps(times['ik']), ik_values=json.dumps(values['ik']),
                    id_times=json.dumps(times['id']), id_values=json.dumps(values['id']), images=images, ctime=int(time.time()),
                    pills = pills, analisys=analysis, ad_times=ad_times, adl_values=adl_values, adh_values=adh_values)
        print(times)


app = tornado.web.Application([
    (r"/", MainHandler),
    (r"/therapy", TherapyHandler),
    (r"/login", LoginHandler),
    ('/images/(.*)', tornado.web.StaticFileHandler, {'path': 'client/images'}),
], cookie_secret="ajidfjijIJIJDIFjmkdmfkm2348fhjn", debug=True)

app.listen(5555)
tornado.ioloop.IOLoop.current().start()