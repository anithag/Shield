from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto import Random
import os
import json
import base64

message = os.urandom(32)
key = RSA.generate(1024)
publickey = key.publickey().exportKey("PEM")
privatekey = key.exportKey("PEM")
key = RSA.importKey(publickey)
cipher = PKCS1_OAEP.new(key)
ciphertext = cipher.encrypt(message)

b64cipher = base64.encodestring(ciphertext)

table={"chinnu":b64cipher}

with open('secret.txt', 'w') as s:
   json.dump(table, s)

key = RSA.importKey(privatekey)
cipher = PKCS1_OAEP.new(key)

with open('secret.txt', 'r') as s:
   table = json.load(s)
   b64cipher = table["chinnu"]
   ciphertext = base64.decodestring(b64cipher)

message = cipher.decrypt(ciphertext)
