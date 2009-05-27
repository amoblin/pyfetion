#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Using GPL v2
#Author: cocobear.cn@gmail.com
#Version:0.1

import urllib
import urllib2
import sys,re
import binascii
import hashlib
import socket
import os

from hashlib import md5
from hashlib import sha1
from uuid import uuid1


FetionVer = "2008"
#"SIPP" USED IN HTTP CONNECTION
FetionSIPP= "SIPP"
FetionNavURL = "nav.fetion.com.cn"
FetionConfigURL = "http://nav.fetion.com.cn/nav/getsystemconfig.aspx"

FetionConfigXML = """<config><user mobile-no="%s" /><client type="PC" version="3.2.0540" platform="W5.1" /><servers version="0" /><service-no version="0" /><parameters version="0" /><hints version="0" /><http-applications version="0" /><client-config version="0" /></config>"""

FetionLoginXML = """<args><device type="PC" version="0" client-version="3.2.0540" /><caps value="simple-im;im-session;temp-group;personal-group" /><events value="contact;permission;system-message;personal-group" /><user-info attributes="all" /><presence><basic value="%s" desc="" /></presence></args>"""

proxy_info = False
#uncomment below line if you need proxy
"""
proxy_info = {'user' : '',
              'pass' : '',
              'host' : '218.249.83.87',
              'port' : 8080 
              }
"""
debug = True
COL_NONE = ""
COL_RED  = ""
 
if os.name == 'posix':
    sys_encoding = 'utf-8'
    if debug != "file":
        COL_NONE = "\033[0m"
        COL_RED  = "\033[0;31;48m" 
else:
   sys_encoding = 'cp936'

class PyFetionException(Exception):
    """Base class for all exceptions raised by this module."""

class PyFetionSocketError(PyFetionException):
    """any socket error"""
    def __init__(self, msg):
        self.PyFetion_error = msg
        self.args = ( msg)

class PyFetionResponseException(PyFetionException):
    """Base class for all exceptions that include SIPC/HTTP error code.
    """
    def __init__(self, code, msg):
        self.PyFetion_code = code
        self.PyFetion_error = msg
        self.args = (code, msg)

class PyFetionAuthError(PyFetionResponseException):
    """Authentication error.
    Your password error.
    """

class PyFetionSupportError(PyFetionResponseException):
    """Support error.
    Your phone number don't support fetion.
    """

class PyFetionRegisterError(PyFetionResponseException):
    """RegisterError.
    """
class PyFetionSendError(PyFetionResponseException):
    """Send SMS error
    """

class PyFetion():

    __config_data = ""
    __sipc_url    = ""
    __sipc_proxy  = ""
    __sid = ""
    
    mobile_no = ""
    passwd = ""
    login_type = ""
    login_ok = False

    def __init__(self,mobile_no,passwd,login_type="TCP",debug_type=True):
	global debug
	debug = debug_type
        self.mobile_no = mobile_no
        self.passwd = passwd
        self.login_type = login_type

        self.__get_system_config()
        self.__set_system_config()

    def login(self,see=False):
        (self.__ssic,self.__domain) = self.__get_uri()
        self.__see = see
        try:
            self.__register(self.__ssic,self.__domain)
        except PyFetionRegisterError,e:
            d_print("Register Failed!")
            return
        self.login_ok = True
    def get_offline_msg(self):
        self.__SIPC.get("GetOfflineMessages","")
	response = self.__SIPC.send()

    def add(self,who):
	my_info = self.get_info()
	try:
	    nick_name = re.findall('nickname="(.+?)" ',my_info)[0]
	except IndexError:
	    nick_name = " "
        self.__SIPC.get("INFO","AddBuddy",who,nick_name)
        response = self.__SIPC.send()
        code = self.__SIPC.get_code(response)
        if code == 521:
            d_print("Aleady added.")
        elif code == 522:
            d_print("Mobile NO. Don't Have Fetion")
            self.__SIPC.get("INFO","AddMobileBuddy",who)
            response = self.__SIPC.send()
	return code


    def get_personal_info(self):
        self.__SIPC.get("INFO","GetPersonalInfo")
        self.__SIPC.send()

    def get_info(self,who=None):
        """get one's contact info.
           who should be uri.
           """
        if who == None:
            who = self.__uri
        self.__SIPC.get("INFO","GetContactsInfo",who)
        response = self.__SIPC.send()
        return response


    def get_contact_list(self):
        self.__SIPC.get("INFO","GetContactList")
        response = self.__SIPC.send()
        return response

    def get_uri(self,who):
        if who == self.mobile_no or who in self.__uri:
            return self.__uri

        if who.startswith("sip"):
            return who

        l = self.get_contact_list()
	try:
            all = re.findall('uri="(.+?)" ',l)
	except:
            return None
        #Get uri from contact list, compare one by one
        #I can't get other more effect way.
        for uri in all:
            #who is the fetion number.
            if who in uri:
                return uri
            ret = self.get_info(uri)
	    try:
                no = re.findall('mobile-no="(.+?)" ',ret)
	    except:
		continue
            #if people show you his mobile number.
            if no:
                #who is the mobile number.
                if no[0] == who:
                    d_print(('who',),locals())
                    return uri
        return None

    def send_msg(self,msg,to=None,flag="SENDMSG"):
        """see send_sms.
           if someone's fetion is offline, msg will send to phone,
           the same as send_sms.
           """
        if not to:
            to = self.__uri
        #Fetion now can send use mobile number(09.02.23)
        #like tel: 13888888888
        #but not in sending to PC
        elif flag != "SENDMSG" and len(to) == 11 and to.isdigit():
            to = "tel:"+to

        else:
            to = self.get_uri(to)
            if not to:
                return -1
        self.__SIPC.get(flag,to,msg)
        response = self.__SIPC.send()
        code = self.__SIPC.get_code(response)
        if code == 280:
            d_print("Send sms/msg OK!")
        elif self.__uri == to and code == 200:
            d_print("Send sms/msg OK!")
        elif flag == "SENDMSG" and code == 200:
	    d_print("Send sms/msg OK!")
        else:
            d_print(('code',),locals())
	    return False
        return True

    def send_sms(self,msg,to=None,long=False):
        """send sms to someone, if to is None, send self.
           if long is True, send long sms.(Your phone should support.)
           to can be mobile number or fetion number
           """
        if long:
            return self.send_msg(msg,to,"SENDCatSMS")
        else:
            return self.send_msg(msg,to,"SENDSMS")

    def send_schedule_sms(self,msg,time,to=None):
        if not to:
            to = self.__uri
        elif len(to) == 11 and to.isdigit():
            to = "tel:"+to
        else:
            to = self.get_uri(to)
            if not to:
                return -1

        self.__SIPC.get("SSSetScheduleSms",msg,time,to)
        response = self.__SIPC.send()
        code = self.__SIPC.get_code(response)
        if code == 486:
            d_print("Busy Here")
            return None
        if code == 200:
            id = re.search('id="(\d+)"',response).group(1)
            d_print(('id',),locals(),"schedule_sms id")
            return id

    def __register(self,ssic,domain):
        self.__SIPC = SIPC(self.__sid,self.__domain,self.passwd,self.login_type,self.__http_tunnel,self.__ssic,self.__sipc_proxy,self.__see)
        response = ""
        for step in range(1,3):
                self.__SIPC.get("REG",step,response)
                response = self.__SIPC.send()

        code = self.__SIPC.get_code(response)
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
        self.__config_data = http_send(url,body).read()
            

    def __set_system_config(self):
        sipc_url = re.search("<ssi-app-sign-in>(.*)</ssi-app-sign-in>",self.__config_data).group(1)
        sipc_proxy = re.search("<sipc-proxy>(.*)</sipc-proxy>",self.__config_data).group(1)
        http_tunnel = re.search("<http-tunnel>(.*)</http-tunnel>",self.__config_data).group(1)
        d_print(('sipc_url','sipc_proxy','http_tunnel'),locals())
        self.__sipc_url   = sipc_url
        self.__sipc_proxy = sipc_proxy
        self.__http_tunnel= http_tunnel

    def __get_uri(self):
        url = self.__sipc_url+"?mobileno="+self.mobile_no+"&pwd="+urllib.quote(self.passwd)
        d_print(('url',),locals())
        ret = http_send(url,login=True)

        header = str(ret.info())
        body   = ret.read()
        ssic = re.search("ssic=(.*);",header).group(1)
        sid  = re.search("sip:(.*)@",body).group(1)
        uri  = re.search('uri="(.*)" mobile-no',body).group(1)
        status = re.search('user-status="(\d+)"',body).group(1)
        domain = "fetion.com.cn"

        d_print(('ssic','sid','uri','status','domain'),locals(),"Get SID OK")
        self.__sid = sid
        self.__uri = uri
        return (ssic,domain)

class SIPC():

    global FetionVer
    global FetionSIPP
    global FetionLoginXML

    header = ""
    body = ""
    content = ""
    code = ""
    ver  = "SIP-C/2.0"
    ID   = 1
    sid  = ""
    domain = ""
    passwd = ""
    see    = True
    __http_tunnel = ""

    def __init__(self,sid,domain,passwd,login_type,http_tunnel,ssic,sipc_proxy,see):
        self.sid = sid
        self.domain = domain
        self.passwd = passwd
        self.login_type = login_type
        self.domain = domain
        self.sid = sid
        self.__seq = 1
        self.__sipc_proxy = sipc_proxy
        self.__see = see
        if self.login_type == "HTTP":
            self.__http_tunnel = http_tunnel
            self.__ssic = ssic
            guid = str(uuid1())
            self.__exheaders = {
                 'Cookie':'ssic=%s' % self.__ssic,
                 'Content-Type':'application/oct-stream',
                 'Pragma':'xz4BBcV%s' % guid,
                 }
     
    def init(self,type):
        self.content = '%s %s %s\r\n' % (type,self.domain,self.ver)
        self.header = [('F',self.sid),
                       ('I',self.ID),
                       ('Q','1 %s' % type),
                      ]

    def send(self):
        content = self.content 
        d_print(('content',),locals())
        if self.login_type == "HTTP":
            #First time t SHOULD SET AS 'i'
            #Otherwise 405 code get
            if self.__seq == 1:
                t = 'i'
            else:
                t = 's'
            url = self.__http_tunnel+"?t=%s&i=%s" % (t,self.__seq)
            ret = http_send(url,content,self.__exheaders)
            response = ret.read()
            self.__seq+=1
            response = self.__sendSIPP()
            #This line will enhance the probablity of success.
            #Sometimes it will return FetionSIPP twice.
            #Probably you need add more
            if response == FetionSIPP:
                response = self.__sendSIPP()
        else:
            if self.__seq == 1:
                self.__tcp_init()
            self.__tcp_send(content)
            response = self.__tcp_recv()
            d_print(('response',),locals())
            self.__seq+=1

        code = self.get_code(response)
        d_print(('code',),locals())
        return response


 
    def get_code(self,response):
        try:
            self.code =int(re.search("%s (\d{3})" % self.ver,response).group(1))
            self.msg  =re.search("%s \d{3} (.*)\r" % self.ver,response).group(1)
            d_print(('self.code','self.msg',),locals())
            return self.code
        except AttributeError,e:
	    self.cmd = re.search("(.+?) %s" % self.ver,response).group(1)
	    d_print(('self.cmd',),locals())
            return self.cmd
 
    def get(self,cmd,arg,ret="",extra=""):
        body = ret
        if cmd == "REG":
            if self.__see:
                body = FetionLoginXML % "400"
            else:
                body = FetionLoginXML % "0"
            self.init('R')
            if arg == 1:
                pass
            if arg == 2:
                nonce = re.search('nonce="(.*)"',ret).group(1)
                cnonce = self.__get_cnonce()
                if FetionVer == "2008":
                    response=self.__get_response_sha1(nonce,cnonce)
                elif FetionVer == "2006":
                    response=self.__get_response_md5(nonce,cnonce)
                salt = self.__get_salt()
                d_print(('nonce','cnonce','response','salt'),locals())
                #If this step failed try to uncomment this lines
                #del self.header[2]
                #self.header.insert(2,('Q','2 R'))
                if FetionVer == "2008":
                    self.header.insert(3,('A','Digest algorithm="SHA1-sess",response="%s",cnonce="%s",salt="%s"' % (response,cnonce,salt)))
                elif FetionVer == "2006":
                    self.header.insert(3,('A','Digest response="%s",cnonce="%s"' % (response,cnonce)))
            #If register successful 200 code get 
            if arg == 3:
                return self.code

        if cmd == "SENDMSG":
            self.init('M')
            self.header.insert(3,('T',arg))
            self.header.insert(4,('C','text/plain'))
            self.header.insert(5,('K','SaveHistory'))
        
        if cmd == "SENDSMS":
            self.init('M')
            self.header.append(('T',arg))
            self.header.append(('N','SendSMS'))

        if cmd == "SENDCatSMS":
            self.init('M')
            self.header.append(('T',arg))
            self.header.append(('N','SendCatSMS'))

        if cmd == "SSSetScheduleSms":
            self.init('S')
            self.header.insert(3,('N',cmd))
            body = '<args><schedule-sms send-time="%s"><message>%s</message><receivers><receiver uri="%s" /></receivers></schedule-sms></args>' % (ret,arg,extra)
	if cmd == "GetOfflineMessages":
            self.init('S')
	    self.header.insert(3,('N',cmd))
	    
        if cmd == "INFO":
            self.init('S')
            self.header.insert(3,('N',arg))
            if arg == "GetPersonalInfo":
                body = '<args><personal attributes="all" /><services version="" attributes="all" /><config version="33" attributes="all" /><mobile-device attributes="all" /></args>'
            elif arg == "GetContactList":
                body = '<args><contacts><buddy-lists /><buddies attributes="all" /><mobile-buddies attributes="all" /><chat-friends /><blacklist /></contacts></args>'
            elif arg == "GetContactsInfo":
                body = '<args><contacts attributes="all"><contact uri="%s" /></contacts></args>' % ret
            elif arg == "AddBuddy":
                body = '<args><contacts><buddies><buddy uri="tel:%s" buddy-lists="" desc="%s" expose-mobile-no="1" expose-name="1" /></buddies></contacts></args>' % (ret,extra)
            elif arg == "AddMobileBuddy":
                body = '<args><contacts><mobile-buddies><mobile-buddy uri="tel:%s" buddy-lists="1" desc="THis message is send by PyFetion" invite="0" /></mobile-buddies></contacts></args>' % ret


        
        #general SIPC info
        self.header.append(('L',len(body)))
        for k in self.header:
            self.content = self.content + k[0] + ": " + str(k[1]) + "\r\n"
        self.content+="\r\n"
        self.content+= body
        if self.login_type == "HTTP":
            #IN TCP CONNECTION "SIPP" SHOULD NOT BEEN SEND
            self.content+= FetionSIPP
        return self.content


    def __sendSIPP(self):
        body = FetionSIPP
        url = self.__http_tunnel+"?t=s&i=%s" % self.__seq
        response = http_send(url,body,self.__exheaders).read()
        d_print(('response',),locals())
        self.__seq+=1
        return response

    def __tcp_init(self):
        try:
            self.__sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error,e:
            s = None
            raise PyFetionSocketError(e.read())
        (host,port) = tuple(self.__sipc_proxy.split(":"))
        port = int(port)
        try:
            self.__sock.connect((host,port))
        except socket.error,e:
            self.__sock.close()
            raise PyFetionSocketError(e.read())


    def __tcp_send(self,msg):
        try:
            self.__sock.send(msg)
        except socket.error,e:
            self.__sock.close()
            raise PyFetionSocketError(e.read())

    def __tcp_recv(self):
        """read buf_size bytes first,if there's still more data, read left data.
           get length from header :
           L: 1022 
        """
        total_data = []
        buf_size = 1024
        try:
            data = self.__sock.recv(buf_size)
            total_data.append(data)
            if "\r\n\r\n" == data[-4:]:
                pass
            elif re.search("L: (\d+)",data):
                match = re.search("L: (\d+)",data)
                body_len = int(match.group(1))
                header_len =  match.end() + 4
                if len(data) != body_len + header_len:
                    print body_len,len(data)
                    left = body_len + header_len - len(data)
                    self.__sock.settimeout(2)
                    data = ""
                    while True:
                        recv_size = max(buf_size,left)
                        data = self.__sock.recv(recv_size)
                        if not data:
                            break
                        total_data.append(data)
                        n = len(data)
                        if n >= left:
                            break
                        left = left - n
            else:
                raise PyFetionSocketError("SHOULD NOT happened.")
        except socket.error,e:
            self.__sock.close()
            raise PyFetionSocketError(e)
        return "".join(total_data)



    def __get_salt(self):
        return self.__hash_passwd()[:8]

    def __get_cnonce(self):
        return md5(str(uuid1())).hexdigest().upper()

    def __get_response_md5(self,nonce,cnonce):
        #nonce = "3D8348924962579418512B8B3966294E"
        #cnonce= "9E169DCA9CBD85F1D1A89A893E00917E"
        key = md5("%s:%s:%s" % (self.sid,self.domain,self.passwd)).digest()
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
        key = sha1("%s:%s:%s" % (self.sid,self.domain,hash_passwd_str)).digest()
        h1  = md5("%s:%s:%s" % (key,nonce,cnonce)).hexdigest().upper()
        h2  = md5("REGISTER:%s" % self.sid).hexdigest().upper()
        response = md5("%s:%s:%s" % (h1,nonce,h2)).hexdigest().upper()
        return response

    def __hash_passwd(self):
        #salt = '%s%s%s%s' % (chr(0x77), chr(0x7A), chr(0x6D), chr(0x03))
        salt = 'wzm\x03'
        src  = salt+sha1(self.passwd).digest()
        return "777A6D03"+sha1(src).hexdigest().upper()

def http_send(url,body="",exheaders="",login=False):
    global proxy_info
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
                code = e.errno
                msg = e.reason
            d_print(('code','msg'),locals())
            if code == 401:
                if login:
                    raise PyFetionAuthError(code,msg)
            if code == 404:
                raise PyFetionSupportError(code,msg)
            if code == 405:
                retry = retry - 1
                continue
            raise PyFetionSocketError(msg)
        break
    
    return conn

def d_print(vars=(),namespace=[],msg=""):
    """if only sigle variable use like this ('var',)"""
    global debug
    if not debug:
        return
    if debug == "file":
        log_file = file("pyfetion.log","a")
        stdout_old = sys.stdout
        sys.stdout = log_file
    if vars and not namespace and not msg:
        msg = vars
    if vars and namespace:
        for var in vars:
            if var in namespace:
                print "[PyFetion]:%s%s%s[" % (COL_RED,var,COL_NONE),
                print str(namespace[var]).decode('utf-8').encode(sys_encoding)+"]"
    if msg:
        print "[PyFetion]:%s %s %s" % (COL_RED,msg,COL_NONE)
    if debug == "file" and log_file:
        log_file.close()
        sys.stdout = stdout_old


def main(argv=None):
    phone = PyFetion("13619861986","123456","TCP")
    try:
        phone.login()
    except PyFetionSupportError,e:
        print u"手机号未开通飞信".encode(sys_encoding)
        return 1
    except PyFetionAuthError,e:
        print u"手机号密码错误".encode(sys_encoding)
        return 2

    if phone.login_ok:
        print u"登录成功".encode(sys_encoding)
    phone.get_offline_msg()
    #phone.get_info()
    phone.add("13619861986")
    #phone.get_personal_info()
    #phone.get_contact_list()
    #ret = phone.send_sms("Hello<cocobear.info ")
    phone.send_msg("cocobear.info","782079728")
    #phone.send_schedule_sms("请注意，这个是定时短信",time)
    #time_format = "%Y-%m-%d %H:%M:%S"
    #time.strftime(time_format,time.gmtime())
    
if __name__ == "__main__":
    sys.exit(main())
