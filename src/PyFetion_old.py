#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIT License
#By : cocobear.cn@gmail.com
#Ver:0.2

import urllib
import urllib2
import sys,re
import binascii
import hashlib
import socket
import os
import time
import exceptions
import logging

from hashlib import md5
from hashlib import sha1
from uuid import uuid1
from threading import RLock
from threading import Thread
from select import select
from Queue import Queue
from copy import copy


FetionOnline = "400"
FetionBusy   = "600"
FetionAway   = "100"
FetionHidden  = "0"
FetionOffline = "365"

FetionVer = "2008"
#"SIPP" USED IN HTTP CONNECTION
FetionSIPP= "SIPP"
FetionNavURL = "nav.fetion.com.cn"
FetionConfigURL = "http://nav.fetion.com.cn/nav/getsystemconfig.aspx"


FetionConfigXML = """<config><user mobile-no="%s" /><client type="PC" version="3.5.2540" platform="W6.1" /><servers version="0" /><service-no version="0" /><parameters version="0" /><hints version="0" /><http-applications version="0" /><client-config version="0" /><services version="0" /></config>"""

FetionLoginXML = """<args><device type="PC" version="1" client-version="3.5.2540" /><caps value="simple-im;im-session;temp-group;personal-group;im-relay;xeno-im;direct-sms;sms2fetion" /><events value="contact;permission;system-message;personal-group;compact" /><user-info attributes="all" /><presence><basic value="%s" desc="" /></presence></args>"""

proxy_info = False
d_print = ''
#uncomment below line if you need proxy
"""
proxy_info = {'user' : '',
              'pass' : '',
              'host' : '218.249.83.87',
              'port' : 8080 
              }
"""

class PyFetionException(Exception):
    """Base class for all exceptions
    """
    def __init__(self, code, msg):
        self.args = (code,msg)

class PyFetionSocketError(PyFetionException):
    """any socket error"""
    def __init__(self,e,msg=''):
        if msg:
            self.args = (e,msg)
            self.code = e
            self.msg  = msg
        elif type(e) is int:
            self.args = (e,socket.errorTab[e])
            self.code = e
            self.msg  = socket.errorTab[e]

        else:
            args = e.args
            d_print(('args',),locals())
            try:
                self.args = (e.errno,msg)
                msg = socket.errorTab[e.errno]
                self.code = e.errno
            except:
                msg = e
            self.msg  = msg

class PyFetionAuthError(PyFetionException):
    """Authentication error.
    Your password error.
    """

class PyFetionSupportError(PyFetionException):
    """Support error.
    Your phone number don't support fetion.
    """

class PyFetionRegisterError(PyFetionException):
    """RegisterError.
    """
class SIPC():

    global FetionVer
    global FetionSIPP
    global FetionLoginXML

    _header = ''
    #body = ''
    _content = ''
    code = ''
    ver  = "SIP-C/2.0"
    Q   = 1
    I   = 1
    queue = Queue()

    def __init__(self,args=[]):
        self.__seq = 1

        if args:
            [self.sid, self._domain,self.login_type, self._http_tunnel,\
             self._ssic, self._sipc_proxy, self.presence, self._lock] = args
        if self.login_type == "HTTP":
            guid = str(uuid1())
            self.__exheaders = {
                 'Cookie':'ssic=%s' % self._ssic,
                 'Content-Type':'application/oct-stream',
                 'Pragma':'xz4BBcV%s' % guid,
                 }
        else:
            self.__tcp_init()
     
    def init_ack(self,type):
        self._content = "%s 200 OK\r\n" % self.ver
        self._header = [('F',self.sid),
                       ('I',self.I),
                       ('Q','%s %s' % (self.Q,type)),
                      ]

    def init(self,type):
        self._content = '%s %s %s\r\n' % (type,self._domain,self.ver)
        self._header = [('F',self.sid),
                       ('I',self.I),
                       ('Q','%s %s' % (self.Q,type)),
                      ]

 
    def recv(self,timeout=False):
        if self.login_type == "HTTP":
            time.sleep(10)
            return self.get_offline_msg()
            pass
        else:
            if timeout:
                infd,outfd,errfd = select([self.__sock,],[],[],timeout)
            else:
                infd,outfd,errfd = select([self.__sock,],[],[])
                
            if len(infd) != 0:
                ret = self.__tcp_recv()
                    
                num = len(ret)
                d_print(('num',),locals())
                if num == 0:
                    return ret
                if num == 1:
                    return ret[0]
                for r in ret:
                    self.queue.put(r)
                    d_print(('r',),locals())
                    
                if not self.queue.empty():
                    return self.queue.get()

            else:
                return "TimeOut"

    def get_code(self,response):
        cmd = ''
        try:
            self.code =int(re.search("%s (\d{3})" % self.ver,response).group(1))
            self.msg  =re.search("%s \d{3} (.*)\r" % self.ver,response).group(1)
        except AttributeError,e:
            try:
                cmd = re.search("(.+?) %s" % self.ver,response).group(1)
                d_print(('cmd',),locals())
            except AttributeError,e:
                pass
                
            return cmd
        return self.code
 
    def get(self,cmd,arg,*extra):
        body = ''
        if extra:
            body = extra[0]
        if cmd == "REG":
            body = FetionLoginXML % self.presence
            self.init('R')
            if arg == 1:
                pass
            if arg == 2:
                nonce = re.search('nonce="(.*)"',extra[0]).group(1)
                cnonce = self.__get_cnonce()
                if FetionVer == "2008":
                    response=self.__get_response_sha1(nonce,cnonce)
                elif FetionVer == "2006":
                    response=self.__get_response_md5(nonce,cnonce)
                salt = self.__get_salt()
                d_print(('nonce','cnonce','response','salt'),locals())
                #If this step failed try to uncomment this lines
                #del self._header[2]
                #self._header.insert(2,('Q','2 R'))
                
                if FetionVer == "2008":
                    self._header.insert(3,('A','Digest algorithm="SHA1-sess",response="%s",cnonce="%s",salt="%s",ssic="%s"' % (response,cnonce,salt,self._ssic)))
                elif FetionVer == "2006":
                    self._header.insert(3,('A','Digest response="%s",cnonce="%s"' % (response,cnonce)))
            #If register successful 200 code get 
            if arg == 3:
                return self.code

        if cmd == "CatMsg":
            self.init('M')
            self._header.append(('T',arg))
            self._header.append(('C','text/plain'))
            self._header.append(('K','SaveHistory'))
            self._header.append(('N',cmd))
        
        if cmd == "SendMsg":
            self.init('M')
            self._header.append(('C','text/plain'))
            self._header.append(('K','SaveHistory'))

        if cmd == "SendSMS":
            self.init('M')
            self._header.append(('T',arg))
            self._header.append(('N',cmd))

        if cmd == "SendCatSMS":
            self.init('M')
            self._header.append(('T',arg))
            self._header.append(('N',cmd))

        if cmd == "NUDGE":
            self.init('IN')
            self._header.append(('T',arg))
            body = "<is-composing><state>nudge</state></is-composing>"

        if cmd == "ALIVE":
            self.init('R')

        if cmd == "DEAD":
            self.init('R')
            self._header.append(('X','0'))

        if cmd == "ACK":
            body = ''
            if arg == 'M':
                self.Q = extra[1]
                self.I = extra[2]

            self.init_ack(arg)
            del self._header[0]
            self._header.insert(0,('F',extra[0]))

        if cmd == "IN":
            body ="<is-composing><state>fetion-show:\xe5\x9b\xa70x000101010000010001000000000000010000000</state></is-composing>"

            self.init('IN')
            self._header.insert(3,('T',arg))


        if cmd == "BYE":
            body = ''
            self.init('B')



        if cmd == "SetPresence":
            self.init('S')
            self._header.insert(3,('N',cmd))
            body = '<args><presence><basic value="%s" /></presence></args>' % arg

        if cmd == "PGPresence":
            self.init('SUB')
            self._header.append(('N',cmd))
            self._header.append(('X','0'))
            body = '<args><subscription><groups /></subscription></args>'

        if cmd == "PGSetPresence":
            self.init('S')
            self._header.insert(3,('N',cmd))
            body = '<args><groups /></args>'

        if cmd == "compactlist":
            self.init('SUB')
            self._header.append(('N',cmd))
            body = '<args><subscription><contacts><contact uri="%s" type="3" />'% arg
            for i in extra[0]:
                body += '<contact uri="%s" type="3" />' % i
            body += '</contacts></subscription></args>'
            
        if cmd == "StartChat":
            if arg == '':
                self.init('S')
                self._header.append(('N',cmd))
            else:
                self.init('R')
                self._header.append(('A','TICKS auth="%s"' % arg))
                self._header.append(('K','text/html-fragment'))
                self._header.append(('K','multiparty'))
                self._header.append(('K','nudge'))
                self._header.append(('K','share-background'))
                self._header.append(('K','fetion-show'))

        if cmd == "InviteBuddy":
            self.init('S')
            self._header.append(('N',cmd))
            body = '<args><contacts><contact uri="%s" /></contacts></args>'%arg

        if cmd == "PGGetGroupList":
            self.init('S')
            self._header.insert(3,('N',cmd))
            body = '<args><group-list version="1" attributes="name;identity" /></args>'
            


        if cmd == "SSSetScheduleSms":
            self.init('S')
            self._header.insert(3,('N',cmd))
            body = '<args><schedule-sms send-time="%s"><message>%s</message><receivers><receiver uri="%s" /></receivers></schedule-sms></args>' % (extra[0],arg,extra[1])
        if cmd == "GetOfflineMessages":
            self.init('S')
            self._header.insert(3,('N',cmd))
	    
        if cmd == "INFO":
            self.init('S')
            self._header.insert(3,('N',arg))
            if arg == "GetPersonalInfo":
                body = '<args><personal attributes="all" /><services version="" attributes="all" /><config attributes="all" /><quota attributes="all" /></args>'
            elif arg == "GetContactList":
                body = '<args><contacts><buddy-lists /><buddies attributes="all" /><mobile-buddies attributes="all" /><chat-friends /><blacklist /><allow-list /></contacts></args>'
            elif arg == "GetContactsInfo":
                body = '<args><contacts attributes="all">'
                for i in extra[0]:
                    body += '<contact uri="%s" />' % i
                body += '</contacts></args>'

            elif arg == "AddBuddy":
                tag = "sip"
                if len(extra[0]) == 11:
                    tag = "tel"

                body = '<args><contacts><buddies><buddy uri="%s:%s" buddy-lists="" desc="%s" addbuddy-phrase-id="0" /></buddies></contacts></args>' % (tag,extra[0],extra[1])
            elif arg == "AddMobileBuddy":
                body = '<args><contacts><mobile-buddies><mobile-buddy uri="tel:%s" buddy-lists="1" desc="%s" invite="0" /></mobile-buddies></contacts></args>' % (extra[0],extra[1])

            elif arg == "DeleteBuddy":

                body = '<args><contacts><buddies><buddy uri="%s" /></buddies></contacts></args>' % extra[0]



        
        #general SIPC info
        if len(body) != 0:
            self._header.append(('L',len(body)))
        for k in self._header:
            self._content = self._content + k[0] + ": " + str(k[1]) + "\r\n"
        self._content+="\r\n"
        self._content+= body
        if self.login_type == "HTTP":
            #IN TCP CONNECTION "SIPP" SHOULD NOT BEEN SEND
            self._content+= FetionSIPP
        return self._content

    def ack(self):
        """ack message from server"""
        content = self._content 
        d_print(('content',),locals())
        self.__tcp_send(content)

    def send(self):
        content = self._content 
        response = ''
        if self._lock:
            d_print("acquire lock ")
            self._lock.acquire()
            d_print("acquire lock ok ")
        d_print(('content',),locals())
        if self.login_type == "HTTP":
            #First time t SHOULD SET AS 'i'
            #Otherwise 405 code get
            if self.__seq == 1:
                t = 'i'
            else:
                t = 's'
            url = self._http_tunnel+"?t=%s&i=%s" % (t,self.__seq)
            ret = http_send(url,content,self.__exheaders)
            if not ret:
                raise PyFetionSocketError(405,'http stoped')
            response = ret.read()
            self.__seq+=1
            response = self.__sendSIPP()
            i = 0
            while response == FetionSIPP and i < 5:
                response = self.__sendSIPP()
                i += 1
            ret = self.__split(response)
            num = len(ret)
            d_print(('num',),locals())
            for rs in ret:
                code = self.get_code(rs)
                d_print(('rs',),locals())
                try:
                    int(code)
                    d_print(('code',),locals())
                    response = rs
                except exceptions.ValueError:
                    self.queue.put(rs)
                    continue

        else:
            self.__tcp_send(content)
            while response is '':
                try:
                    ret = self.__tcp_recv()
                except socket.error,e:
                    raise PyFetionSocketError(e)

                num = len(ret)
                d_print(('num',),locals())
                for rs in ret:
                    code = self.get_code(rs)
                    d_print(('rs',),locals())
                    try:
                        int(code)
                        d_print(('code',),locals())
                        response = rs
                    except exceptions.ValueError:
                        self.queue.put(rs)
                        continue
        if self._lock:
            self._lock.release()
            d_print("release lock")
 

        return response



    def __sendSIPP(self):
        body = FetionSIPP
        url = self._http_tunnel+"?t=s&i=%s" % self.__seq
        ret = http_send(url,body,self.__exheaders)
        if not ret:
            raise PyFetionSocketError(405,'Http error')
        response = ret.read()
        d_print(('response',),locals())
        self.__seq+=1
        return response

    def __tcp_init(self):
        try:
            self.__sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error,e:
            s = None
            raise PyFetionSocketError(e)
        (host,port) = tuple(self._sipc_proxy.split(":"))
        port = int(port)
        try:
            self.__sock.connect((host,port))
        except socket.error,e:
            self.__sock.close()
            raise PyFetionSocketError(e)


    def close(self):
        self.__sock.close()

    def __tcp_send(self,msg):
        try:
            self.__sock.send(msg)
        except socket.error,e:
            self.__sock.close()
            raise PyFetionSocketError(e)

    def __tcp_recv(self):
        """read bs bytes first,if there's still more data, read left data.
           get length from header :
           L: 1022 
        """
        total_data = []
        bs = 1024
        try:
            data = self.__sock.recv(bs)
            total_data.append(data)
            while True and data:
                if not re.search("L: (\d+)",data) and not data[-4:] == '\r\n\r\n':
                    data = self.__sock.recv(bs)
                    total_data.append(data)
                elif not re.search("L: (\d+)",data) and data[-4:] == '\r\n\r\n':
                    return total_data
                else:
                    break
                

            while re.search("L: (\d+)",data):
                n = len(data)
                L = int(re.findall("L: (\d+)",data)[-1])
                p = data.rfind('\r\n\r\n')
                abc = data
                data = ''

                p1 = data.rfind(str(L))
                if p < p1:
                    d_print("rn before L")
                    left = L + n - (p1 + len(str(L))) + 4

                else:
                    left = L - (n - p -4)
                if left == L:
                    d_print("It happened!")
                    break
                d_print(('n','L','p','left',),locals())

                #if more bytes then last L
                #come across another command: BN etc.
                #read until another L come
                if left < 0:
                    d_print(('abc',),locals())
                    d = ''
                    left = 0
                    while True:
                        d = self.__sock.recv(bs)
                        data += d
                        if re.search("L: (\d+)",d):
                            break
                    d_print("read left bytes")
                    d_print(('data',),locals())
                    total_data.append(data)

                #read left bytes in last L
                while left:
                    data = self.__sock.recv(left)
                    n = len(data)
                    left = left - n

                    if not data:
                        break
                    total_data.append(data)

        except socket.error,e:
            #self.__sock.close()
            raise PyFetionSocketError(e)

        return self.__split(''.join(total_data))

        #return ''.join(total_data)

    def __split(self,data):
        
        c = []
        d = []

        #remove string "SIPP"
        if self.login_type == "HTTP":
            data = data[:-4]
        L = re.findall("L: (\d+)",data)
        L = [int(i) for i in L]

        d_print(('data',),locals())
        b = data.split('\r\n\r\n')
        for i in range(len(b)):
            if b[i].startswith(self.ver) and "L:" not in b[i]:
                d.append(b[i]+'\r\n\r\n')
                del b[i]
                break

        c.append(b[0])
        d_print(('L','b',),locals())
        for i in range(0,len(L)):
            c.append(b[i+1][:L[i]])
            c.append(b[i+1][L[i]:])


        
        d_print(('c',),locals())
        #remove last empty string
        if c[-1] == '':
            c.pop()

        c.reverse()
        while c:
            s = c.pop()
            s += '\r\n\r\n'
            if c:
                s += c.pop()
            d.append(s)

        d_print(('d',),locals())
        return d

    def __get_salt(self):
        return self.__hash_passwd()[:8]

    def __get_cnonce(self):
        return md5(str(uuid1())).hexdigest().upper()

    def __get_response_md5(self,nonce,cnonce):
        #nonce = "3D8348924962579418512B8B3966294E"
        #cnonce= "9E169DCA9CBD85F1D1A89A893E00917E"
        key = md5("%s:%s:%s" % (self.sid,self._domain,self.passwd)).digest()
        h1  = md5("%s:%s:%s" % (key,nonce,cnonce)).hexdigest().upper()
        h2  = md5("REGISTER:%s" % self.sid).hexdigest().upper()
        response  = md5("%s:%s:%s" % (h1,nonce,h2)).hexdigest().upper()
        #d_print(('nonce','cnonce','key','h1','h2','response'),locals())
        return response

    def __get_response_sha1(self,nonce,cnonce):
        #nonce = "3D8348924962579418512B8B3966294E"
        #cnonce= "9E169DCA9CBD85F1D1A89A893E00917E"
        hash_passwd = self.__hash_passwd()
        hash_passwd_str = binascii.unhexlify(hash_passwd[8:])
        key = sha1("%s:%s:%s" % (self.sid,self._domain,hash_passwd_str)).digest()
        h1  = md5("%s:%s:%s" % (key,nonce,cnonce)).hexdigest().upper()
        h2  = md5("REGISTER:%s" % self.sid).hexdigest().upper()
        response = md5("%s:%s:%s" % (h1,nonce,h2)).hexdigest().upper()
        return response

    def __hash_passwd(self):
        #salt = '%s%s%s%s' % (chr(0x77), chr(0x7A), chr(0x6D), chr(0x03))
        salt = 'wzm\x03'
        src  = salt+sha1(self.passwd).digest()
        return "777A6D03"+sha1(src).hexdigest().upper()



def http_send(url,body='',exheaders='',login=False):
    global proxy_info
    conn = ''
    headers = {
               'User-Agent':'IIC2.0/PC 3.2.0540',
              }
    headers.update(exheaders)

    if proxy_info:
        proxy_support = urllib2.ProxyHandler(\
            {"http":"http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info})
        opener = urllib2.build_opener(proxy_support)
    else:
        opener = urllib2.build_opener()

    urllib2.install_opener(opener)
    request = urllib2.Request(url,headers=headers,data=body)
    #add retry for GAE. 
    #PyFetion will get 405 code sometimes, we should re-send the request.
    retry = 5
    while retry:
        try:
            conn = urllib2.urlopen(request)
        except urllib2.URLError, e:
            if hasattr(e,'code'):
                code = e.code
                msg = e.read()
            else:
                code = e.reason.errno
                msg = e.reason.strerror

            d_print(('code','msg'),locals())
            if code == 401 or code == 400:
                if login:
                    raise PyFetionAuthError(code,msg)
            if code == 404 or code == 500:
                raise PyFetionSupportError(code,msg)
            if code == 405:
                retry = retry - 1
                continue
            raise PyFetionSocketError(code,msg)
        break
    return conn

class on_cmd_I(Thread,SIPC):
     #if there is invitation SIP method [I]
    def __init__(self,fetion,response,args):
        self.fetion = fetion
        self.response = response
        self.args = args
        self.begin = time.time()
        self.Q = 4
        self.I = 4
        self.from_uri = ''
        Thread.__init__(self)

    def run(self):
    
        running = True
        try:
            self.from_uri = re.findall('F: (.*)',self.response)[0]
            credential = re.findall('credential="(.+?)"',self.response)[0]
            sipc_proxy = re.findall('address="(.+?);',self.response)[0]
        except:
            d_print("find tag error")
            return

        self.from_uri = self.from_uri.rstrip()
        self.fetion._ack('I',self.from_uri)
        self.args[5] = sipc_proxy
        #no lock
        self.args[7] = None

        #SIPC(self.args)
        SIPC.__init__(self,self.args)
        self.get("StartChat",credential)
        response = self.send()
        self.deal_msg(response)


        while running:
            if not self.queue.empty():
                response = self.queue.get()
            else:
                response = self.recv()
            if len(response) == 0:
                d_print("User Left converstion")
                self.fetion.session.pop(self.from_uri)
                return
            self.deal_msg(response)
            
            #self._bye()


    def deal_msg(self,response):

        try:
            Q = re.findall('Q: (-?\d+) M',response)
            I = re.findall('I: (-?\d+)',response)
        except:
            d_print("NO Q")
            return False

        for i in range(len(Q)):
            self.Q = Q[i]

            self.fetion.queue.put(response)

            self._ack('M')
            self._ack('IN')
        return True

    def _ack(self,cmd):
        """ack message from uri"""
        self.get("ACK",cmd,self.from_uri,self.Q,self.I)
        self.response = self.ack()
        self.deal_msg(self.response)

    def _send_msg(self,msg):
        msg = msg.replace('<','&lt;')
        self.get("SendMsg",'',msg)
        self.send()
        
    def _bye(self):
        """say bye to this session"""
        self.get("BYE",'')
        self.send()



class PyFetion(SIPC):

    __log = ''
    __sipc_url = ''
    _ssic = ''
    _lock = RLock()
    _sipc_proxy  = ''
    _domain = ''
    _http_tunnel = ''
    
    mobile_no = ''
    passwd = ''
    queue = Queue()
    sid = ''
    login_type = ''
    receving = False
    presence = ''
    debug = False
    contactlist = {}
    grouplist = {}
    session = {}

    def __init__(self,mobile_no,passwd,login_type="TCP",debug=False):
        self.mobile_no = mobile_no
        self.passwd = passwd
        self.login_type = login_type
         

        if debug == True:
            logging.basicConfig(level=logging.DEBUG,format='%(message)s')
            self.__log = logging
        elif debug == "FILE":
            logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(thread)d %(message)s',
                        filename='./PyFetion.log',
                        filemode='w')
            self.__log = logging

        global d_print
        #replace global function with self method
        d_print = self.__print

        self.__sipc_url   = "https://uid.fetion.com.cn/ssiportal/SSIAppSignIn.aspx"
        self._sipc_proxy = "221.176.31.45:8080"
        self._http_tunnel= "http://221.176.31.45/ht/sd.aspx"
        #uncomment this line for getting configuration from server everytime
        #It's very slow sometimes, so default use fixed configuration
        #self.__set_system_config()


    def login(self,presence=FetionOnline):
        if not self.__get_uri():
            return False
        self.presence = presence

        try:
            self.__register(self._ssic,self._domain)
        except PyFetionRegisterError,e:
            d_print("Register Failed!")
            return False
        #self.get_personal_info()
        if not self.get_contactlist():
            d_print("get contactlist error")
            return False
        self.get("compactlist",self.__uri,self.contactlist.keys())
        response = self.send()
        code = self.get_code(response)
        if code != 200:
            return False
        #self.get("PGGetGroupList",self.__uri)
        #response = self.send()

        self.get_offline_msg()
        self.receving = True
        return True


    def logout(self):
        
        self.get("DEAD",'')
        self.send()
        self.receving = False

    def start_chat(self,who):

        self.get("StartChat",'')
        response = self.send()

        try:
            credential = re.findall('credential="(.+?)"',response)[0]
            sipc_proxy = re.findall('address="(.+?);',response)[0]
        except:
            d_print("find tag error")
            return False

        args = [self.sid,self._domain,self.login_type,self._http_tunnel,self._ssic,sipc_proxy,self.presence,None]


        _SIPC = SIPC(args)
        _SIPC.get("StartChat",credential)
        response = _SIPC.send()

        _SIPC.get("InviteBuddy",who)
        response = _SIPC.send()
        code = _SIPC.get_code(response)
        if code != 200:
            return False

        response = _SIPC.recv()
        try:
            type = re.findall('<event type="(.+?)"',response)[0]
        except :
            return False
        if type == "UserEntered":
            return FetionHidden
        elif type == "UserFailed":
            return FetionOnline



    def set_presence(self,presence):
        """set status of fetion"""
        if self.presence == presence:
            return True
        self.get("SetPresence",presence)
        response = self.send()
        code = self.get_code(response)
        if code == 200:
            self.presence = presence
            d_print("set presence ok.")
            return True
        return False

        #self.get("PGSetPresence",presence)
        #response = self.send()
        
    def get_offline_msg(self):
        """get offline message from server"""
        self.get("GetOfflineMessages",'')
        response = self.send()
        return response

    def add(self,who):
        """add friend who should be mobile number or fetion number"""
        my_info = self.get_info()
        try:
            #nick_name = re.findall('nickname="(.*?)" ',my_info)[0]
            nick_name = my_info[0]
        except IndexError:
            nick_name = " "

        #code = self._add(who,nick_name,"AddMobileBuddy")
        code = self._add(who,nick_name)
        if code == 522:
            code = self._add(who,nick_name,"AddMobileBuddy")

        if code == 404 or code == 400 :
            d_print("Not Found")
            return False
        if code == 521:
            d_print("Aleady added.")
            return True
        if code == 200:
            return True

        return False

    def delete(self,who):
        
        if who.isdigit() and len(who) == 11:
            who = "tel:" + who
        else:
            who = self.get_uri(who)
            if not who:
                return False

        self.get("INFO","DeleteBuddy",who)
        response = self.send()
        code = self.get_code(response)
        if code == 404 or code == 400 :
            d_print("Not Found")
            return False
        if code == 200:
            return True
        return False

    def _add(self,who,nick_name,type="AddBuddy"):

        self.get("INFO",type,who,nick_name)
        response = self.send()
        code = self.get_code(response)
        return code


    def get_personal_info(self):
        """get detail information of me"""
        self.get("INFO","GetPersonalInfo")
        response = self.send()
        nickname = re.findall('nickname="(.+?)"',response)[0]
        impresa = re.findall('impresa="(.+?)"',response)[0]
        #mobile = re.findall('mobile-no="(^1[35]\d{9})"',response)[0]
        mobile = re.findall('mobile-no="(.+?)"',response)[0]
        name = re.findall(' name="(.+?)"',response)[0]
        gender = re.findall('gender="([01])"',response)[0]
        fetion_number = re.findall('user-id="(\d{9})"',response)[0]
        #email = re.findall('personal-email="(.+?)"',response)[0]
        response = []
        response.append(nickname)
        response.append(impresa)
        response.append(mobile)
        response.append(name)
        response.append(fetion_number)
        #response.append(gender)
        #response.append(email)
        return response

    def get_info(self,who=None):
        """get contact info.
           who should be uri. string or list
        """
        alluri = []
        if who == None:
            return self.get_personal_info()

        if type(who) is not list:
            alluri.append(who) 
        else:
            alluri = who
            
        self.get("INFO","GetContactsInfo",alluri)
        response = self.send()
        return response



    def set_info(self,info):
        contacts = re.findall('<contact (.+?)</contact>',info)
        contacts += re.findall('<presence (.+?)</presence>',info)
        for contact in contacts:
            #print contacts
            uri = ''
            nickname = ''
            mobile_no = ''
            try:
                (uri,mobile_no,nickname) = re.findall('uri="(.+?)".+?mobile-no="(.*?)".+?nickname="(.*?)"',contact)[0]
            except:
                try:
                    (uri,nickname) = re.findall('uri="(.+?)".+?nickname="(.*?)"',contact)[0]
                except:
                    continue
            #print uri,nickname,mobile_no
            if uri == self.__uri:
                continue
            if self.contactlist[uri][0] == '':
                self.contactlist[uri][0] = nickname

            if self.contactlist[uri][1] == '':
                self.contactlist[uri][1] = mobile_no


    
    def get_contactlist(self):
        """get contact list
           contactlist is a dict:
           {uri:[name,mobile-no,status,type,group-id]}
        """
        buddy_list = ''
        allow_list = ''
        chat_friends = ''
        need_info = []

        self.get("INFO","GetContactList")
        response = self.send()
        code = self.get_code(response)
        if code != 200:
            return False

        try:
            d = re.findall('<buddy-lists>(.*?)<allow-list>',response)[0]
        #No buddy here
        except:
            return True
        try:
            buddy_list = re.findall('uri="(.+?)" user-id="\d+" local-name="(.*?)" buddy-lists="(.*?)"',d)
            self.grouplist = re.findall('id="(\d+)" name="(.*?)"',d)
        except:
            return False

        try:
            d = re.findall('<chat-friends>(.*?)</chat-friends>',d)[0]
            chat_friends = re.findall('uri="(.+?)" user-id="\d+"',d)
        except:
            pass

        
        for uri in chat_friends:
            if uri not in self.contactlist:
                l = ['']*5
                need_info.append(uri)
                self.contactlist[uri] = l       
                self.contactlist[uri][0] = ''      
                self.contactlist[uri][2] = FetionHidden       
                self.contactlist[uri][3] = 'A'      


        #buddy_list [(uri,local_name),...]
        for p in buddy_list:
            l = ['']*5

            #set uri
            self.contactlist[p[0]] = l
            #set local-name
            self.contactlist[p[0]][0] = p[1]       
            #set default status
            self.contactlist[p[0]][2] = FetionHidden       
            #self.contactlist[p[0]][2] = FetionOffline       

            #set group id here!
            self.contactlist[p[0]][4] = p[2]

            if p[0].startswith("tel"):
                self.contactlist[p[0]][3] = 'T'      
                self.contactlist[p[0]][2] = FetionHidden       
                #set mobile_no
                self.contactlist[p[0]][1] = p[0][4:]
                #if no local-name use mobile-no as name
                if p[1] == '':
                    self.contactlist[p[0]][0] = self.contactlist[p[0]][1]
            else:
                self.contactlist[p[0]][3] = 'B'      
                if self.contactlist[p[0]][0] == '':
                    need_info.append(p[0])
        """
        try:
            s = re.findall('<allow-list>(.+?)</allow-list>',response)[0]
            allow_list = re.findall('uri="(.+?)"',s)
        except:
            pass

        #allow_list [uri,...]
        for uri in allow_list:
            if uri not in self.contactlist:
                l = ['']*4
                need_info.append(uri)
                self.contactlist[uri] = l       
                self.contactlist[uri][0] = ''      
                self.contactlist[uri][2] = FetionHidden       
                self.contactlist[uri][3] = 'A'      

        """
        ret = self.get_info(need_info)
        self.set_info(ret)

        return True

    def get_uri(self,who):
        """get uri from fetion number"""
        if who in self.__uri:
            return self.__uri

        if who.startswith("sip"):
            return who

        for uri in self.contactlist:
            if who in uri:
                return uri
        return None

    def send_msg(self,msg,to=None,flag="CatMsg"):
        """more info at send_sms function.
           if someone's fetion is offline, msg will send to phone,
           the same as send_sms.
           """

        if not to:
            to = self.__uri
        #Fetion now can use mobile number(09.02.23)
        #like tel: 13888888888
        #but not in sending to PC
        elif flag != "CatMsg" and to.startswith("tel:"):
            pass

        elif flag == "CatMsg" and to.startswith("tel:"):
            return False
        elif flag != "CatMsg" and len(to) == 11 and to.isdigit():
            to = "tel:"+to

        else:
            to = self.get_uri(to)
            if not to:
                return False
        msg = msg.replace('<','&lt;')
        self.get(flag,to,msg)
        try:
            response = self.send()
        except PyFetionSocketError,e:
            d_print(('e',),locals())
            return False

        code = self.get_code(response)
        if code == 280:
            d_print("Send sms OK!")
        elif code == 200:
            d_print("Send msg OK!")
        else:
            d_print(('code',),locals())
            return False
        return True

    def send_sms(self,msg,to=None,long=True):
        """send sms to someone, if to is None, send self.
           if long is True, send long sms.(Your phone should support.)
           to can be mobile number or fetion number
           """
        if long:
            return self.send_msg(msg,to,"SendCatSMS")
        else:
            return self.send_msg(msg,to,"SendSMS")

    def send_schedule_sms(self,msg,time,to=None):
        if not to:
            to = self.__uri
        elif len(to) == 11 and to.isdigit():
            to = "tel:"+to
        else:
            to = self.get_uri(to)
            if not to:
                return False

        msg = msg.replace('<','&lt;')
        self.get("SSSetScheduleSms",msg,time,to)
        response = self.send()
        code = self.get_code(response)
        if code == 486:
            d_print("Busy Here")
            return None
        if code == 200:
            id = re.search('id="(\d+)"',response).group(1)
            d_print(('id',),locals(),"schedule_sms id")
            return id


    def alive(self):
        """send keepalive message"""
        self.get("ALIVE",'')
        response = self.send()
        code = self.get_code(response)
        if code == 200:
            d_print("keepalive message send ok.")
            return True
        return False

    def receive(self):
        """response from server"""
        threads = []

        while self.receving:
            if not self.queue.empty():
                response = self.queue.get()
            else:
                try:
                    response = self.recv(5)
                except PyFetionSocketError,e:
                    yield ["NetworkError",e.msg]
                    continue

            if response =="TimeOut":
                continue
            elif len(response) == 0:
                d_print("logout")
                return
            elif response.startswith("BN"):
                try:
                    type = re.findall('<event type="(.+?)"',response)[0]
                except IndexError:
                    d_print("Didn't find type")
                    d_print(('response',),locals())
                    

                if type == "ServiceResult":
                    self.set_info(response)
                      
                if type == "deregistered" or type=="disconnect":
                    self.receving = False
                    yield [type]
                if type == "PresenceChanged":
                    self.set_info(response)
                    ret = re.findall('<presence uri="(.+?)">.+?value="(.+?)".+?type="sms">(\d+)\.',response)
                    if not ret:
                        ret = re.findall('<presence uri="(.+?)">.+?value="(.+?)"',response)


                    #remove self uri
                    event = [i for i in ret if i[0] != self.__uri]
                    event = list(set(event))
                    for e in event:
                        if len(e) == 3 and e[2] == FetionOffline:
                            self.contactlist[e[0]][2] = e[2]
                        else:
                            self.contactlist[e[0]][2] = e[1]
                            

                    yield [type,event]
                if type == "UpdateBuddy" or type == "UpdateMobileBuddy":
                    uri = re.findall('uri="(.+?)"',response)[0]
                    l = ['']*4
                    self.contactlist[uri] = l
                    if type == "UpdateBuddy":
                        ret = self.get_info(uri)
                        self.set_info(ret)
                    else:
                        self.contactlist[uri][3] = 'T'      
                        self.contactlist[uri][2] = FetionHidden       
                        self.contactlist[uri][1] = uri[4:]
                        self.contactlist[uri][0] = uri[4:]

            elif response.startswith("M"):
                try:
                    from_uri = re.findall('F: (.*)',response)[0].strip()
                    msg = re.findall('\r\n\r\n(.*)',response,re.S)[0]
                except:
                    d_print("Message without content")
                    continue
                #if from PC remove <Font>
                try:
                    msg = re.findall('<Font .+?>(.+?)</Font>',msg,re.S)[0]
                except:
                    pass

                #from phone or PC
                try:
                    XI = re.findall('XI: (.*)',response)[0]
                    type = "PC"
                except:
                    type = "PHONE"
                #ack this message 
                try:
                    Q = re.findall('Q: (-?\d+) M',response)[0]
                    I = re.findall('I: (-?\d+)',response)[0]
                    self._ack('M',from_uri,Q,I)
                except:
                    pass

                yield ["Message",from_uri,msg,type]

            elif response.startswith("I"):
                try:
                    from_uri = re.findall('F: (.*)',response)[0].rstrip()
                except:
                    pass
                args = [self.sid,self._domain,self.login_type,self._http_tunnel,self._ssic,self._sipc_proxy,self.presence,None]

                
                t = on_cmd_I(self,response,args)

                t.setDaemon(True)
                t.start()
                self.session[from_uri] = t
                #print self.session


    def _ack(self,cmd,from_uri,Q=0,I=0):
        """ack message """
        self.get("ACK",cmd,from_uri,Q,I)
        self.ack()


    def __register(self,ssic,domain):
        SIPC.__init__(self)
        response = ''
        for step in range(1,3):
                self.get("REG",step,response)
                response = self.send()

        code = self.get_code(response)
        if code == 200:
            d_print("register successful.")
        else:
            raise PyFetionRegisterError(code,response)


    def __get_system_config(self):
        global FetionConfigURL
        global FetionConfigXML
        url = FetionConfigURL
        body = FetionConfigXML % self.mobile_no
        d_print(('url','body'),locals())
        config_data = http_send(url,body).read()
         

        sipc_url = re.search("<ssi-app-sign-in>(.*)</ssi-app-sign-in>",config_data).group(1)
        sipc_proxy = re.search("<sipc-proxy>(.*)</sipc-proxy>",config_data).group(1)
        http_tunnel = re.search("<http-tunnel>(.*)</http-tunnel>",config_data).group(1)
        d_print(('sipc_url','sipc_proxy','http_tunnel'),locals())
        self.__sipc_url   = sipc_url
        self._sipc_proxy = sipc_proxy
        self._http_tunnel= http_tunnel
        

    def __get_uri(self):
        url = self.__sipc_url+"?mobileno="+self.mobile_no+"&pwd="+urllib.quote(self.passwd)
        d_print(('url',),locals())
        ret = http_send(url,login=True)

        header = str(ret.info())
        body   = ret.read()
        try:
            ssic = re.search("ssic=(.*);",header).group(1)
            sid  = re.search("sip:(.*)@",body).group(1)
            uri  = re.search('uri="(.*)" mobile-no',body).group(1)
            status = re.search('user-status="(\d+)"',body).group(1)
        except:
            return False
        domain = "fetion.com.cn"

        d_print(('ssic','sid','uri','status','domain'),locals(),"Get SID OK")
        self.sid = sid
        self.__uri = uri
        self._ssic = ssic
        self._domain = domain

        return True

    def __print(self,vars=(),namespace=[],msg=''):
        """if only sigle variable ,arg should like this ('var',)"""
        if not self.__log:
            return
        if vars and not namespace and not msg:
            msg = vars
        if vars and namespace:
            for var in vars:
                if var in namespace:
                    self.__log.debug("%s={%s}" % (var,str(namespace[var])))
        if msg:
            self.__log.debug("%s" % msg)

