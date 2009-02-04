#!/usr/bin/env python
#encoding=utf-8
#Using GPL v2
#Author: cocobear.cn@gmail.com

import urllib2,urllib,cookielib,httplib
import sys,re

user = "cocobear.cn@gmail.com"
passwd = "password"

def tag2html(name,url,description):
    global user
    file_name = user+".html"
    f = open(file_name,"a")
    f.write("\t<DT><A HREF=\""+url+"\">"+name+"</A>\n")
    if description:
        f.write("\t<DD>"+description+"</DD>\n")
    f.close()

def login(opener):
    global user,passwd
    url = "http://www.zhuaxia.com/passport/logon_check?/\sourceid=undefined&customerId=-1"
    body = (("email",user),("password",passwd),("persistentCookie","false"))
    ret = opener.open(url,urllib.urlencode(body)).read()
    print ret.strip("\n\r")

    if int(ret) != 1:
        print "Login error!"
        return -1
    pg_num = 0
    base_url = "http://www.zhuaxia.com/ajaxMyTagCoreFetcher.php?tag_id=-1&pg_sz=50&pg_num=%d&desc_status=0&show_type=0&logId=24&sourceid=0"
    url= base_url % pg_num

    ret = opener.open(url)
    data = ret.read()
    nums_re = '中共有<b>(\d+)</b>篇'
    nums = int(re.search(nums_re,data).group(1))
    for pg_num in range(1,nums/50+1):
        print pg_num
        url = base_url % pg_num
        ret = opener.open(url)
        data += ret.read()
    """
    f = open('url.htm','w')
    f.write(data)
    f.close()
    """
    url_re = '查看原文：(.*)" href=.* target="_blank">(.*)</a>'
    urls = re.findall(url_re,data)
    for i in urls:
        tag2html(i[1],i[0],None)

def init():
    httplib.HTTPConnection.debuglevel  =  1 
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

    exheaders = [("User-Agent","Opera/9.27 (X11; Linux x86_64; U; en)"),("Connection","Keep-Alive"),("Referer","http://www.zhuaxia.com"),("Accept","text/html, application/xml;q=0.9, application/xhtml+xml, */*;q=0.1"),("Accept-Charset","iso-8859-1, utf-8, utf-16, *;q=0.1"),("Cookie2","$Version=1"),]

    opener.addheaders = exheaders
    urllib2.install_opener(opener)
    return opener
    
def main(argv=None):
    global user,tag
    
    opener=init()
    if login(opener) == 1:
        return -1

if __name__ == "__main__":
    sys.exit(main())
