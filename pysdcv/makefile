PYINC = /usr/include/python2.5

lookup.so: lookup.c
	gcc lookup.c -g -I$(PYINC) -lz -shared -fPIC -o lookup.so

clean:
	rm -f lookup.so

