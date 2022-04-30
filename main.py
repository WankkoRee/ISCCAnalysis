from requests import Session
import re
import json
import time

host = 'https://iscc.isclab.org.cn'
username = ""
password = ""

ss = Session()
ss.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'

ptnProfile = re.compile(r'<h1 id="team-id">(.*?)</h1>\s+<h3 class="text-center">总积分为:(\d*?),排在(\d*?)位。</h3>')


def updateUserList():
    id = (int(list(userList.keys())[-1]) if len(userList) > 0 else 0) + 1
    err_status = 0
    while True:
        ret = ss.get(f'{host}/team/{id}')
        if ret.status_code == 200:
            name, score, ranking = ptnProfile.findall(ret.text)[0]
            if name == '' and score == '':
                err_status += 1
                if err_status >= 20:
                    return True
            else:
                err_status = 0
                userList[f'{id}'] = {'name': name, 'score': 0, 'friends': {}}
                print(id, name)
        else:
            raise Exception(f'HTTP {ret.status_code}')
        id += 1
    pass


def updateQuestionList(type, valueName):
    ret = ss.get(f'{host}/{type}')
    if ret.status_code == 200:
        ret = ret.json()
        for q in ret['game']:
            if q['category'] not in valueName.keys():
                valueName[q['category']] = {}
            retret = ss.get(f'{host}/{type}/{q["id"]}')
            if retret.status_code == 200:
                retret = retret.json()
                valueName[q['category']][q['id']] = {
                    'name': retret['name'],
                    'score': retret['value'],
                    'description': retret['description'],
                    'files': retret['files'],
                    'solves': []
                }
                print(q['category'], q['id'], retret['name'])
            else:
                raise Exception(f'HTTP {retret.status_code}')
            pass
    else:
        raise Exception(f'HTTP {ret.status_code}')
    pass


def updateQuestionsolve(type, valueName):
    for category in valueName.keys():
        for id in valueName[category].keys():
            ret = ss.get(f'{host}/{type}/{id}/solves')
            if ret.status_code == 200:
                ret = ret.json()
                valueName[category][id]['solves'] = ret['teams']
                for slove in ret['teams']:
                    userList[f"{slove['id']}"]['score'] += valueName[category][id]['score']
                print(category, id, ret['teams'])
    pass


def updateChallengeList():
    updateQuestionList('chals', challengeList)


def updateChallengesolve():
    updateQuestionsolve('chal', challengeList)
    pass


def updateArenaList():
    updateQuestionList('arenas', arenaList)
    pass


def updateArenasolve():
    updateQuestionsolve('are', arenaList)
    pass


def main():
    for id in userList:
        userList[id]['score'] = 0
    updateUserList()

    assert ss.post(f'{host}/login', data={'name': username, 'password': password}, allow_redirects=False).status_code == 302

    updateChallengeList()
    updateChallengesolve()
    with open('challenge.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(challengeList, ensure_ascii=False))

    updateArenaList()
    updateArenasolve()
    with open('arena.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(arenaList, ensure_ascii=False))

    with open('user.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(userList, ensure_ascii=False))

    with open('status.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps({'updateTime': time.time()}, ensure_ascii=False))


if __name__ == '__main__':
    with open('user.json', 'r', encoding='UTF-8') as f:
        userList = json.loads(f.read(-1))
    challengeList = {}
    arenaList = {}

    main()
