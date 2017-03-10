import datetime
import os
import uuid
import time

import sys

import requests
import tornado.ioloop
import tornado.web
import random
import json

from PIL import Image
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

class EventsHandler(BaseHandler):
    def get(self):
        colors = {'GL': '#7B2EC1', 'FD': '#7EBF28','ID': '#7CADD8','AD': '#116CC1','DS': '#C14C1B','GG': '#C14C1B'}
        start = self.get_argument('start')
        end = self.get_argument('end')
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        if not self.current_user:
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        events = db['events'].find({'user': name, 'time': {'$gte': start_date, '$lt': end_date}}).sort('time');
        ready_events = []
        for event in events:
            ready_event = {
                'title': event['title'],
                'start': event['time'].strftime("%Y-%m-%dT%H:%M:%S"),
                'end': (event['time']+datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
                'allDay': False,
                'backgroundColor': colors[event['type']],
                'color': 'white'
            }
            ready_events.append(ready_event)
        self.write(json.dumps(ready_events))


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


class StatsHandler(BaseHandler):
    def get(self):

        if not self.current_user:
            self.redirect("/login")
            return

        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)

        name = tornado.escape.xhtml_escape(self.current_user)
        user = db['users'].find_one({'_id': ObjectId(name)})
        results = db['results'].find({'user_id': name, "otime": {'$gte': start, '$lt': end}}).sort('time')
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

        start+=datetime.timedelta(days=1)
        end += datetime.timedelta(days=1)

        self.render('dashboard.html', gl_times=json.dumps(times['gl']), gl_values=json.dumps(values['gl']),
                    ik_times=json.dumps(times['ik']), ik_values=json.dumps(values['ik']),
                    id_times=json.dumps(times['id']), id_values=json.dumps(values['id']), images=images, ctime=int(time.time()),
                    pills = pills, analisys=analysis, ad_times=ad_times, adl_values=adl_values, adh_values=adh_values,
                    gh1 = user['GH1'],gh2 = user['GH2'], we_times=we_times, we_values=we_values, start_date = start.strftime("%Y-%m-%d %H:%M:%S"), end_date = end.strftime("%Y-%m-%d %H:%M:%S"),)

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
    return (ok, text)

class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.render('client.html', message='', error='', today=datetime.date.today().strftime('%Y-%m-%d'))
    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        type = self.get_argument('type')
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
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
                extn = os.path.splitext(fname)[1].lower()
                if extn!='.png' and extn!='.jpg' and extn!='.jpeg':
                    raise Exception("error file type")
                cname = str(uuid.uuid4()) + extn
                fh = open(os.path.dirname(os.path.realpath(__file__))+'/images/' + cname, 'wb')
                fh.write(fileinfo['body'])
                im = Image.open(os.path.dirname(os.path.realpath(__file__))+'/images/'+cname);
                im.thumbnail((300,300), Image.ANTIALIAS)
                im.save(os.path.dirname(os.path.realpath(__file__))+'/images/'+cname)
                food = ''
                try:
                    tvorog = requests.get('http://185.106.141.196:9991/roctbb?url=http://roctbb.net:5555/images/'+cname)
                    food = tvorog.text
                except:
                    pass
                data = {'type': 'FD', 'filename': cname, 'user_id': name, 'time': current_time, 'text': food}
            if type=='GG':
                value = str(self.get_argument('value')).replace(',', '.')
                data = {'type': 'GG', 'value': float(value), 'user_id': name, 'time': current_time, 'name': 'Гликированный гемоглобин'}
            if type == 'GG':
                value = str(self.get_argument('value')).replace(',', '.')
                data = {'type': 'WE', 'value': float(value), 'user_id': name, 'time': current_time,
                        'name': 'Вес'}
            if type=='LC':
                ah_value = float(str(self.get_argument('ah_value')).replace(',', '.'))
                lpn_value = float(str(self.get_argument('lpn_value')).replace(',', '.'))
                lvn_value = float(str(self.get_argument('lvn_value')).replace(',', '.'))
                tg_value = float(str(self.get_argument('tg_value')).replace(',', '.'))

                data = {'type': 'AH', 'value': float(ah_value), 'user_id': name, 'time': current_time, 'name': 'Общий холестерин'}
                db['results'].insert_one(data)
                data = {'type': 'LPN', 'value': float(lpn_value), 'user_id': name, 'time': current_time, 'name': 'ЛПН'}
                db['results'].insert_one(data)
                data = {'type': 'LVN', 'value': float(lvn_value), 'user_id': name, 'time': current_time, 'name': 'ЛВН'}
                db['results'].insert_one(data)
                data = {'type': 'TG', 'value': float(tg_value), 'user_id': name, 'time': current_time, 'name': 'Триглицериды'}
            if type=='AD':
                lvalue = str(self.get_argument('lvalue')).replace(',', '.')
                hvalue = str(self.get_argument('hvalue')).replace(',', '.')
                data = {'type': 'AD', 'lvalue': float(lvalue),'hvalue': float(hvalue),'user_id': name, 'time': current_time}

            db['results'].insert_one(data)

            message = 'Данные сохранены! '
            is_ok = True
            if type=='GL': # если юзер заполнил глюкозу
                value = str(self.get_argument('value')).replace(',','.')
                is_ok, status_message = get_status_and_message_for_gl(float(value))
                message += status_message
            self.render('client.html', message_ok=is_ok, message=message, error='')
        except Exception as e:
            print(e)
            self.render('client.html', message='', error='Проверьте правильность данных!')

app = tornado.web.Application([
    (r"/exit", ExitHandler),
    (r"/", MainHandler),
    (r"/stats", StatsHandler),
    (r"/therapy", TherapyHandler),
    (r"/diagno", DiagnoHandler),
    (r"/login", LoginHandler),
    (r"/events", EventsHandler),

    ('/images/(.*)', tornado.web.StaticFileHandler, {'path': 'client/images'}),
], cookie_secret="ajidfjijIJIJDIFjmkdmfkm2348fhjn", debug=True)

app.listen(5555)
tornado.ioloop.IOLoop.current().start()