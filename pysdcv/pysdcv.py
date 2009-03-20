#!/usr/bin/env python
# -*- code=utf-8 -*-
#By cocobear.cn@gmail.com
#Using GPL v2

from lookup import lookup
import sys


if __name__ == "__main__":
    dict_prefix = "/usr/share/stardict/dic/stardict-langdao-ec-gb-2.4.2/langdao-ec-gb"
    #dict_prefix = "./dic/stardict-langdao-ec-gb-2.4.2/langdao-ec-gb"
    if len(sys.argv) != 2:
        print "give me a word"
        sys.exit(1)

    ifo_file = dict_prefix + ".ifo"
    f = file(ifo_file)
    s = f.readlines()
    wc = int(s[2].strip().split("=")[1])
    file_size = int(s[3].strip().split("=")[1])
    s =  lookup(dict_prefix,file_size,wc,sys.argv[1])
    print s
