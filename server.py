import os
import uuid
import time

import sys
import tornado.ioloop
import tornado.web
import random
import json

from bson import ObjectId
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

class ExitHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user');
        self.redirect('/login')

class TherapyHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        user = db['users'].find_one({'_id': ObjectId(name)})
        self.render('therapy.html',gh1 = user['GH1'],gh2 = user['GH2'],gl1 = user['GL1'],gl2 = user['GL2'])
    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        user = db['users'].find_one({'_id': ObjectId(name)})
        try:
            user['GH1']=float(self.get_argument('diab_GH1'))
            user['GH2'] = float(self.get_argument('diab_GH2'))
            user['GL1'] = float(self.get_argument('diab_GL1'))
            user['GL2'] = float(self.get_argument('diab_GL2'))
            db['users'].update({'_id': ObjectId(name)}, user)
        except:
            pass
        self.render('therapy.html',gh1 = user['GH1'],gh2 = user['GH2'],gl1 = user['GL1'],gl2 = user['GL2'])

class DiagnoHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        self.render('diagno.html', error='')


class MainHandler(BaseHandler):
    def get(self):

        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        user = db['users'].find_one({'_id': ObjectId(name)})
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

        we_times = []
        we_values = []

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
            elif result['type'] == 'WE':
                we_times.append(result['time'])
                we_values.append(result['value'])
            else:
                analysis.append(result)



        self.render('dashboard.html', gl_times=json.dumps(times['gl']), gl_values=json.dumps(values['gl']),
                    ik_times=json.dumps(times['ik']), ik_values=json.dumps(values['ik']),
                    id_times=json.dumps(times['id']), id_values=json.dumps(values['id']), images=images, ctime=int(time.time()),
                    pills = pills, analisys=analysis, ad_times=ad_times, adl_values=adl_values, adh_values=adh_values,
                    gh1 = user['GH1'],gh2 = user['GH2'], we_times=we_times, we_values=we_values)


app = tornado.web.Application([
    (r"/exit", ExitHandler),
    (r"/", MainHandler),
    (r"/therapy", TherapyHandler),
    (r"/diagno", DiagnoHandler),
    (r"/login", LoginHandler),

    ('/images/(.*)', tornado.web.StaticFileHandler, {'path': 'client/images'}),
], cookie_secret="ajidfjijIJIJDIFjmkdmfkm2348fhjn", debug=True)

app.listen(5555)
tornado.ioloop.IOLoop.current().start()