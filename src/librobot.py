#! /usr/bin/env python
# -*- coding: utf-8 -*-

#By : amoblin@gmail.com

from FetionRobot import *
from time import sleep
from copy import copy
import time
import sys
import exceptions

import urllib,re
from HTMLParser import HTMLParser

from PyBistu import *

#from judou import argmax_seg,atom_seg,ENCODING
#from dictionary.word_dict import FooDict, SogouDict, JudouDict


userhome = os.path.expanduser('~')
config_folder = os.path.join(userhome,'.librobot')
config_file = os.path.join(config_folder,'librobot.txt')
mobile_no = ""

colors = {}

#last lines
def last_lines(filename, lines = 1):
    #print the last several line(s) of a text file
    """
    Argument filename is the name of the file to print.
    Argument lines is the number of lines to print from last.
    """
    block_size = 1024
    block = ''
    nl_count = 0
    start = 0
    fsock = file(filename, 'rU')
    try:
        #seek to end
        fsock.seek(0, 2)
        #get seek position
        curpos = fsock.tell()
        while(curpos > 0): #while not BOF
            #seek ahead block_size+the length of last read block
            curpos -= (block_size + len(block));
            if curpos < 0: curpos = 0
            fsock.seek(curpos)
            #read to end
            block = fsock.read()
            nl_count = block.count('\n')
            #if read enough(more)
            if nl_count >= lines: break
        #get the exact start position
        for n in range(nl_count-lines+1):
            start = block.find('\n', start)+1
    finally:
        fsock.close()
    return block[start:]

class LibRobot(FetionRobot):
    def __init__(self,name):
        FetionRobot.__init__(self,name)

    def monitor(self):
        self.threads.append(processor(self.phone))
        self.start_threads()

class processor(fetion_recv):
    def __init__(self,phone):
        fetion_recv.__init__(self,phone)

    def parser_cmd(self,to,line):
        fetion_recv.parser_cmd(self,to,line)
        message = ""
        nickname = self.phone.contactlist[to][0]
        if line[0]=='-':
            cmd = line[1:]
            cmd = cmd.split()
            if cmd[0] == 'help' or cmd[0] == 'h':
                message = "欢迎使用北京信息科技大学图书馆查询系统(北信兔)\n"
                message += "默认查询参数：检索词类型：所有题名；匹配方式：模糊匹配；资料类型：全部；分管名称：小营校区；排列方式：出版年逆序。\n目前只显示索书号和标题。以后会逐步完善。\n"
                message += "换页： -p [页码]\n客服：-q [消息]\n"
                message += "显示在线好友： -bls\n显示所有好友：-bla或者-bll\n"
                message += "好友间通信：-a [序号|飞信号] [消息]\n"
                #message += "已借图书列表：-ls\n"
                message += "获取该帮助：-h\n"
                message += "更多请访问http://code.google.com/p/bistu\n"
            elif cmd[0] == 'page' or cmd[0] == 'p':
                if len(cmd)<2:
                    message='参数错误'
                else:
                    if not self.libkeywords.has_key(to):
                        message = '请先进行关键字查询。'
                    elif cmd[1].isdigit():
                        message = search(self.libkeywords[to],cmd[1])
                    else:
                        message = "参数格式错误。第二个参数应为数字，也就是你要看的页号。"
            elif cmd[0]=='b' and to=='sip:856882346@fetion.com.cn;p=5911':
                if len(cmd)<2:
                    return
                c = copy(self.phone.contactlist)
                num = len(c.items())
                for i in c:
                    self.phone.send_msg(line[3:],i)
            elif cmd[0]=='q':
                if len(cmd)<2:
                    message='参数错误'
                else:
                    message = nickname + "("+to.split(":")[1].split("@")[0]+"):" + line[3:]
                    to = 'sip:856882346@fetion.com.cn;p=5911'
            elif cmd[0]=='a':
                if len(cmd)<3:
                    message='参数错误'
                else:
                    message = " ".join(cmd[2:])
                to = self.get_sip(cmd[1])
            elif cmd[0]=='bls':
                c = copy(self.phone.contactlist)
                num = len(c.items())
                for i in c:
                    if c[i][0] == '':
                        c[i][0] = i[4:4+9]
                count=0
                for i in range(num):
                    if c[c.keys()[i]][2] == FetionOnline:
                        message +='['+str(i)+']'+c[c.keys()[i]][0]+" "
                        count=count+1
                message = "在线好友/所有好友：" + str(count)+"/"+str(num)+"\n"+message
            elif cmd[0]=='bll':
                c = copy(self.phone.contactlist)
                num = len(c.items())
                for i in c:
                    if c[i][0] == '':
                        c[i][0] = i[4:4+9]
                for i in range(num):
                    uri = c.keys()[i]
                    message += "["+ str(i)+"] " + c[uri][0]+" " + c[uri][1]+" " + status[c[uri][2]]
                    for group in self.phone.grouplist:
                        if group[0] == c[uri][4]:
                            message += " " + group[1]
                    message +="\n"
            elif cmd[0]=='bla':
                c = copy(self.phone.contactlist)
                num = len(c.items())
                for i in c:
                    if c[i][0] == '':
                        c[i][0] = i[4:4+9]
                #printl(status[FetionOnline])
                for group in self.phone.grouplist:
                    message += group[1]+":"
                    for i in range(num):
                        if c[c.keys()[i]][4] == group[0]:
                            message += "[" + str(i) + "]" + c[c.keys()[i]][0] + " "
                    message +="\n"
            elif cmd[0]=='his':
                command_log_file = os.path.join(config_folder,"librot.log")
                message = "".join(last_lines(command_log_file,5))
            elif cmd[0]=='u' and cmd[2]=='-p':
                if len(cmd)!=4:
                    message = "参数错误。"
            elif cmd[0]=='ls':
                message="所借图书列表"
            elif cmd[0]=='info':
                if len(cmd)<2:
                    message = "参数错误。"
                    message="图书信息"
            elif cmd[0]=='binfo':
                if len(cmd)<2:
                    message = "参数错误。"
                    message="好友信息"
            elif cmd[0]=='invit':
                if len(cmd)<2:
                    message = "参数错误。"
                else:
                    message="邀请好友"
            elif cmd[0]=='ls':
                message=cmd[0]
            elif cmd[0]=='ls':
                message=cmd[0]
            elif cmd[0]=='ls':
                message=cmd[0]
            elif cmd[0]=='ls':
                message=cmd[0]
            elif cmd[0]=='ls':
                message=cmd[0]
            else:
                message="意外的命令，令我不知所措，错落有致，志存高远，远走他乡，相见恨晚。"
        else:
            print time.strftime(ISOTIMEFORMAT)," ",nickname," search:",line
            message = search(line)
            if message == 0:
                #for DictClass in (JudouDict,):# SogouDict, FooDict):
                #    dict = DictClass()
                #    dict.load()
                #    export_word_graph = line[1]
                #    text = line[0]
                    #message = ' '.join(argmax_seg(line, dict, encoding=ENCODING, export_word_graph=export_word_graph))
                print message
            else:
                self.libkeywords[to]=line

                header = "你好，我是北信兔！更多帮助请输入'-h'\n"
                title = '关键词为"' + line+ '"的'
                message = header + title + message
                print message

        if self.phone.send_msg(message.decode('utf-8').encode('utf-8'),to):
            print "response success.\n"
        else:
            print "response failed.\n"

    def welcome(self):
        num = len(self.phone.contactlist.items())
        message = u"欢迎第"+num.decode('utf-8')+u"位好友使用北京信息科技大学图书查询系统（北信兔）！\n"
        print message
        self.phone.send_msg(message.encode('utf-8'),uri)

        nickname = self.phone.contactlist[self.phone.newsip][0]
        message = u"添加好友："+nickname.decode('utf-8')
        self.phone.send_msg(message.encode('utf-8'),"sip:856882346@fetion.com.cn;p=5911")

if __name__ == "__main__":
    robot = LibRobot("librobot")   #飞信机器人守护
    robot.setDaemon(True)
    robot.start()
    robot.print_info()
    while(True):
        time.sleep(10)
        pass
