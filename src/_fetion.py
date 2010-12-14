#! /usr/bin/env python
# -*- coding: utf-8 -*-
#MIT License
#By : cocobear.cn@Gmail.com
#Ver:0.2

from PyFetion import *
from threading import Thread
from time import sleep
from copy import copy
import time
import sys
import exceptions


status = {FetionHidden:"短信",FetionOnline:"在线",FetionBusy:"忙碌",FetionAway:"离开",FetionOffline:"离线"}

class fetion_recv(Thread):
    def __init__(self,phone):
        self.phone = phone
        Thread.__init__(self)

    def run(self):
        #self.phone.get_offline_msg()
        global status
        start_time = time.time()
        s = {"PC":"电脑","PHONE":"手机"}

        #状态改变等消息在这里处理 收到的短信或者消息在recv中处理
        for e in self.phone.receive():
            #print e
            if e[0] == "PresenceChanged":
                #在登录时BN消息(e)有可能含有多个uri 
                for i in e[1]:
                    if time.time() - start_time > 5:
                        printl('')
                        printl("%s [%s]" % (self.phone.contactlist[i[0]][0],status[i[1]]))
                        
            elif e[0] == "Message":
                #获得消息
                #系统广告 忽略之
                if e[1] not in self.phone.contactlist:
                    continue
                printl('')
                printl("%s从%s发来:%s" % (self.phone.contactlist[e[1]][0],s[e[3]],e[2]))
                printl('')
            elif e[0] == "deregistered":
                self.phone.receving = False
                printl('')
                printl("您从其它终端登录")

            elif e[0] == "NetworkError":
                printl("网络通讯出错:%s"%e[1])
                self.phone.receving = False

        printl("停止接收消息")

class fetion_alive(Thread):
    def __init__(self,phone):
        self.phone = phone
        Thread.__init__(self)

    def run(self):
        last_time = time.time()
        while self.phone.receving:
            sleep(3)
            if time.time() - last_time  > 300:
                last_time = time.time()
                self.phone.alive()

        printl("停止发送心跳")

class fetion_input(Thread):
    def __init__(self,phone):
        self.phone = phone
        self.to    = ""
        self.type  = "SMS"
        self.hint  = "PyFetion:"
        Thread.__init__(self)

    def run(self):
        sleep(1)
        self.help()
        while self.phone.receving:
            try:
                self.hint = toEcho(self.hint)
            except :
                pass

            self.cmd(raw_input(self.hint))
        printl("退出输入状态")

    def cmd(self,arg):
        global status

        if not self.phone.receving:
            return
        cmd = arg.strip().lower().split(' ')
        if cmd[0] == "":
            return
        elif cmd[0] == "quit" or cmd[0] == "q":
            self.to = ""
            self.hint = "PyFetion:"


        elif self.to == "ME":
            self.phone.send_sms(toUTF8(arg))

        elif self.to:
            if self.type == "SMS":
                if not self.phone.send_sms(toUTF8(arg),self.to):
                    printl("发送短信失败")
            else:
                if self.to in self.phone.session:
                    self.phone.session[self.to]._send_msg(toUTF8(arg))
                    return
                if not self.phone.send_msg(toUTF8(arg),self.to):
                    printl("发送消息失败")
                
            return

        elif cmd[0] == "help" or cmd[0] == "h" or cmd[0] == '?':
            #显示帮助信息
            self.help()
        elif cmd[0] == "status" or cmd[0] == "st":
            #改变飞信的状态
            if len(cmd) != 2:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return

            try:
                i = int(cmd[1])
            except exceptions.ValueError:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return

            if i >3 or i < 0:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return
                
            if self.phone.presence == status.keys()[i]:
                return
            else:
                self.phone.set_presence(status.keys()[i])
                
        elif cmd[0] == "sms" or cmd[0] == 'msg' or cmd[0] == 's' or cmd[0] == 'm' or cmd[0] == "find" or cmd[0] == 'f':
            #发送短信或者消息
            s = {"MSG":"消息","SMS":"短信","FIND":"查询"}
            if len(cmd) == 1 and cmd[0].startswith('s'):
                self.hint = "给自己发短信:"
                self.to = "ME"
                return
            if len(cmd) != 2:
                printl("命令格式:sms[msg] 编号[手机号]")
                return

            if cmd[0].startswith('s'):
                self.type = "SMS"
            elif cmd[0].startswith('m'):
                self.type = "MSG"
            else:
                self.type = "FIND"
            self.to   = ""
 
            try:
                int(cmd[1])
            except exceptions.ValueError:
                if cmd[1].startswith("sip"):
                    self.to = cmd[1]
                    self.hint = "给%s发%s:" % (cmd[1],s[self.type])
                else:
                    printl("命令格式:sms[msg] 编号[手机号]")
                    return
           
            #使用编号作为参数
            if len(cmd[1]) < 4:
                n = int(cmd[1])
                if n >= 0 and n < len(self.phone.contactlist):
                    self.to = self.phone.contactlist.keys()[n]
                    self.hint = "给%s发%s:" % (self.phone.contactlist[self.to][0],s[self.type])
                else:
                    printl("编号超出好友范围")

            #使用手机号作为参数
            elif len(cmd[1]) == 11:
                for c in self.phone.contactlist.items():
                    if c[1][1] == cmd[1]:
                        self.to = c[0]
                        self.hint = "给%s发%s:" % (c[1][0],s[self.type])

                if not self.to:
                    printl("手机号不是您的好友")

            else:
                printl("不正确的好友")


            if self.type == "FIND":
                #如果好友显示为在线(包括忙碌等) 则不查询
                if self.phone.contactlist[self.to][2] != FetionHidden:
                    printl("拜托人家写着在线你还要查!")
                else:
                    ret = self.phone.start_chat(self.to)
                    if ret:
                        if ret == self.phone.contactlist[self.to][2]:
                            printl("该好友果然隐身")
                        elif ret == FetionOnline:
                            printl("该好友的确不在线哦")
                    else:
                        printl("获取隐身信息出错")

                self.to = ""
                self.type = "SMS"
                self.hint  = "PyFetion:"
                    
            
        elif cmd[0] == "ls" or cmd[0] == "l":
            #显示好友列表
            buddys = self.phone.get_contactlist()
            if not buddys:
                printl("没有好友")
                return

            for i in buddys:
                if buddys[i][0] == '':
                    buddys[i][0] = i[4:4+9]

            for i in range(len(buddys)):
                printl("%-4d%-8s%-20s" % (i,status[buddys[buddys.keys()[i]][2]],buddys[buddys.keys()[i]][0],))



        elif cmd[0] == "add" or cmd[0] == 'a':
            if len(cmd) != 2:
                printl("命令格式:add[a] 手机号或飞信号")
                return

            if cmd[1].isdigit() and len(cmd[1]) == 9 or len(cmd[1]) == 11:
                
                code = self.phone.add(cmd[1])
                if code:
                    printl("添加%s成功"%cmd[1])
                else:
                    printl("添加%s失败"%cmd[1])
                    
            else:
                printl("命令格式:add[a] 手机号或飞信号")
                return
                
        elif cmd[0] == "del" or cmd[0] == 'd':
            if len(cmd) != 2:
                printl("命令格式:del[d] 手机号或飞信号")
                return
            if cmd[1].isdigit() and len(cmd[1]) == 9 or len(cmd[1]) == 11:
                code = self.phone.delete(cmd[1])
                if code:
                    printl("删除%s成功"%cmd[1])
                else:
                    printl("删除%s失败"%cmd[1])
            else:
                printl("命令格式:del[d] 手机号或飞信号")
                return

        elif cmd[0] == "get":
            self.phone.get_offline_msg()
        elif cmd[0] == "cls" or cmd[0] == 'c':
            #清屏
            self.clear()

        elif cmd[0] == "exit" or cmd[0] == 'x':
            self.phone.logout()

        else:
            printl("不能识别的命令 请使用help")

    def clear(self):
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")

    def help(self):
        self.clear()
        printl("""
------------------------基于PyFetion的一个CLI飞信客户端-------------------------

        命令不区分大小写中括号里为命令的缩写

        help[?]           显示本帮助信息
        ls[l]             列出好友列表
        status[st]        改变飞信状态 参数[0隐身 1离开 2忙碌 3在线]
                          参数为空显示自己的状态
        msg[m]            发送消息 参数为序号或手机号 使用quit退出
        sms[s]            发送短信 参数为序号或手机号 使用quit退出
                          参数为空给自己发短信
        find[f]           查看好友是否隐身 参数为序号或手机号
        add[a]            添加好友 参数为手机号或飞信号
        del[d]            删除好友 参数为手机号或飞信号
        cls[c]            清屏
        quit[q]           退出对话状态
        exit[x]           退出飞信

        """)



class progressBar(Thread):
    def __init__(self):
        self.running = True
        Thread.__init__(self)

    def run(self):
        i = 1
        n = 10
        while self.running:
            sys.stderr.write('\r')
            i = i % n
            sys.stderr.write('='*i)
            sys.stderr.write('>')
            sys.stderr.write('='*(n-i))
            sleep(0.5)
            i += 1

    def stop(self):
        self.running = False


def toUTF8(str):
    return str.decode((os.name == 'posix' and 'utf-8' or 'cp936')).encode('utf-8')

def toEcho(str):
    return str.decode('utf-8').encode((os.name == 'posix' and 'utf-8' or 'cp936'))

def printl(msg):
    msg = str(msg)
    try:
        print(msg.decode('utf-8'))
    except exceptions.UnicodeEncodeError:
        print(msg)

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
    
    

def main(argv=None):
    
    mobile_no = raw_input(toEcho("手机号:"))
    passwd = getpass(toEcho("口  令:"))

    phone = PyFetion(mobile_no,passwd,"TCP",debug="FILE")
    try:
        t = progressBar()
        t.start()
        #可以在这里选择登录的方式[隐身 在线 忙碌 离开]
        ret = phone.login(FetionOnline)
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
        pass
        t.stop()

    if ret:
        printl("登录成功")
    else:
        printl("登录失败")
        return 1

    threads = []
    threads.append(fetion_recv(phone))
    threads.append(fetion_alive(phone))
    #threads.append(fetion_input(phone))
    t1 = fetion_input(phone)
    t1.setDaemon(True)
    t1.start()
    for t in threads:
        t.setDaemon(True)
        t.start()

    while len(threads):
        t = threads.pop()
        if t.isAlive():
            t.join()
    del t1
    printl("飞信退出")

    #phone.send_schedule_sms("请注意，这个是定时短信",time)
    #time_format = "%Y-%m-%d %H:%M:%S"
    #time.strftime(time_format,time.gmtime())
    
if __name__ == "__main__":
    sys.exit(main())

