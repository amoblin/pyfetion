#!/usr/bin/env python
#-*- coding:utf-8 -*-

#By: amoblin@gmail.com

import sys,os,string,re

from PyFetion import *
userhome = os.path.expanduser('~')

ISOTIMEFORMAT='%Y-%m-%d %H:%M:%S'
status = {FetionHidden:"短信在线",FetionOnline:"在线",FetionBusy:"忙碌",FetionAway:"离开",FetionOffline:"离线"}

class FetionRobot(Thread):
    """飞信机器人"""
    def __init__(self,name):
        Thread.__init__(self)
        self.home = os.path.join(userhome,'.'+name)
        self.file = os.path.join(self.home,name+'.txt')
        self.config()
        self.phone = ""
        self.threads = []

    def run(self):
        self.login()
        try:
            self.monitor()
        except KeyboardInterrupt:
            self.phone.logout()
            sys.exit(0)
            print "飞信退出"

    def monitor(self):
        self.threads.append(fetion_recv(self.phone))
        self.start_threads()

    def start_threads(self):
        for t in self.threads:
            t.setDaemon(True)
            t.start()

        while len(self.threads):
            t = self.threads.pop()
            if t.isAlive():
                t.join()

    def print_info(self):
        time.sleep(2)
        print "启动飞信机器人守护进程。"
        #print phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        for i in range(num):
            uri = c.keys()[i]
            if c[uri][2] != FetionHidden and c[uri][2] != FetionOffline and c[uri][2] != "":
                outstr = "[" + str(i) + "]" + c[uri][0]
                print outstr,":",status[c[uri][2]],"\t",
        print ""

    def config(self):
        if not os.path.isdir(self.home):
            os.mkdir(self.home)
        if not os.path.exists(self.file):
            file = open(self.file,'w')
            content = "#该文件由pyfetion生成，请勿随意修改\n#tel=12345678910\n#password=123456\n"
            content +="隐身=蓝色\n离开=青蓝色\n离线=紫红色\n忙碌=红色\n在线=绿色\n"
            content +="颜色和linux终端码的对应参照http://www.chinaunix.net/jh/6/54256.html"
            file.write(content)
            file.close()
            if not os.path.exists(self.file):
                print u'创建文件失败'
            else:
                print u'创建文件成功'

    def login(self):
        '''登录设置'''
        try:
            confile = open(self.file,'r')
            lines = confile.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                if line.startswith("tel"):
                    mobile_no = line.split("=")[1][:-1]
                elif line.startswith("password"):
                    passwd = line.split("=")[1]
            self.phone = PyFetion(mobile_no,passwd,"TCP",debug="True")
        except:
            mobile_no = raw_input(toEcho("手机号:"))
            passwd = getpass(toEcho("口  令:"))
            save = raw_input(toEcho("是否保存手机号和密码以便下次自动登录(y/n)?"))
            if save == 'y':
                confile = open(self.file,'w')
                content = "#该文件由pyfetion生成，请勿随意修改\n"
                content = content +  "tel=" + mobile_no
                content = content + "\npassword=" + passwd
                confile.write(content)
                confile.close()

            self.phone = PyFetion(mobile_no,passwd,"TCP",debug="FALSE")

        try:
            t = progressBar()
            t.start()

            ret = self.phone.login(FetionOnline)
        except PyFetionSupportError,e:
            printl("手机号未开通飞信")
            return 1
        except PyFetionAuthError,e:
            printl("手机号密码错误")
            return 1
        except PyFetionSocketError,e:
            print(e.msg)
            printl("网络通信出错 请检查网络连接")
            return 1
        finally:
            t.stop()

        if not ret:
            print "登录失败"
            return 1

        if not self.phone.contactlist:
            print "没有好友"
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()


        self.threads.append(fetion_alive(self.phone))

class fetion_recv(Thread):
    '''receive message'''
    def __init__(self,phone):
        Thread.__init__(self)
        self.phone = phone
        self.libkeywords = {}

    def run(self):
        global status
        start_time = time.time()

        #状态改变等消息在这里处理 收到的短信或者消息在recv中处理
        for e in self.phone.receive():
            if e[0] == "Message":
                """获得消息系统广告 忽略之"""
                if e[1] not in self.phone.contactlist:
                    continue
                self.parser_cmd(e[1],e[2])
                #self.save_chat(e[1],e[2])
            elif e[0] == "PresenceChanged":
                if self.phone.newsip:
                    self.welcome()
                    self.phone.newsip=''
            elif e[0] == "deregistered":
                self.phone.receving = False
                printl('')
                printl("您从其它终端登录")

            elif e[0] == "NetworkError":
                printl("网络通讯出错:%s"%e[1])
                self.phone.receving = False

        printl("停止接收消息")

    def welcome(self):
        num = len(self.phone.contactlist.items())
        message = u"欢迎第"+num.decode('utf-8')+u"位好友！\n"
        print message
        self.phone.send_msg(message.encode('utf-8'),uri)

        nickname = self.phone.contactlist[self.phone.newsip][0]
        message = u"添加好友："+nickname.decode('utf-8')
        self.phone.send_msg(message.encode('utf-8'),"sip:856882346@fetion.com.cn;p=5911")

    def parser_cmd(self,to,line):
        message=time.ctime()
        nickname = self.phone.contactlist[to][0]
        if line[0]=='-':
            cmd = line[1:]
            message += " cmd:"+cmd
        else:
            message += "Text:" + line
        print message

    def get_sip(self,num):
        '''get sip and nickname from phone number or order or fetion number'''
        c = copy(self.phone.contactlist)
        if not num.isdigit():
            '''昵称形式'''
            for uri in c.keys():
                if num == c[uri][0]:
                    return uri
            return
        if len(num)==11:
            '''cellphone number'''
            sip = ""
            for c in c.items():
                if c[1][1] == num:
                    sip=c[0]
                    return sip
            if not sip:
                printl("手机号不是您的好友")
        elif len(num) == 9:
            '''fetion number'''
            for uri in c.keys():
                if num == self.get_fetion_number(uri):
                    return uri
        elif len(num) < 4:
            '''order number'''
            n = int(num)
            if n >= 0 and n < len(c):
                return c.keys()[n]
            else:
                printl("编号超出好友范围")

    def get_fetion_number(self,uri):
        '''get fetion number from uri'''
        return uri.split("@")[0].split(":")[1]

    def save_chat(self,sip,text):
        '''日志保存'''
        command_log_file = os.path.join(config_folder,"librot.log")
        file = open(command_log_file,"a")
        record = self.phone.contactlist[sip][0] + "(" + sip.split("@")[0].split(":")[1] + ") " + time.strftime(ISOTIMEFORMAT) + " " + text + "\n"
        file.write(record)
        file.close()

class fetion_alive(Thread):
    '''keep alive'''
    def __init__(self,phone):
        self.phone = phone
        Thread.__init__(self)

    def run(self):
        last_time = time.time()
        while self.phone.receving:
            time.sleep(3)
            if time.time() - last_time  > 300:
                last_time = time.time()
                self.phone.alive()

        print "停止发送心跳"

class progressBar(Thread):
    """进度栏"""
    def __init__(self):
        self.running = True
        Thread.__init__(self)

    def run(self):
        i = 1
        while self.running:
            sys.stderr.write('\r')
            sys.stderr.write('-'*i)
            sys.stderr.write('>')
            time.sleep(0.5)
            i += 1

    def stop(self):
        self.running = False

def toUTF8(str):
    return str.decode(('cp936')).encode('utf-8')

def printl(msg):
    msg = str(msg)
    try:
        print(msg.decode('utf-8'))
    except exceptions.UnicodeEncodeError:
        print(msg)

def toEcho(str):
    return str.decode('utf-8').encode((os.name == 'posix' and 'utf-8' or 'cp936'))

def getpass(msg):
    """实现一个命令行下的密码输入界面"""
    passwd = ""
    sys.stdout.write(msg)
    ch = getch()
    while (ch != '\r'):
        #Linux下得到的退格键值是\x7f 不理解
        if ch == '\b' or ch == '\x7f':
            passwd = passwd[:-1]
        else:
            passwd += ch
        sys.stdout.write('\r')
        sys.stdout.write(msg)
        sys.stdout.write('*'*len(passwd))
        sys.stdout.write(' '*(80-len(msg)-len(passwd)-1))
        sys.stdout.write('\b'*(80-len(msg)-len(passwd)-1))
        ch = getch()

    sys.stdout.write('\n')
    return passwd

def getch():
    if os.name == 'posix':
        import sys,tty,termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

        return ch

    elif os.name == 'nt':
        import msvcrt
        return msvcrt.getch()

if __name__ == "__main__":
    robot = FetionRobot("fetionrobot")   #飞信机器人守护
    robot.setDaemon(True)
    robot.start()
    robot.print_info()
    while(True):
        time.sleep(10)
        pass
