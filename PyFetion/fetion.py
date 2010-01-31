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
import cmd,wave
#from PIL import ImageGrab

ISOTIMEFORMAT='%Y-%m-%d %X'

status = {FetionHidden:"短信在线",FetionOnline:"在线",FetionBusy:"忙碌",FetionAway:"离开",FetionOffline:"离线"}

class fetion_recv(Thread):
    '''receive message'''
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
                        printl("%s(%s) [%s]" % (self.phone.contactlist[i[0]][0],self.phone.get_order(i[0]),status[i[1]]))

                        #pynotify.init("Some Application or Title")
                        #self.notification = pynotify.Notification(self.phone.contactlist[i[0]][0], status[i[1]], "dialog-warning")
                        #self.notification.set_urgency(pynotify.URGENCY_NORMAL)
                        #self.notification.set_timeout(1)
                        #self.notification.show()

                        
            elif e[0] == "Message":
                #获得消息
                #系统广告 忽略之
                if e[1] not in self.phone.contactlist:
                    continue
                printl('')
                printl("%s(%s)从%s发来:%s" % (self.phone.contactlist[e[1]][0],self.phone.get_order(e[1]),s[e[3]],e[2]))
                printl('')
                
                self.save_chat(e[1],e[2])

                #pynotify.init("Some Application or Title")
                #self.notification = pynotify.Notification(self.phone.contactlist[e[1]][0], e[2], "dialog-warning")
                #self.notification.set_urgency(pynotify.URGENCY_NORMAL)
                #self.notification.set_timeout(1)
                #self.notification.show()

            elif e[0] == "deregistered":
                self.phone.receving = False
                printl('')
                printl("您从其它终端登录")

            elif e[0] == "NetworkError":
                printl("网络通讯出错:%s"%e[1])
                self.phone.receving = False

        printl("停止接收消息")

    def save_chat(self,sip,text):
        file = open("chat_history.dat","a")
        record = sip + " " + time.strftime(ISOTIMEFORMAT) + " " + text + "\n"
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
            sleep(3)
            if time.time() - last_time  > 300:
                last_time = time.time()
                self.phone.alive()

        printl("停止发送心跳")

class CLI(cmd.Cmd):
    '''解析命令行参数'''
    def __init__(self,phone):
        global status
        cmd.Cmd.__init__(self)
        self.phone=phone
        self.to=""
        self.type="msg"
        self.nickname = self.phone.get_personal_info()[0]
        self.sta="\033[32m" + self.nickname + "\033[0m"
        self.prompt = self.sta + ">"

    def default(self, line):
        '''会话中：快速发送消息'''
        c = copy(self.phone.contactlist)
        if self.to:
            if self.phone.send_msg(toUTF8(line),self.to):
                print u'send to ',c[self.to][0]
                self.save_chat(self.to,line)
            else:
                printl("发送消息失败")
        else:
            print line, u' 不支持的命令!'

    def do_test(self,line):
        if not line:
            return

    def do_info(self,line):
        '''用法：info
            查看个人信息'''
        info = self.phone.get_personal_info()
        print u"昵称：",info[0]
        print u"状态：",info[1]

    def do_la(self,line):
        '''用法:ls\n显示所有好友列表.'''
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        printl(status[FetionOnline])
        for i in range(num):
            if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                #printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))
                print "\033[32m",str(i),c[c.keys()[i]][0],"\t",
        print "\033[0m"

        printl(status[FetionHidden])
        outstr = ""
        for i in range(num):
            if c[c.keys()[i]][2] == FetionHidden:
                #printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))
                print "\033[35m",str(i),c[c.keys()[i]][0],"\t",
        print ""

        printl(status[FetionOffline])
        outstr = ""
        for i in range(num):
            if c[c.keys()[i]][2] == FetionOffline:
                #printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))
                print "\033[36m",str(i),c[c.keys()[i]][0],"\t",
        print ""

    def do_ls(self,line):
        '''用法: ls\n 显示在线好友列表'''
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        for i in range(num):
            if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                print u"\033[32m",str(i),c[c.keys()[i]][0],"\t",
        print "\033[0m"

    def do_ll(self,line):
        '''用法: ll\n列出好友详细信息:序号，昵称，手机号，状态.'''
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        for i in range(num):
            if c[c.keys()[i]][2] == FetionHidden:
                printl("\033[35m%-4d\t%-20s\t%-11s\t%-4s\033[0m" % (i,c[c.keys()[i]][0],c[c.keys()[i]][1],status[c[c.keys()[i]][2]]))
            elif c[c.keys()[i]][2] == FetionAway:
                printl("\033[34m%-4d\t%-20s\t%-11s\t%-4s\033[0m" % (i,c[c.keys()[i]][0],c[c.keys()[i]][1],status[c[c.keys()[i]][2]]))
            elif c[c.keys()[i]][2] == FetionOffline:
                printl("\033[36m%-4d\t%-20s\t%-11s\t%-4s\033[0m" % (i,c[c.keys()[i]][0],c[c.keys()[i]][1],status[c[c.keys()[i]][2]]))
            elif c[c.keys()[i]][2] == FetionBusy:
                printl("\033[31m%-4d\t%-20s\t%-11s\t%-4s\033[0m" % (i,c[c.keys()[i]][0],c[c.keys()[i]][1],status[c[c.keys()[i]][2]]))
            elif c[c.keys()[i]][2] == FetionOnline:
                printl("\033[32m%-4d\t%-20s\t%-11s\t%-4s\033[0m" % (i,c[c.keys()[i]][0],c[c.keys()[i]][1],status[c[c.keys()[i]][2]]))

    def do_status(self,i):
        '''用法: status [i]\n改变状态:0 隐身 1 离开 2 离线 3 忙碌 4 在线.'''
        if i:
            i = int(i)
            self.phone.set_presence(status.keys()[i])
            color=""
            if i==0:
                '''FetionHidden'''
                self.sta= "\033[35m" + self.nickname  + "\033[0m"
            elif i == 1:
                '''FetionAway'''
                self.sta= "\033[34m" + self.nickname + "\033[0m"
            elif i == 2:
                '''FetionOffline'''
                self.sta= "\033[36m" + self.nickname + "\033[0m"
            elif i == 3:
                '''FetionBusy'''
                self.sta= "\033[31m" + self.nickname + "\033[0m"
            elif i == 4:
                '''FetionOnline'''
                self.sta= "\033[32m" + self.nickname + "\033[0m"
            self.prompt = self.sta + ">"
        else:
            print status[self.phone.presence],u"\n用法: status [i]\n改变状态:0 隐身 1 离开 2 离线 3 忙碌 4 在线."

    def do_msg(self,line):
        """msg [num] [text]
        send text to num and save the session"""
        if not line:
            print u'用法：msg [num] [text]'
            return
        cmd = line.split()
        num = cmd[0]

        self.to = self.get_sip(num)
        nickname = self.get_nickname(self.to)
        self.prompt = self.sta +" [to] "+nickname+">"
        if len(cmd)>1:
            if self.phone.send_msg(toUTF8(cmd[1]),self.to):
                self.save_chat(self.to,cmd[1])
                print u'send message to ', nickname
            else:
                printl("发送消息失败")

    def save_chat(self,sip,text):
        file = open("chat_history.dat","a")
        record ="out!" + sip + " " + time.strftime(ISOTIMEFORMAT) + " " + text + "\n"
        file.write(record)
        file.close()

    def do_sms(self,line):
        '''用法：sms [num] [text]
            send sms to num'''
        if not line:
            print u'用法：sms [num] [text]'
            return
        cmd = line.split()
        if len(cmd) ==1:
            return
        num = cmd[0]
        self.to=self.get_sip(line)
        if not self.phone.send_sms(toUTF8(line.split(" ")[1]),self.to):
            printl("发送短信失败")
        else:
            print u'已发送 '#,self.get_nickname(self.to)

    def do_find(self,line):
        '''用法：find [序号|手机号]|all
            隐身查询'''
        if not line:
            print u'用法：find [num]'
            return
        if line=='all':
            c = copy(self.phone.contactlist)
            num = len(c.items())
            for i in c:
                if c[i][0] == '':
                    c[i][0] = i[4:4+9]
            for i in range(num):
                if c[c.keys()[i]][2] == FetionHidden:
                    ret = self.phone.start_chat(c.keys()[i])
                    if ret:
                        if ret == c[c.keys()[i]][2]:
                            print "\033[35m",str(i),c[c.keys()[i]][0],"\t",
                        #elif ret == FetionOnline:
                            #print c[c.keys()[i]][0],u"不在线"
            print "\033[0m"
            return
        cmd = line.split()
        to = self.get_sip(cmd[0])
        nickname = self.get_nickname(to)
        if self.phone.contactlist[to][2] != FetionHidden:
            printl("拜托人家写着在线你还要查!")
        else:
            ret = self.phone.start_chat(to)
            if ret:
                if ret == self.phone.contactlist[to][2]:
                    print nickname, u"果然隐身"
                elif ret == FetionOnline:
                    print nickname, u"的确不在线哦"
            else:
                printl("获取隐身信息出错")

    def do_add(self,line):
        '''用法：add 手机号或飞信号'''
        if not line:
            printl("命令格式:add[a] 手机号或飞信号")
            return

        if line.isdigit() and len(line) == 9 or len(line) == 11:
            code = self.phone.add(line)
            if code:
                printl("添加%s成功"%line)
            else:
                printl("添加%s失败"%line)
        else:
            printl("命令格式:add[a] 手机号或飞信号")

    def do_del(self,line):
        '''delete buddy'''
        if not line:
            printl("命令格式:del[d] 手机号或飞信号")
            return
        if line.isdigit() and len(line) == 9 or len(line) == 11:
            code = self.phone.delete(line)
            if code:
                printl("删除%s成功"%line)
            else:
                printl("删除%s失败"%line)
        else:
            printl("命令格式:del[d] 手机号或飞信号")

    def do_get(self,line):
        self.phone.get_offline_msg()

    def do_update(self,line):
        '''用法：update [状态]
            更新飞信状态'''
        pass

    def do_scrot(self,line):
        if line:
            print "用法:scrot"
            return
        #im = ImageGrab.grab()
        #name = time.strftime("%Y%m%d%H%M%S") + ".png"
        #im.save(name)

    def do_cls(self,line):
        pass

    def get_sip(self,num):
        '''get sip and nickname from phone number or order'''
        c = copy(self.phone.contactlist)
        sip=""
        if len(num)==11:
            '''cellphone number'''
            for c in c.items():
                if c[1][1] == num:
                    sip = c[0]
            if not sip:
                printl("手机号不是您的好友")
        elif len(num) < 4:
            n = int(num)
            if n >= 0 and n < len(self.phone.contactlist):
                sip = c.keys()[n]
            else:
                printl("编号超出好友范围")
                return
        else:
            '''昵称形式'''
            for sip in c.keys():
                if num == c[sip][0]:
                    break;
        return sip


    def get_nickname(self,sip):
        return self.phone.contactlist[sip][0]

    def do_history(self,line):
        '''usage:history
        show the chat history information'''
        if not line:
            file = open("chat_history.dat","r")
            records = file.readlines()
            for record in records:
                temp = record.split()
                time = temp[2].split(":")[0]+":"+temp[2].split(":")[1]
                text = temp[3]

                sips = temp[0].split("!")
                if len(sips)==2:
                    sip = sips[1]
                    nickname = self.get_nickname(sip)
                    print self.nickname," to ",nickname," ",time,text
                else:
                    sip=sips[0]
                    nickname = self.get_nickname(sip)
                    print nickname," to ",self.nickname," ",time,text
        else:
            sip = get_sip(line)

    def do_quit(self,line):
        '''quit\nquit the current session'''
        self.to=""
        self.prompt=self.sta+">"
        pass

    def do_exit(self,line):
        '''exit\nexit the program'''
        self.phone.logout()
        sys.exit(0)

    def help_help(self):
        self.clear()
        printl("""
------------------------基于PyFetion的一个CLI飞信客户端-------------------------

        命令不区分大小写中括号里为命令的缩写

        help[?]           显示本帮助信息
        ls                列出在线好友列表
        la                列出所有好友列表
        ll                列出序号，备注，昵称，所在组，状态
        status[st]        改变飞信状态 参数[0隐身 1离开 2忙碌 3在线]
                          参数为空显示自己的状态
        msg[m]            发送消息 参数为序号或手机号 使用quit退出
        sms[s]            发送短信 参数为序号或手机号 使用quit退出
                          参数为空给自己发短信
        find[f]           查看好友是否隐身 参数为序号或手机号
        info[i]           查看个人信息
        update[u]         更新状态
        add[a]            添加好友 参数为手机号或飞信号
        del[d]            删除好友 参数为手机号或飞信号
        cls[c]            清屏
        quit[q]           退出对话状态
        exit[x]           退出飞信

        """)

    def clear(self):
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")

    def do_EOF(self, line):
        return True
    
    def postloop(self):
        print

    #shortcut
    do_q = do_quit
    do_h = do_history
    do_x = do_exit
    do_m = do_msg
    do_s = do_sms
    do_st = do_status
    do_f = do_find
    do_a = do_add
    do_d = do_del
    do_i = do_info
    do_u = do_update

class fetion_input(Thread):
    def __init__(self,phone):
        self.phone = phone
        self.to    = ""
        self.type  = "SMS"
        self.hint  = "PyFetion:"
        Thread.__init__(self)

    def run(self):
        sleep(1)
        #self.help()
        #while self.phone.receving:
        #    try:
        #        self.hint = toEcho(self.hint)
        #    except :
        #        pass

        #    #self.cmd(raw_input(self.hint))
        CLI(self.phone).cmdloop()
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
           
            c = copy(self.phone.contactlist)
            #使用编号作为参数
            if len(cmd[1]) < 4:
                n = int(cmd[1])
                if n >= 0 and n < len(self.phone.contactlist):
                    self.to = c.keys()[n]
                    self.hint = "给%s发%s:" % (c[self.to][0],s[self.type])
                else:
                    printl("编号超出好友范围")
                    return

            #使用手机号作为参数
            elif len(cmd[1]) == 11:
                for c in c.items():
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
                        if ret == c[self.to][2]:
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
            if not self.phone.contactlist:
                printl("没有好友")
                return
            if self.phone.contactlist.values()[0] != 0:
                pass
            #当好友列表中昵称为空重新获取
            else:
                self.phone.get_contactlist()

            #print self.phone.contactlist
            c = copy(self.phone.contactlist)
            num = len(c.items())
            for i in c:
                if c[i][0] == '':
                    c[i][0] = i[4:4+9]
            printl(status[FetionOnline])
            for i in range(num):
                if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))

            printl(status[FetionHidden])
            for i in range(num):
                if c[c.keys()[i]][2] == FetionHidden:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))

            printl(status[FetionOffline])
            for i in range(num):
                if c[c.keys()[i]][2] == FetionOffline:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))


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


class progressBar(Thread):
    def __init__(self):
        self.running = True
        Thread.__init__(self)

    def run(self):
        i = 1
        while self.running:
            sys.stderr.write('\r')
            sys.stderr.write('-'*i)
            sys.stderr.write('>')
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
    

def login():
    '''登录设置'''
    if len(sys.argv) > 3:
        print u'参数错误'
    elif len(sys.argv) == 3:
        mobile_no = sys.argv[1]
        passwd = sys.argv[2]
    else:
        if len(sys.argv) == 2:
            mobile_no = sys.argv[1]
        elif len(sys.argv) == 1:
            mobile_no = raw_input(toEcho("手机号:"))
        passwd = getpass(toEcho("口  令:"))
    phone = PyFetion(mobile_no,passwd,"TCP",debug="FILE")
    return phone


def main(phone):
    '''main function'''
    try:
        t = progressBar()
        t.start()
        #可以在这里选择登录的方式[隐身 在线 忙碌 离开]
        ret = phone.login(FetionHidden)
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
    phone = login()
    sys.exit(main(phone))
