#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIT License
#By : cocobear.cn@gmail.com

import urllib2
import re
import socket
import os
import time
import exceptions
import logging

from hashlib import md5
from hashlib import sha1
from threading import RLock
from threading import Thread
from select import select
from Queue import Queue
from binascii import a2b_hex,b2a_hex
from struct import pack


FetionOnline = "400"
FetionBusy   = "600"
FetionAway   = "100"
FetionHidden  = "0"
FetionOffline = "365"

FetionVer = "4.1.1160"
#"SIPP" USED IN HTTP CONNECTION
FetionSIPP= "SIPP"
FetionNavURL = "nav.fetion.com.cn"
FetionConfigURL = "http://nav.fetion.com.cn/nav/getsystemconfig.aspx"


FetionConfigXML = """<config><user mobile-no="%s" /><client type="PC" version="%s" platform="W5.1" /><servers version="0" /><service-no version="0" /><parameters version="0" /><hints version="0" /><http-applications version="0" /><client-config version="0" /><services version="0" /><banners version="0" /></config>"""

FetionLoginXML = """<args><device accept-language="default" machine-code="00000000000000000000000000000000" /><caps value="1FFF" /><events value="7F" /><user-info mobile-no="%s" user-id="%s"><personal version="0" attributes="v4default;alv2-version;alv2-warn;dynamic-version" /><custom-config version="0"/><contact-list version="0" buddy-attributes="v4default" /></user-info><credentials domains="fetion.com.cn;m161.com.cn;www.ikuwa.cn;games.fetion.com.cn;turn.fetion.com.cn;pos.fetion.com.cn;ent.fetion.com.cn;mms.fetion.com.cn"/><presence><basic value="%s" desc="" /><extendeds /></presence></args>
"""


proxy_info = False
log = None
#uncomment below line if you need proxy
"""
proxy_info = {'user' : '',
              'pass' : '',
              'host' : '218.249.83.87',
              'port' : 8080 
              }
"""



def Pass(*args):
    pass


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
            log(locals())
            try:
                msg = socket.errorTab[e.errno]
            except:
                msg = ''
            self.args = (e.errno,msg)
            self.code = e.errno
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
    
class PyFetionPiccError(PyFetionException):
    """Authentication error.
    Your need enter pic code .
    """


class SIPC():

    global FetionVer
    global FetionSIPP
    global FetionLoginXML

    _header = ''
    #body = ''
    _content = ''
    code = ''
    ver  = "SIP-C/4.0"
    Q   = 1
    I   = 1
    queue = Queue()

    def __init__(self,args=[]):
        self.__seq = 1

        if args:
            [self.userid,self.sid, self._domain,self.login_type, self._http_tunnel,\
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
                if num == 0:
                    return ret
                if num == 1:
                    return ret[0]
                for r in ret:
                    self.queue.put(r)
                    log(locals())
                    
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
            except AttributeError,e:
                pass
            return cmd
        return self.code
 
    def get(self,cmd,arg,*extra):
        body = ''
        if extra:
            body = extra[0]
        if cmd == "REG":
            self.init('R')
            if arg == 1:
                self._header.insert(3,('CN','491c23644b7769ede1af078cb14901e2'))
                self._header.insert(4,('CL','type="pc",version="%s"'%FetionVer))

                pass
            if arg == 2:
                body = FetionLoginXML % (self.mobile_no,self._user_id,self.presence)
                nonce = re.search('nonce="(.+?)"',extra[0]).group(1)
                key = re.search('key="(.+?)"',extra[0]).group(1)
                #signature = re.search('signature="(.+?)"',extra[0]).group(1)

                p1 = sha1("fetion.com.cn:"+self.passwd).hexdigest()
                p2 = sha1(pack("l",long(self._user_id))+a2b_hex(p1)).hexdigest()
                plain = nonce+a2b_hex(p2)+a2b_hex("e146a9e31efb41f2d7ab58ba7ccd1f2958ec944a5cffdc514873986923c64567")
                response = self.__RSA_Encrypt(plain,len(plain),a2b_hex(key[:-6]),a2b_hex(key[-6:]))


                log(locals())

                self._header.insert(3,('A','Digest algorithm="SHA1-sess-v4",response="%s"' % (response)))
                if self.verify:
                    self._header.insert(4,('A','Verify algorithm="%s",type="GeneralPic",response="%s",chid="%s"'%(self.verify_info[0],self.verify_info[1],self.verify_info[2])))


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



        if cmd == "SetPresenceV4":
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

        if cmd == "PresenceV4":
            self.init('SUB')
            self._header.append(('N',cmd))
            body = '<args><subscription self="v4default;mail-count;impresa;sms-online-status;feed-version;feed-type;es2all" buddy="v4default;feed-version;feed-type;es2all" version="" /></args>'
            
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
        log('content:'+content)
        self.__tcp_send(content)

    def send(self):
        content = self._content 
        response = ''
        if self._lock:
            #log("acquire lock ")
            self._lock.acquire()
            #log("acquire lock ok ")
        log('content:'+content)
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
            for rs in ret:
                code = self.get_code(rs)
                try:
                    int(code)
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

                for rs in ret:
                    code = self.get_code(rs)
                    try:
                        int(code)
                        response = rs
                    except exceptions.ValueError:
                        self.queue.put(rs)
                        continue
        if self._lock:
            self._lock.release()
            #log("release lock")
 

        return response



    def __sendSIPP(self):
        body = FetionSIPP
        url = self._http_tunnel+"?t=s&i=%s" % self.__seq
        ret = http_send(url,body,self.__exheaders)
        if not ret:
            raise PyFetionSocketError(405,'Http error')
        response = ret.read()
        log('response:'+response)
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
                    log("rn before L")
                    left = L + n - (p1 + len(str(L))) + 4

                else:
                    left = L - (n - p -4)
                if left == L:
                    log("It happened!")
                    break

                #if more bytes then last L
                #come across another command: BN etc.
                #read until another L come
                if left < 0:
                    log('abc')
                    d = ''
                    left = 0
                    while True:
                        d = self.__sock.recv(bs)
                        data += d
                        if re.search("L: (\d+)",d):
                            break
                    log("read left bytes")
                    log('data:'+data)
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

        log('data:'+data)
        b = data.split('\r\n\r\n')
        for i in range(len(b)):
            if b[i].startswith(self.ver) and "L:" not in b[i]:
                d.append(b[i]+'\r\n\r\n')
                del b[i]
                break

        c.append(b[0])
        for i in range(0,len(L)):
            c.append(b[i+1][:L[i]])
            c.append(b[i+1][L[i]:])


        
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

        return d
    def __RSA_Encrypt(self,plain,length,rsa_n,rsa_e):
        import  ctypes 

        lib = "./RSA_Encrypt."
        if os.name == "posix":
            lib += "so"
        else:
            lib += "dll"
        crypto_handler = ctypes.cdll.LoadLibrary(lib)

        c_ubyte_p = ctypes.POINTER(ctypes.c_ubyte)
        RSA_Encrypt = crypto_handler.RSA_Encrypt
        RSA_Encrypt.argtypes = [ctypes.c_char_p,ctypes.c_int,c_ubyte_p,c_ubyte_p]
        RSA_Encrypt.restype = c_ubyte_p


        n = (ctypes.c_ubyte*128)()
        ctypes.memmove(n,rsa_n,128)

        e = (ctypes.c_ubyte*3)()
        ctypes.memmove(e,rsa_e,3)

        ret = RSA_Encrypt(plain,length,n,e)
        return b2a_hex(ctypes.string_at(ret,128))



def http_send(url,body='',exheaders='',login=False):
    global proxy_info,FetionVer
    conn = ''
    headers = {
               'User-Agent':'IIC4.0/PC %s'%FetionVer,
              }
    headers.update(exheaders)

    log('url:'+url)
    if proxy_info:
        proxy_support = urllib2.ProxyHandler(\
            {"http":"http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info})
        opener = urllib2.build_opener(proxy_support)
    else:
        opener = urllib2.build_opener()

    urllib2.install_opener(opener)
    if body == '':
        request = urllib2.Request(url,headers=headers)
    else:
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

            log(locals())
            if code == 401 or code == 400:
                if login:
                    raise PyFetionAuthError(code,msg)
            if code == 404 or code == 500:
                raise PyFetionSupportError(code,msg)
            if code == 405:
                retry = retry - 1
                continue
            if code == 421:
                raise PyFetionPiccError(code,msg)
            raise PyFetionSocketError(code,msg)
        break
    return conn



def get_pic(algorithm,obj):

    pic_url = "http://nav.fetion.com.cn/nav/GetPicCodeV4.aspx?algorithm="+algorithm
    ret = http_send(pic_url,login=True)
    data = ret.read()

    pic_id = re.findall('pic-certificate id="(.+?)"',data)[0]
    pic64 = re.findall('pic="(.+?)"',data)[0]
    import base64
    from ImageShow import show
    fname = "fetion_verify.bmp"
    pic = base64.decodestring(pic64)
    f = file(fname,"wb")
    f.write(pic)
    f.close()
    show(fname)
    pic_code = raw_input("\t输入验证码".decode('utf-8').encode((os.name == 'posix' and 'utf-8' or 'cp936')))
    obj.verify = True
    obj.verify_info = [algorithm,pic_code,pic_id]

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
            log("find tag error")
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
                log("User Left converstion")
                self.fetion.session.pop(self.from_uri)
                return
            self.deal_msg(response)
            
            #self._bye()


    def deal_msg(self,response):

        try:
            Q = re.findall('Q: (-?\d+) M',response)
            I = re.findall('I: (-?\d+)',response)
        except:
            log("NO Q")
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
    _user_id = ''
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
    session = {}
    verify = False
    verify_info = []

    def __init__(self,mobile_no,passwd,login_type="TCP",debug=False):
        self.mobile_no = mobile_no
        self.passwd = passwd
        self.login_type = login_type
        global log
         

        if debug == True:
            logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(lineno)d %(funcName)s  %(message)s',
                        )
            log = logging.debug
        elif debug == "FILE":
            logging.basicConfig(level=logging.DEBUG,
                    format='Line:%(lineno)d Fun:%(funcName)s  %(message)s',
                        filename='./PyFetion.log',
                        filemode='w')
            log = logging.debug
        else:
            log = Pass
        
        #replace global function with self method

        self.__sipc_url   = "https://uid.fetion.com.cn/ssiportal/SSIAppSignInV4.aspx"
        self._sipc_proxy = "221.176.31.45:8080"
        self._http_tunnel= "http://221.176.31.45/ht/sd.aspx"
        #uncomment this line for getting configuration from server
        #self.__set_system_config()


    def login(self,presence=FetionOnline):
        if not self.__get_uri():
            return False
        self.presence = presence

        try:
            response = self.__register(self._ssic,self._domain)
        except PyFetionRegisterError,e:
            log("Register Failed!")
            return False
        #self.get_personal_info()
        self.get_contactlist(response)

        self.get("PresenceV4","")
        response = self.send()
        log(locals())

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
            log("find tag error")
            return False

        args = [self._user_id,self.sid,self._domain,self.login_type,self._http_tunnel,self._ssic,sipc_proxy,self.presence,None]


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
        self.get("SetPresenceV4",presence)
        response = self.send()
        code = self.get_code(response)
        if code == 200:
            self.presence = presence
            log("set presence ok.")
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
            nick_name = re.findall('nickname="(.*?)" ',my_info)[0]
        except IndexError:
            nick_name = " "

        #code = self._add(who,nick_name,"AddMobileBuddy")
        code = self._add(who,nick_name)
        if code == 522:
            code = self._add(who,nick_name,"AddMobileBuddy")

        if code == 404 or code == 400 :
            log("Not Found")
            return False
        if code == 521:
            log("Aleady added.")
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
            log("Not Found")
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
            self.contactlist[uri][1] = mobile_no

        #log(('self.contactlist',),locals())

    
    def get_contactlist(self,response):
        """get contact list
           contactlist is a dict:
           {uri:[name,mobile-no,status,type]}
        """
        buddy_list = ''
        chat_friends = ''
        need_info = []

        d = re.findall('<contact-list (.*?)</contact-list>',response)[0]
        try:
            buddy_list = re.findall('<b .+? u="(.+?)" n="(.*?)"',d)
        except:
            return False


        #buddy_list [(uri,local_name),...]
        for p in buddy_list:
            l = ['']*4

            #set uri
            self.contactlist[p[0]] = l       
            #set local-name
            self.contactlist[p[0]][0] = p[1]       
            #set default status
            self.contactlist[p[0]][2] = FetionHidden       
            #self.contactlist[p[0]][2] = FetionOffline       

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

        #ret = self.get_info(need_info)
        log(len(self.contactlist))
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
        self.get(flag,to,msg)
        try:
            response = self.send()
        except PyFetionSocketError,e:
            log(locals())
            return False

        code = self.get_code(response)
        if code == 280:
            log("Send sms OK!")
        elif code == 200:
            log("Send msg OK!")
        else:
            log(locals())
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

        self.get("SSSetScheduleSms",msg,time,to)
        response = self.send()
        code = self.get_code(response)
        if code == 486:
            log("Busy Here")
            return None
        if code == 200:
            id = re.search('id="(\d+)"',response).group(1)
            log(locals())
            return id


    def alive(self):
        """send keepalive message"""
        self.get("ALIVE",'')
        response = self.send()
        code = self.get_code(response)
        if code == 200:
            log("keepalive message send ok.")
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
                log("logout")
                return
            elif response.startswith("BN"):
                try:
                    type = re.findall('<event type="(.+?)"',response)[0]
                except IndexError:
                    log('response:'+response)
                    

                if type == "ServiceResult":
                    self.set_info(response)
                      
                if type == "deregistered" or type=="disconnect":
                    self.receving = False
                    yield [type]
                if type == "PresenceChanged":
                    self.set_info(response)
                    #uri,mobile_no,name,presence
                    ret = re.findall('<c id=.+? su="(.+?)".+?m="(.*?)".+?n="(.*?)".+?b="(.+?)"',response)
                    if not ret:
                        ret = re.findall('<c id=.+? su="(.+?)".+?m="(.*?)".+?b="(.+?)"',response)


                    log(ret)
                    #remove self uri
                    event = [i for i in ret if i[0] != self.__uri]
                    event = list(set(event))
                    log(event)
                    for e in event:
                        #mobile_no
                        self.contactlist[e[0]][1] = e[1]
                        if len(e) == 4:
                            #name
                            if not self.contactlist[e[0]][0]:
                                self.contactlist[e[0]][0] = e[2]
                            #presence
                            self.contactlist[e[0]][2] = e[3]
                        else:
                            #presence
                            self.contactlist[e[0]][2] = e[2]
                            

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
                    log("Message without content")
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
        ret = ''

        self.get("REG",1,response)
        response = self.send()

        while True:
            self.get("REG",2,response)
            ret = self.send()
            code = self.get_code(ret)
            if code == 200:
                log("register successful.")
                break
            elif code == 421:
                algorithm = re.findall('algorithm="(.+?)"',ret)[0]
                get_pic(algorithm,self)
                continue
            else:
                raise PyFetionRegisterError(code,ret)

        return ret

    def __get_system_config(self):
        global FetionConfigURL
        global FetionConfigXML
        global FetionVer
        url = FetionConfigURL
        body = FetionConfigXML % (self.mobile_no,FetionVer)
        config_data = http_send(url,body).read()
         

        sipc_url = re.search("<ssi-app-sign-in>(.*)</ssi-app-sign-in>",config_data).group(1)
        sipc_proxy = re.search("<sipc-proxy>(.*)</sipc-proxy>",config_data).group(1)
        http_tunnel = re.search("<http-tunnel>(.*)</http-tunnel>",config_data).group(1)
        log(locals())
        self.__sipc_url   = sipc_url
        self._sipc_proxy = sipc_proxy
        self._http_tunnel= http_tunnel
        

    def __get_uri(self):
        url = self.__sipc_url+"?mobileno="+self.mobile_no+"&domains=fetion.com.cn%3bm161.com.cn%3bwww.ikuwa.cn"+"&v4digest-type=1&v4digest="+sha1("fetion.com.cn:"+self.passwd).hexdigest()
        while True:
            try:
                ret = http_send(url,login=True)
            except PyFetionPiccError,e:
                algorithm = re.findall('algorithm="(.+?)"',e[1])[0]
                get_pic(algorithm,self)
                url = url+"&pid="+self.verify_info[2]+"&pic="+self.verify_info[1]+"&algorithm="+algorithm
                continue
            break

        header = str(ret.info())
        body   = ret.read()
        try:
            ssic = re.search("ssic=(.+?);",header).group(1)
            sid  = re.search("sip:(.+?)@",body).group(1)
            uri  = re.search('uri="(.+?)" mobile-no',body).group(1)
            user_id = re.search('user-id="(.+?)"',body).group(1)
            status = re.search('user-status="(\d+)"',body).group(1)
        except:
            return False
        domain = "fetion.com.cn"

        log(locals())
        self.sid = sid
        self.__uri = uri
        self._ssic = ssic
        self._user_id = user_id
        self._domain = domain

        return True

