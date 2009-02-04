#!/usr/bin/env python
#coding: utf-8 
#author:        cocobear
#version:       0.1

import urllib
import sys,getopt,re
__doc__ = """Usage:
            ./url2read.py -h
            ./url2read.py -r ftp://cocobear.info/中国
            ./url2read.py http://cocobear.info/%E4%B8%AD%E5%9B%BD
        """
 
def url2read(s):

    s = urllib.unquote(s)
    try: 
            s = s.decode('UTF-8')
    except UnicodeDecodeError:
            try:
                s = s.decode('GBK')
            except UnicodeDecodeError:
                print "ERROR"
    finally:
            print s.encode(sys.stdin.encoding)


def read2url(s):
    head = ''
    g = re.search('^(http|ftp://)(.*)',s)
    if g:
        head = g.group(1)
        s = g.group(2)
    gbk = urllib.quote(s.decode(sys.stdin.encoding).encode('GBK'))

    utf8 = urllib.quote(s.decode(sys.stdin.encoding).encode('utf-8'))
    if gbk == utf8:
        print head+gbk
        return 0
    else:
        print "UTF8:\n"+head+utf8
        print "GBK:\n"+head+gbk
        return 0

def main(argv=None):
    f = False
    if len(sys.argv) < 2:
        print __doc__
        return 1
    try:
        opts,args = getopt.getopt(sys.argv[1:],"h,r",["help","reverse"])
    except getopt.error,msg:
        print msg
        print __doc__
        return 1
    for o,a in opts:
        if o in ("-h","--help"):
            print __doc__
            return 0
        if o in ("-r","--reverse"):
            f = True
    for arg in args: 
        if f:
            return read2url(arg)
        else:
            return url2read(arg)
    
    
if __name__ == "__main__":
    sys.exit(main())

   
