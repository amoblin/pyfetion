#!/usr/bin/env python
#
import sys
import os
import re

TEST = "test"
def find_dir(original_dir,l):
	while True:
		for f in os.listdir(original_dir):	
			#print f,
			f = original_dir+"/"+f
			if os.path.isdir(f):
				l.append(f)
				find_dir(f,l)
		return 

def file_copy(original_dir,num):
	global TEST
	while num:
		test_dir = TEST+str(num)
		for f in os.listdir(original_dir):
			#print f,
			f = original_dir+"/"+f
			if os.path.isfile(f):
				print "cp",f,re.sub(original_dir,test_dir,f)
		l = []
		find_dir(original_dir,l)	
		for i in l:
			for j in os.listdir(i):
				j = i+"/"+j
				if os.path.isfile(j):
					print "cp",j,re.sub(original_dir,test_dir,j)
		num-=1
		print 

def dir_copy(original_dir,num):
	global TEST
	while num:
		print "mkdir",
		test_dir = TEST+str(num)
		l = []
		find_dir(original_dir,l)
		for i in l:
			print test_dir,re.sub(original_dir,test_dir,i),

		num-=1
		print
	return

def main(argv=None):
	if argv is None:
		argv = sys.argv
	if len(sys.argv) != 2:
		return(usage())
	num = 5
	print "echo \"Starting create directories\""
	print "date +%T.%N"
	dir_copy(argv[1],num)
	print "echo \"Starting copy files\""
	print "date +%T.%N"
	file_copy(argv[1],num)
	print "echo \"Recursive directory stats\""
	print "find . -print -exec ls -l {} \\;"
	print "du -s *"
	print "date +%T.%N"

	print "echo \"Scanning each file\""
	print "find . -exec grep kangaroo {} \\;"
	print "find . -exec wc {} \\;"
	print "date +%T.%N"






def usage():
	print "\n%s [Your File name]\n" % sys.argv[0]
	return 1

if __name__ == "__main__":
	sys.exit(main())


	
