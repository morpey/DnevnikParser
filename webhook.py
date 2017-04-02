#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
import cherrypy
import config
import telebot
import main
import time
import datetime
import threading
import json
import requests
import codecs
import logging
import connect_to_base
from bs4 import BeautifulSoup
delay = config.delay
check = {}
captcha = {}
login_g = {}
session = {}
print('Thank you for start the bot, Bitch')

WEBHOOK_HOST = config.ip
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % config.token

bot = telebot.TeleBot(config.token)


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


def check_the_school(message):
    global login_g, session
    r = session[str(message)].get('https://schools.school.mosreg.ru/school.aspx')
    text = r.text.encode()
    soup = BeautifulSoup(text, "lxml")
    items1 = soup.find('a', {'class': 'avatar'}).get('href')
    login_g[str(message)] = items1.split('=')[1]


def messages(message, login):
    global session
    if type(message) == telebot.types.Message:
        message = message.chat.id
    try:
        time.sleep(0.01)
        main.login_to_the_site(login, session[message], login_g[str(message)].split(' ')[0])
    except KeyError:
        return 0
    result = main.parse_user_datafile_bs(login)
    mess = ''
    if result != 0:
        result = json.loads(result).items()
        for item in result:
            class_id = item[0]
            mark = item[1]
            marks_a = ''
            marks_b = ''
            for item1 in mark:
                if item1.find('0') != -1:
                    for word in item1:
                        if (word.isdigit() and word != '0') or (word == 'Б') or (word == 'П') or (word == 'Н')\
                                or (word == '-'):
                            if word == '-':
                                marks_a = marks_a.rstrip()
                                marks_a += str(word) + ' '
                            else:
                                marks_a += str(word) + ' '
                else:
                    marks_b += str(item1) + ' '
            if marks_a != '':
                mess += 'Убрана оценка по ' + class_id + ' : ' + marks_a + '\n'
            if marks_b != '':
                mess += 'Новая оценка по ' + class_id + ' : ' + marks_b + '\n'

        return mess
    else:
        return 0


def do_something(message, login):
    global login_g, check
    try:
        if not check[message]:
            return
    except KeyError:
        pass
    try:
        time.sleep(0.01)
        soobshenie = messages(message, login)
    except TypeError as e:
        print(datetime.datetime.now().strftime('%d.%m.%Y %H:%M') + ' Ебучие ошибки ' + login_g[message].split(' ')[1])
        url = 'https://login.school.mosreg.ru/user/login'
        session[message] = requests.Session()
        session[message].post(url, data={'login': login_g[message].split(' ')[1],
                                         'password': login_g[message].split(' ')[2]})
        print(e)
    except AttributeError as e:
        print(datetime.datetime.now().strftime('%d.%m.%Y %H:%M') + ' Ебучие ошибки ' + login_g[message].split(' ')[1])
        url = 'https://login.school.mosreg.ru/user/login'
        session[message] = requests.Session()
        r = session[message].post(url, data={'login': login_g[message].split(' ')[1],
                                             'password': login_g[message].split(' ')[2]})
        bot.send_photo(message, json.loads(r.text)['captchaUrl'])
        check[message] = False
        captcha[message] = {json.loads(r.text)['captchaCode']: ''}
        print(e)
    except Exception as e:
        logging.exception(e)
        url = 'https://login.school.mosreg.ru/user/login'
        session[message] = requests.Session()
        session[message].post(url, data={'login': login_g[message].split(' ')[1],
                                         'password': login_g[message].split(' ')[2]})
        soobshenie = messages(message, login)
        if soobshenie != 0:
            bot.send_message(message, soobshenie)
        else:
            if soobshenie != 0:
                bot.send_message(message, soobshenie)
    else:
        if soobshenie != 0:
            bot.send_message(message, soobshenie)
        else:
            if soobshenie != 0:
                bot.send_message(message, soobshenie)


def start_timer(message, login):
    global check
    while check[message]:
        time.sleep(delay)
        thread = threading.Thread(target=do_something, name='t%s' % message, kwargs={'message': message,
                                                                                     'login': login})
        thread.start()


@bot.message_handler(regexp="^[0-9]+$")
def captcha_check(message):
    global captcha, check, session, login_g
    try:
        cap = captcha[str(message.chat.id)].popitem()
        if cap[1] == '':
            url = 'https://login.school.mosreg.ru/user/login'
            session[str(message.chat.id)] = requests.Session()
            r = session[str(message.chat.id)].post(url, data={
                'login': login_g[str(message.chat.id)].split(' ')[1],
                'password': login_g[str(message.chat.id)].split(' ')[2],
                'captchaCode': cap[0], 'captcha': message.text})
            if json.loads(r.text).get('returnUrl'):
                check[str(message.chat.id)] = True
                bot.send_message(message.chat.id, 'Ввод верный')
                start_timer(str(message.chat.id), login_g[str(message.chat.id)].split(' ')[1])
            else:
                print(json.loads(r.text))
        elif cap[1] != '':
            url = 'https://login.school.mosreg.ru/user/login'
            session[str(message.chat.id)] = requests.Session()
            r = session[str(message.chat.id)].post(url, data={'login': cap[1].split(' ')[0],
                                                              'password': cap[1].split(' ')[1],
                                                              'captchaCode': cap[0], 'captcha': message.text})
            if json.loads(r.text).get('returnUrl'):
                check_the_school(message.chat.id)
                print('New user ' + cap[1].split(' ')[0])
                check[message.chat.id] = True
                login_g[str(message.chat.id)] += ' ' + cap[1].split(' ')[0] + ' ' + cap[1].split(' ')[1]
                connect_to_base.save(login_g)
                print_all(message.chat.id)
                bot.send_message(message.chat.id, 'Начало проверки')
                start_timer(message.chat.id, cap[1].split(' ')[0])
            else:
                print(json.loads(r.text))
    except Exception as e:
        logging.exception(e)


@bot.message_handler(regexp="all")
def print_all(id_our):
    global login_g
    if type(id_our) == telebot.types.Message:
        id_our = str(id_our.chat.id)
    if str(id_our) in login_g:
        res = json.loads(main.all_marks(login_g[str(id_our)].split(' ')[1]))
        result = ''
        for a in res:
            item1 = a.popitem()
            result += (item1[0] + ' ' + item1[1]) + '\n'
        bot.send_message(id_our, result)
    else:
        bot.send_message(id_our, 'Войдите, прежде чем получите список оценок')


@bot.message_handler(regexp="(?i)^start [a-zA-Z0-9.]+ [a-zA-Z0-9]+$")
def handle_message(message):
    global login_g, check, session, captcha
    if str(message.chat.id) in login_g:
        stop_message(message)
    message_copy = str(message.text).split(' ')
    url = 'https://login.school.mosreg.ru/user/login'
    try:
        session[str(message.chat.id)] = requests.Session()
        session[str(message.chat.id)].post(url, data={'login': message_copy[1], 'password': message_copy[2]})
        check_the_school(message.chat.id)
        do_something(str(message.chat.id), message_copy[1])
    except TypeError as e:
        print('Wrong Pass ' + message_copy[1])
        bot.send_message(message.chat.id, 'Неверный логин или пароль')
        print(e)
    except AttributeError as e:
        print('Wrong Pass ' + message_copy[1])
        r = session[str(message.chat.id)].post(url, data={'login': message_copy[1], 'password': message_copy[2]})
        bot.send_photo(str(message.chat.id), json.loads(r.text)['captchaUrl'])
        check[str(message.chat.id)] = False
        captcha[str(message.chat.id)] = {json.loads(r.text)['captchaCode']: message_copy[1] + ' ' + message_copy[2]}
        print(e)
    else:
        print('New user ' + message_copy[1])
        check[message.chat.id] = True
        login_g[str(message.chat.id)] += ' ' + message_copy[1] + ' ' + message_copy[2]
        connect_to_base.save(login_g)
        print_all(message.chat.id)
        bot.send_message(message.chat.id, 'Начало проверки')
        p1 = threading.Thread(target=start_timer, name='tp%s' % message.chat.id, kwargs={
            "message": message.chat.id,
            "login": message_copy[1]})
        p1.start()


def read_file(filename):
    fileobj = codecs.open(filename, "r", "utf_8_sig")
    text = fileobj.read()
    fileobj.close()
    return text


@bot.message_handler(regexp="stop")
def stop_message(message):
    global check, login_g
    print("Stop " + login_g[str(message.chat.id)].split(' ')[1])
    bot.send_message(message.chat.id, 'Остановка проверки')
    check[message.chat.id] = False
    connect_to_base.delete(message.chat.id, login_g[str(message.chat.id)])
    connect_to_base.marks_delete(login_g[str(message.chat.id)].split(' ')[1])
    login_g.pop(str(message.chat.id))


def start():
    global login_g
    login_g = connect_to_base.start()
    for item in login_g:
        print('New user ' + login_g[item].split(' ')[1])
        check[item] = True
        url = 'https://login.school.mosreg.ru/user/login'
        time.sleep(0.01)
        session[item] = requests.Session()
        session[item].post(url, data={'login': login_g[item].split(' ')[1], 'password': login_g[item].split(' ')[2]})
        p1 = threading.Thread(target=start_timer, name='tp%s' % item, kwargs={
            "message": item,
            "login": login_g[item].split(' ')[1]})
        p1.start()


bot.remove_webhook()

# Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})
start()
# Собственно, запуск!
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
