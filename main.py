# -*- encoding: utf-8 -*-
import itchat
from itchat.content import *
import json
import time
import os
import re

quns = set([
    u"KB2周三4:00-6:00（日上）",
])

admins = set([
    u"刘占亮",
    u"佐佐",
])

data_dir = "./data/"
media_dir = "./media/"

if not os.path.isdir(data_dir): os.makedirs(data_dir)
if not os.path.isdir(media_dir): os.makedirs(media_dir)

'''
TEXT    文本    文本内容
MAP    地图    位置文本
CARD    名片    推荐人字典
NOTE    通知    通知文本
SHARING    分享    分享名称
PICTURE    图片/表情    下载方法
RECORDING    语音    下载方法
ATTACHMENT    附件    下载方法
VIDEO    小视频    下载方法
FRIENDS    好友邀请    添加好友所需参数
SYSTEM    系统消息    更新内容的用户或群聊的UserName组成的列表
'''

debug = True

import sqlite3

def create_table():
    conn = sqlite3.connect('wechat.db')
    create_sql = '''create table if not exists info(
    msgtime text,
    msgtype int,
    user text,
    cnt int,
    primary key(msgtime, msgtype, user)
    );
    '''
    conn.execute(create_sql)
    conn.close()

def update(when, msgtype, user):
    line = u"[%s]发了语音@%s" % (user, when)
    print(line.encode("utf-8", "ignore"))
    conn = sqlite3.connect('wechat.db')
    s1 = '''INSERT OR IGNORE INTO info VALUES (?, ?, ?, ?);'''
    conn.execute(s1, (when, msgtype, user, 0))
    s2 = '''UPDATE info SET cnt=cnt+1 WHERE msgtime=? and msgtype=? and user=?'''
    conn.execute(s2, (when, msgtype, user))
    conn.commit()
    conn.close()

def show(when):
    print "show"
    conn = sqlite3.connect('wechat.db')
    s = '''select msgtime, user, cnt from info where msgtime=?;'''
    c = conn.cursor()
    ret = c.execute(s, (when, ))
    line = ""
    for row in ret:
        line += '|'.join([unicode(i) for i in row]) + '\n'
    conn.close()
    return line

def show2(start, end):
    print "show2"
    conn = sqlite3.connect('wechat.db')
    s = '''select user, sum(cnt) from info where msgtime>=? and msgtime<=? group by user;'''
    c = conn.cursor()
    ret = c.execute(s, (start, end,))
    print start, end
    line = ""
    for row in ret:
        line += "|".join([unicode(i) for i in row]) + '\n'
    conn.close()
    return line


create_table()


@itchat.msg_register([TEXT,])
def text_reply(msg):
    if msg["User"]["NickName"] not in admins: return
    
    if re.match(ur'\d{8,8}-\d{8,8}', msg['Text']):
        two = msg['Text'].split('-')
        info = show2(two[0], two[1])
        if info != "":
            return info
        else:
            return u"没有数据"

    if re.match(ur'\d{8,8}', msg['Text']):
        info = show(msg['Text'])
        if info != "":
            return info
        else:
            return u"没有数据"
    if msg['Text'].startswith(u"adminadd"):
        admins.add(msg['Text'][len("adminadd"):])
        return u";".join(admins)
    elif msg['Text'].startswith(u"admindel"):
        admins.remove(msg['Text'][len("admindel"):])
        return u";".join(admins)
    elif msg['Text'].startswith(u"admins"):
        return u";".join(admins)
    elif msg['Text'].startswith(u"qunadd"):
        quns.add(msg['Text'][len("qunadd"):])
        return u";".join(quns)
    elif msg['Text'].startswith(u"qundel"):
        quns.remove(msg['Text'][len("qundel"):])
        return u";".join(quns)
    elif msg['Text'].startswith(u"quns"):
        return u";".join(quns)
       

def save(msg):
    if msg["Type"] != "Recording": return
    file_name = "%s%s.json" % (data_dir, time.strftime('%Y%m%d', time.localtime()))
    out = open(file_name,'a')
    line = "%s\n" % json.dumps(msg, ensure_ascii=False)
    out.write(line.encode('utf-8'))
    out.flush()
    out.close()

    if msg["User"]["NickName"] not in quns: return
    when = time.strftime('%Y%m%d', time.localtime())
    msgtype = 1
    user = msg['ActualNickName'] if 'ActualNickName' in msg else msg['FromUserName']
    update(when, msgtype, user)

@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def qun_download_files(msg):
    if debug:
        msg['Text']("%s%s" % (media_dir, msg['FileName']))
    msg['Text'] = 'download_fn'
    msg['_type'] = 'qun';
    save(msg)

itchat.auto_login(hotReload=True)
itchat.run()
itchat.dump_login_status()
