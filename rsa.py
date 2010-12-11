import Crypto
import Crypto.PublicKey
from Crypto.PublicKey.RSA import generate

from cPickle import dumps, loads
import base64
import math
import os
import random
import sys
import types
import zlib

class RSA():
    def __init__(self):
        self.encrypt("hello",genkey())

    def genkey(self,bits = 1024):
        Key = generate(bits)
        #['n', 'e', 'd', 'p', 'q', 'u']
        #print 'n ',Key.n
        #print 'e ',Key.e
        #print 'd ',Key.d
        #print 'p ',Key.p
        #print 'q ',Key.q
        #print 'u ',Key.u
        #print '  ',Key.p * Key.q
        return {'public':{'k':Key.e,'n':Key.n},'private':{'k':Key.d,'n':Key.n}}
    
    def encrypt(self,message,key):
        print 'here!'
        return self.chopstring(message, key['k'],key['n'],self.encrypt_int)
    
    def decrypt(self,cypher, key):
        """Decrypts a cypher with the private key 'key'"""
    
        return self.gluechops(cypher, key['k'], key['n'], self.decrypt_int)
    
    def sign(self,message, key):
        """Signs a string 'message' with the private key 'key'"""
        
        return self.chopstring(message, key['k'], key['n'], self.decrypt_int)

    def verify(self,cypher, key):
        """Verifies a cypher with the public key 'key'"""
    
        return self.gluechops(cypher, key['k'], key['n'], self.encrypt_int)   
    
    def decrypt_int(self,cyphertext, dkey, n):
        """Decrypts a cypher text using the decryption key 'dkey', working
        modulo n"""
    
        return self.encrypt_int(cyphertext, dkey, n)

    def gluechops(self,chops, key, n, funcref):
        """Glues chops back together into a string.  calls
        funcref(integer, key, n) for each chop.
    
        Used by 'decrypt' and 'verify'.
        """
        message = ""
    
        chops = self.unpicklechops(chops)
        
        for cpart in chops:
            mpart = funcref(cpart, key, n)
            message += self.int2bytes(mpart)
        
        return message
    def unpicklechops(self,string):
        """base64decodes and unpickes it's argument string into chops"""
    
        return loads(zlib.decompress(base64.decodestring(string)))

    def int2bytes(self,number):
        """Converts a number to a string of bytes
        
        >>> bytes2int(int2bytes(123456789))
        123456789
        """
    
        if not (type(number) is types.LongType or type(number) is types.IntType):
            raise TypeError("You must pass a long or an int")
    
        string = ""
    
        while number > 0:
            string = "%s%s" % (chr(number & 0xFF), string)
            number /= 256
        
        return string

    def encrypt_int(self,message, ekey, n):
        """Encrypts a message using encryption key 'ekey', working modulo
        n"""
    
        if type(message) is types.IntType:
            return self.encrypt_int(long(message), ekey, n)
    
        if not type(message) is types.LongType:
            raise TypeError("You must pass a long or an int")
    
        if message > 0 and \
                math.floor(math.log(message, 2)) > math.floor(math.log(n, 2)):
            raise OverflowError("The message is too long")
    
        return self.fast_exponentiation(message, ekey, n)

    def fast_exponentiation(self,a, p, n):
        """Calculates r = a^p mod n
        """
        result = a % n
        remainders = []
        while p != 1:
            remainders.append(p & 1)
            p = p >> 1
        while remainders:
            rem = remainders.pop()
            result = ((a ** rem) * result ** 2) % n
        return result
    
    def chopstring(self,message, key, n, funcref):
        """Splits 'message' into chops that are at most as long as n,
        converts these into integers, and calls funcref(integer, key, n)
        for each chop.
    
        Used by 'encrypt' and 'sign'.
        """
    
        msglen = len(message)
        mbits = msglen * 8
        nbits = int(math.floor(math.log(n, 2)))
        nbytes = nbits / 8
        blocks = msglen / nbytes
    
        if msglen % nbytes > 0:
            blocks += 1
    
        cypher = []
        
        for bindex in range(blocks):
            offset = bindex * nbytes
            block = message[offset:offset+nbytes]
            value = self.bytes2int(block)
            cypher.append(funcref(value, key, n))
    
        return self.picklechops(cypher)
    
    def bytes2int(self,bytes):
        """Converts a list of bytes or a string to an integer
    
        >>> (128*256 + 64)*256 + + 15
        8405007
        >>> l = [128, 64, 15]
        >>> bytes2int(l)
        8405007
        """
    
        if not (type(bytes) is types.ListType or type(bytes) is types.StringType):
            raise TypeError("You must pass a string or a list")
    
        # Convert byte stream to integer
        integer = 0
        for byte in bytes:
            integer *= 256
            if type(byte) is types.StringType: byte = ord(byte)
            integer += byte
    
        return integer
    
    def picklechops(self,chops):
        """Pickles and base64encodes it's argument chops"""
    
        value = zlib.compress(dumps(chops))
        encoded = base64.encodestring(value)
        return encoded.strip()

if __name__ == "__main__":
    RSA()
    
