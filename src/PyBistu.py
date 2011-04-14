#!/usr/bin/python
#-*coding:utf-8-*-

import urllib,re,sys
from HTMLParser import HTMLParser

class CustomParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        (self.islisttable,self.istd,self.istitle,self.isCount) = (0, 0, 0, 0)
        self.count=[]
        self.title=[]

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            for (attr, value)  in attrs:
                if attr=='width' and value == '97%':
                    self.islisttable = 1

        if self.islisttable and tag == 'td':
            self.istd=1

        if self.istd and tag == 'a':
            for (attr, value)  in attrs:
                if attr=='class' and value == 'opec_blue':
                    self.istitle=1

        if tag == 'span':
            for (attr, value)  in attrs:
                if attr=='class' and value == 'opec_red':
                    self.isCount=1

    def handle_endtag(self,tag):
        if tag=='table':
            self.islisttable=0
        if tag=='span':
            self.isCount=0
        if tag=='td':
            self.istd=0
        if tag=='a':
            self.istitle=0

    def handle_data(self,data):
        if self.istitle:
            self.title.append(data)

def search(key_words,page=1):
    url='http://211.68.37.131/opac2/book/search.jsp'

    data={}
    data['recordtype'] = 'all'      #资料类型 01中文图书
    data['library_id'] = "C"                  #分馆号 A健翔桥,B清河,C小营 
    data['kind'] = "simple"                                     #简单检索
    data['word'] = key_words.decode('utf-8').encode('cp936')    #关键词
    data['cmatch'] = "qx"                                       #匹配方式：前向 mh,jq
    data['searchtimes'] = "1"
    data['type'] = "title"                              #检索词类型：所有题名
    data['searchtimes'] = "1"                       #
    data['size'] = "10"                             #
    data['curpage'] =  page                          #
    data['orderby'] = "pubdate_date"                #
    data['ordersc'] = "desc"                        #
    url_values = urllib.urlencode(data)
    url = url + '?' + url_values

    pg = urllib.urlopen(url)
    content = pg.read()
    pg.close()


    #content = content.decode("cp936")
    content = content.decode("gb18030") #陈艳吉测试"拍案惊奇"使cp936出bug 2010-05-11 11:26出现。 12:48解决。
    #print content.encode('utf-8')

    #hp = CustomParser()

    #test = open("test.html")
    #content = test.read()
    #test.close()

    #hp.feed(content)
    #hp.close()
    #print hp.title
    #myre = '<a href="javascript:popup('+"'"+"detailBook.jsp','.+?')"+'" '+'class=opac_blue>(.+?)</a>'
    title_re = 'class=opac_blue>(.+?)</a>'
    number_re = '<span class="opac_red">(.+?)</span>'
    curpage_re = u'当前第<span class="opac_red"> <b>(.+?)</b> </span>页'
    page_number_re = u'共<span class="opac_red"> <b>(.+?)</b> </span>页</td>'

    number = re.findall(number_re,content)[0]
    curpage = re.findall(curpage_re,content)
    if len(curpage)>0:
        curpage=curpage[0]
        page_number= re.findall(page_number_re,content)[0]
        msg = "检索结果共" + number.encode('utf-8') + "条，" + page_number.encode('utf-8')  + "页，当前在第" +curpage.encode('utf-8')  +"页:\n"
    else:
        msg="没有检索到关键词'%s'的记录" % key_words
	return msg


    #print content
    #table_re = 'table Width=97(.+?)cellspacing'
#<table Width=97%
    table_re = 'class=opac_blue>(.+?)</a>'
    table = re.findall(table_re,content)
    if len(table):
        pass

    flag=1
    for title in table:
        if flag:
            msg = msg + title.encode('utf-8') 
            flag=0
        else:
            msg = msg + "《" + title.encode('utf-8')  + "》\n"
            flag=1

    return msg

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "help"
    else:
        print search(sys.argv[1])
