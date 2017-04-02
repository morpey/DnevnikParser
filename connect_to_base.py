# - *- coding: utf- 8 - *-
import pymysql.cursors
import config
login_g = {}


def connect():
    connection = pymysql.connect(host=config.Mysql_ip,
                                 user=config.Mysql_login,
                                 password=config.Mysql_pass,
                                 db=config.Mysql_base,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def marks_load(login):
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT EXISTS(SELECT login FROM marks WHERE login = %s)'
            cursor.execute(sql, login)
            result = cursor.fetchone()
            if result.popitem()[1] == 1:
                sql = "SELECT marks FROM `marks` WHERE login = %s"
                cursor.execute(sql, login)
                result = cursor.fetchone()
                return result
            else:
                sql = "INSERT INTO marks (login) values (%s)"
                cursor.execute(sql, login)
                connection.commit()
                return 0
    finally:
        connection.close()


def marks_save(login, text):
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE marks SET marks = %s WHERE login = %s "
            cursor.execute(sql, [text.encode('utf8'), login])
            connection.commit()
    finally:
        connection.close()


def marks_delete(login):
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM marks WHERE login = %s"
            cursor.execute(sql, login)
            connection.commit()
    finally:
        connection.close()


def start():
    login = {}
    connection = connect()
    try:
        with connection.cursor() as cursor:
                sql = "SELECT * FROM `employees` ORDER BY chat_id ASC"
                cursor.execute(sql)
                result = cursor.fetchall()
                for item in result:
                    login[item['chat_id']] = str(item['school_id'] + ' ' + item['login'] + ' ' + item['password'])
    finally:
        connection.close()
        return login


def save(login):
    connection = connect()
    try:
        for item in login:
            with connection.cursor() as cursor:
                sql = 'SELECT EXISTS(SELECT chat_id FROM employees WHERE chat_id = %s AND login = %s AND' \
                      ' password = %s AND school_id = %s )'
                cursor.execute(sql, [item, login[item].split(' ')[1], login[item].split(' ')[2],
                                     login[item].split(' ')[0]])
                result = cursor.fetchone()
                if result.popitem()[1] == 0:
                    sql = "INSERT INTO employees (chat_id, login, password, school_id) values (%s, %s ,%s,%s)"
                    cursor.execute(sql, [item, login[item].split(' ')[1], login[item].split(' ')[2],
                                   login[item].split(' ')[0]])
                    connection.commit()
    finally:
        connection.close()


def delete(chat_id, login):
    connection = connect()
    try:
        with connection.cursor() as cursor:
                sql = "DELETE FROM employees WHERE chat_id = %s AND login = %s AND password = %s AND school_id = %s"
                cursor.execute(sql, [chat_id, login.split(' ')[1], login.split(' ')[2], login.split(' ')[0]])
                connection.commit()
    finally:
        connection.close()
