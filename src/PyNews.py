#!/usr/bin/python
#-*coding:utf-8-*-

import urllib,re,sys

def search():
    url = 'http://yanjiusheng.bistu.edu.cn/web/ViewMoreNotice.aspx'

    pg = urllib.urlopen(url)
    content = pg.read()
    pg.close()

    item_re = u' target=_blank>(.+?)</a>'
    time_re = u'<span id="datetime"></span>&nbsp;&nbsp;&nbsp;&nbsp;(.+?)</span>'

    time = re.findall(time_re,content)[0]
    items = re.findall(item_re,content)
    msg = time+"\n"
    for item in items:
            msg = msg + item  + "\n"
    return msg

if __name__ == "__main__":
    print search()
