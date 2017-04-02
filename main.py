# - *- coding: utf- 8 - *-
import json
import connect_to_base
from bs4 import BeautifulSoup
import codecs


def login_to_the_site(login, s, school):
    r = s.get('https://schools.school.mosreg.ru/marks.aspx?school=%s&tab=period' % school)
    with open('html/test_%s.html' % login, 'wb') as output_file:
        output_file.write(r.text.encode())


def read_file(filename):
    fileobj = codecs.open(filename, "r", "utf_8_sig")
    text = fileobj.read()
    fileobj.close()
    return text


def all_marks(login):
    fresults = connect_to_base.marks_load(login)
    return fresults['marks']


def parse_user_datafile_bs(login):
    fresults = connect_to_base.marks_load(login)
    results = []
    text = read_file('html/test_%s.html' % login)
    soup = BeautifulSoup(text, "lxml")
    items1 = soup.find('table', {'id': 'journal'}).findAll('td', {'class': 's2'})
    items2 = soup.find('table', {'id': 'journal'}).findAll('td', {'class': 'tac', 'style': 'text-align:left;'})
    for item in zip(items1, items2):
        class_id = item[0].find('strong', {'class': 'u'}).text
        marks = item[1].findAll(['a', 'span'], {'class': 'mark'})
        strmarks = ''
        for mark in marks:
            if mark != '':
                strmarks = strmarks + str(mark.text) + ' '
        strmarks = strmarks.rstrip()
        results.append({
            class_id: strmarks
        })
    if fresults != 0 and fresults['marks']:
        fresults = json.loads(fresults['marks'])
        result = {}
        save_result = json.dumps(results, ensure_ascii=False)
        save_result = json.loads(save_result)
        for a, b in zip(fresults, results):
            b1 = dict(b)
            first = a.popitem()[1].split(' ')
            second = b.popitem()[1].split(' ')
            first_copy = list(first)
            third = []
            if first != second:
                for item in second:
                    if item in first:
                        first.remove(item)
                for item in first_copy:
                    if item in second:
                        second.remove(item)
                for item in first:
                    third += [item+'0']
                for item in second:
                    third += [item]
                result.update({b1.popitem()[0]: third})
        if result == {}:
            return 0
        else:
            connect_to_base.marks_save(login, json.dumps(save_result, ensure_ascii=False))
            result = json.dumps(result, ensure_ascii=False)
            return result
    else:
        connect_to_base.marks_save(login, json.dumps(results, ensure_ascii=False))
        return 0
