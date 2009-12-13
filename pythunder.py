#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIT License
#By: cocobear.cn@gmail.com
   
from aes import AES
from struct import unpack,pack
from binascii import b2a_hex

import urllib2
import sys
   
def printf(raw):
    s = []
    s.append(raw)
    print len(s[0]),s
    
def parse(data):
    urls = []
    start = 0
    #printf(data)
    if len(data) < 53:
        return urls
    unkown9,file_size,zero4,cid_len,cid,zero8,nums = unpack('<9slll20sql',data[:53])
    start += 53
    #printf(unkown9)
    #print file_size,zero4,cid_len,
    cid = b2a_hex(cid)
    #print cid
    #print zero8,nums
    while nums:
        total_len,durl_len = unpack('<ll',data[start:start+8])
        start += 8
        rurl_len = total_len - durl_len - 8 - 23
        #print total_len,durl_len,rurl_len
        durl,rurl_len,rurl = unpack('<%ssl%ss'%(durl_len,rurl_len),data[start:start+total_len-4-23])
        start += total_len - 4
        #print durl,rurl
        urls.append(durl)
        nums = nums - 1
    return urls

def get_urls(url):
   
    urls = []
    servers = { 
        1:{'server': 'http://58.254.39.6:80/',
           'cmd': '\x36\x00\x00\x00\x09\x00\x00\x00',
           'key': '\xB6\xC3\x0A\xEB\x99\xCA\xF8\x49\xA7\x34\xCE\x4B\xFD\x90\x6C\x54'},
        2:{'server': 'http://123.129.242.169:80/',
           'cmd': '\x36\x00\x00\x00\x55\x00\x00\x00',
           'key': '\x18\x3A\x7F\x85\xE4\x21\xC7\x58\x06\x18\x6C\x63\x32\x86\x1E\xCD'},
        #3:{'server': 'http://123.129.242.168:80/',
        #   'cmd': '\x36\x00\x00\x00\x57\x00\x00\x00',
        #   'key': '\x64\x91\x63\x9D\xE8\x09\x87\x4D\xA5\x0A\x12\x02\x3F\x25\x3C\xF0'}
        #4:{'server': 'http://123.129.242.168:80/',
        #   'cmd':'\x36\x00\x00\x00\xf7\x00\x00\x00',
        #   'key':'\x2D\x33\xD2\x89\x46\xC3\xF8\x39\x76\x7B\xC4\x2F\x46\x1C\x45\x4C'}

             }

    for s in servers.values():
        server = s['server']
        cmd = s['cmd']
        key = s['key']
        a = AES(key)
    
        plaintext = ''
        plaintext += 'd\x02\x05\x00\x00\x00\xd1\x07\x00'
        plaintext += pack('<l',len(url))
        plaintext += url
        plaintext += '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x10\x00\x00\x0000030D3F968AAYV4\x00\x00\x00\x00j\x01\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x000000\x04\x00\x00\x00'
        #alignment
        length = len(plaintext)
        _,extra = divmod(length,16)
        if extra:
            plaintext += chr(extra)*(16-extra)
        else:
            plaintext += chr(16)*16
        #printf(plaintext)
        #encryption
        ciphertext = a.encrypt(plaintext)
        #printf(ciphertext)
    
        #add 12 bytes[command+len]
        data = ''
        data += cmd
        data += pack('<l',len(ciphertext))
        data += ciphertext
        #printf(data)
    
        headers = {
               'Accept':'*/*',
               'Content-type':'application/octet-stream',
               'Connection':'Keep-Alive',
                  }
        opener = urllib2.build_opener()
        urllib2.install_opener(opener)
        request = urllib2.Request(server,headers = headers,data=data)
        try:
            conn = urllib2.urlopen(request)
        except urllib2.URLError:
            continue
        result = conn.read()

        #decryption;ignore the first 12 bytes.
        plaintext  = a.decrypt(result[12:])
        #printf(plaintext)
        urls.extend(parse(plaintext))
    return list(set(urls))

def main():
    if len(sys.argv) != 2:
        url = 'http://42.duote.com/xunleidt.exe'
    else:
        url = sys.argv[1]
    print get_urls(url)
if __name__ == '__main__':
    sys.exit(main())
            
