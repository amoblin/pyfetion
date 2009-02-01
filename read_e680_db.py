#!/usr/bin/env python
# -*- coding=utf-8 -*-
#Using GPL v2
#Author: cocobear.cn@gmail.com

"""
获取数据库名:
db = bsddb.db.DB()
db.open('native.db',bsddb.db.DB_UNKNOWN,bsddb.db.DB_RDONLY)
db.keys()
"""

import bsddb
import struct
import time

db_file = 'native.db'    
#databases中tuple分别表示:
#输出显示 数据库名 显示格式
#显示格式:
#0----原始内容输出
#1----UTF16汉字输出
#2----数字逆序输出
#3----日期输出


databases = [('姓名','780_contact_table.first name',1),('手机1','780_contact_table.mobile1',2),('手机2','780_contact_table.mobile2',2),('家庭1','780_contact_table.home1',2),('家庭2','780_contact_table.home2',2),('工作1','780_contact_table.work1',2),('工作1','780_contact_table.work1',2),]
databases = [('姓名','780_contact_table.first name',1),('手机1','780_contact_table.mobile1',2)]
databases = [('发送人','ems_table_in_flash.cmn_fld_from_name',1),('主题','ems_table_in_flash.cmn_fld_subject',1),('接收人','ems_table_in_flash.cmn_fld_to_name',1),('时间','ems_table_in_flash.cmn_fld_time_msg_reach_phone',3),]
out = []

for database in databases:
    #进行单文件多数据库操作 需要每次新建一个环境
    #因此下面这行在for循环里
    db =bsddb.db.DB()
    db.open(db_file,database[1],bsddb.db.DB_UNKNOWN,bsddb.db.DB_RDONLY)
    #每次读一个数据库
    #原本数据库中的value是系统的id key是具体有意义的内容
    #下面这行把db.items()得到的list进行反转 为以后有序输出
    out.append(sorted(db.items(),key=lambda (k,v): (v,k)))
    db.close()

#格式化输出
for i in databases:
    print i[0]+":",
print

for i in range(len(out[0])):
    for j in range(len(out)):
        #如果输出内容属于电话号码需要反转
        #根据databases中各位置含义来来判断
        if databases[j][2] == 0:
            #原始内容输出
            temp = []
            temp.append(out[j][i][0])
            print temp
        elif databases[j][2] == 1:
            #使用utf16进行解码
            print out[j][i][0].decode('utf16'),
        elif databases[j][2] == 2:
            #数字逆序输出
            print out[j][i][0].decode('utf16')[::-1],
        elif databases[j][2] == 3:
            #日期输出
            s = struct.unpack('<L',out[j][i][0])[0]
            print time.strftime("%Y-%m-%d",time.localtime(s))
    print

