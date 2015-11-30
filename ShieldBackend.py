from __future__ import print_function
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP 
from Crypto import Random
import Cipher as mycipherutil
import DBop
import os
import base64
import json

class ShieldBackend:
  username = None
  pbkey = None
  prkey = None
  dbxclient = None
  cwd = None

  def __init__(self):
	self.dbhandle = DBop.DBophandle()
	self.dbhandle.connecttodb("ShieldDB/user.db")
	'''self.dbhandle.inituserdb()'''
 
  def setclient(self, dbxclient):
	self.dbxclient = dbxclient
	return

  def register(self, username):
	key = RSA.generate(1024)
	publickey = key.publickey().exportKey("PEM")
	privatekey = key.exportKey("PEM")
	
	self.dbhandle.insertuser(username, publickey, privatekey)
	print('Registration done')	
	
  def login(self, username):
	row = self.dbhandle.getuser(username) 
	if row is None:
		return False
	else:
		self.username = username
		self.pbkey, self.prkey = (row[0], row[1])
		self.cwd="/"
		print('Welcome ' + self.username)
		return True

  def check_perm(self):
	'''Get last directory'''
	lastdir = os.path.split(self.cwd)[1]
	'''Get current directory shadow file '''
	if not self.cwd == "/":
		curdirshadowfile = self.cwd + "/" + lastdir + ".sdw"
		with self.dbxclient.get_file(curdirshadowfile) as df:
   			permtable = json.load(df)

   		if not self.username in  permtable.keys() and not self.cwd == "/":
			print('You donot have permissions to do this operation')
			return False
		else:
			return True
	return True
	
  def check_pathperm(self, path):
	'''Get directory  path in which file is created'''
	relpath = os.path.split(path)[0]
	if relpath:
		dirlist = relpath.split("/")
		if dirlist:
		   shadowdirpath = self.cwd 
		   for idx, val in enumerate(dirlist):
		   	shadowdirpath = shadowdirpath + "/" + val 
		   	shadowdirfile = shadowdirpath + "/" + val + ".sdw"
			with self.dbxclient.get_file(shadowdirfile) as df:
   				permtable = json.load(df)
   			if not self.username in  permtable.keys():
				print('You donot have permissions to do this operation')
				return False
	return True
			
  def create(self, tmpfilename, uploadfile):
	
	dbxuploadfilepath = self.cwd + "/" + uploadfile
	encfilename = tmpfilename + ".enc"

	'''generate 256-bit random key for symmetric encryption'''
	key = os.urandom(32)
	mycipherutil.encrypt_file(key, tmpfilename, encfilename)
	
	'''upload encrypted file'''
       	f = open(encfilename, 'rb')
	response = self.dbxclient.put_file(dbxuploadfilepath, f)
	f.close()

	'''put shadow file with owner'''
	shadowfile = dbxuploadfilepath + ".sdw"
	shadowfilelocal = tmpfilename + ".sdw"
     	'''Encrypt above key using owner's public key '''
     	cipher = PKCS1_OAEP.new(RSA.importKey(self.pbkey))
        encryptedkey = cipher.encrypt(key)
        dictentry = {self.username:base64.encodestring(encryptedkey)}
	with open(shadowfilelocal, "w+") as sdw:
	     		json.dump(dictentry, sdw)
	
	with open(shadowfilelocal, "r") as sdw:
	   	        response = self.dbxclient.put_file(shadowfile, sdw)
	   		#print(("Upload status:" ,  response))
	
	return


  def mkdir(self, dirname, uploaddirname):


	if not self.check_perm():
		return

	'''generate 256-bit random key for symmetric encryption'''
	key = os.urandom(32)
	
	'''create folder path. Expected relative path only'''
	dbxuploaddirpath = self.cwd + "/" + uploaddirname

	response = self.dbxclient.file_create_folder(dbxuploaddirpath)

	'''put shadow file with owner'''
	shadowfile = dbxuploaddirpath + "/" + uploaddirname + ".sdw"
	shadowfilelocal = dirname + ".sdw"
	'''Encrypt above key using owner's public key '''
	cipher = PKCS1_OAEP.new(RSA.importKey(self.pbkey))
	encryptedkey = cipher.encrypt(key)
        dictentry = {self.username:base64.encodestring(encryptedkey)}

	'''create permissions '''
	with open(shadowfilelocal, "w+") as sdw:
	     		json.dump(dictentry, sdw)
	
	with open(shadowfilelocal, "r") as sdw:
	   		response = self.dbxclient.put_file(shadowfile, sdw)
	   		#print(("Upload status: ",  response)) 
	
	return

  def open(self, filename, dnfile):

	'''expecting a relative path in filename'''
	dbxdwnfilepath = self.cwd + "/" + filename
	shadowfile = dbxdwnfilepath + ".sdw"

	with self.dbxclient.get_file(shadowfile) as df:
   		permtable = json.load(df)

   	if not self.username in  permtable.keys():
		print('You donot have permissions to do this operation')
		return
	else:

   		b64cipherkey = permtable[self.username]
   		encryptedkey = base64.decodestring(b64cipherkey)

		'''Decrypt above key using owner's private key '''
		cipher = PKCS1_OAEP.new(RSA.importKey(self.prkey))
		decryptedkey = cipher.decrypt(encryptedkey)

		f = open(dnfile, 'wb')
		with self.dbxclient.get_file(dbxdwnfilepath) as df:
		     f.write(df.read())

		f.close()
	
		'''decrypt'''
		decfilename = dnfile + ".dec"
		mycipherutil.decrypt_file(decryptedkey, dnfile, decfilename)
		print("File Downloaded")

  def share(self, filename, user):

	'''probe if file/dir'''
	folder_metadata = self.dbxclient.metadata(self.cwd + "/" + filename)
	if folder_metadata['is_dir'] :
		isdir = True
	else:
		isdir = False

	''' get shadow file and update permissions'''
	'''Expect only one level in filename i.e. no dir1/dir2/file.txt'''
	if isdir:
		hostdirpath = self.cwd + "/" + filename
		shadowfile = hostdirpath + "/" + filename + ".sdw"
	else:
		shadowfile = self.cwd + "/" + filename + ".sdw"	

	localshadowfile = "users/" + self.username + "/" + filename + ".sdw"
	with self.dbxclient.get_file(shadowfile) as df:
   		permtable = json.load(df)

   	if not self.username in  permtable.keys():
		print('You donot have permissions to do this operation')
		return
	else:
		''' get the key '''
   		b64cipherkey = permtable[self.username]
   		encryptedkey = base64.decodestring(b64cipherkey)

	        '''Decrypt above key using owner's private key '''
	        cipher = PKCS1_OAEP.new(RSA.importKey(self.prkey))
	        decryptedkey = cipher.decrypt(encryptedkey)

		'''get the public key of user'''
	        row = self.dbhandle.getuser(user) 
		userpbkey = row[0]

	        '''Encrypt above decryptedkey using owner's public key '''
	        usercipher = PKCS1_OAEP.new(RSA.importKey(userpbkey))
	        userencryptedkey = usercipher.encrypt(decryptedkey)

		'''update permissions'''
		permtable[user] = base64.encodestring(userencryptedkey)


	        with open(localshadowfile, "w+") as sdw:
	             json.dump(permtable, sdw)

	        with open(localshadowfile, "r") as sdw:
	   	     response = self.dbxclient.put_file(shadowfile, sdw, overwrite=True)
	   	     #print(("Upload status: ",  response) )
		return
	
  def cd(self, dir):
	if not self.cwd == "/" and not dir == "..":
		dbxdirpath = self.cwd + "/" + dir
	elif dir == ".." and not self.cwd == "/":
		dbxdirpath = os.path.split(self.cwd)[0]
	elif dir == ".." and self.cwd == "/":
		dbxdirpath = "/"
	else:
		''' only relative path at the moment'''
		if  not self.cwd == "/": 
		    dbxdirpath = self.cwd + "/" + dir
		else:
		    dbxdirpath = self.cwd + dir

	if dbxdirpath == "/" :
		'''we should be in / directory'''
		self.cwd = "/"
	else:

		'''Get last directory'''
		if not dir == ".." :
			lastdir = os.path.split(dir)[1]
		else:
			lastdir = os.path.split(dbxdirpath)[1]

		shadowdirfile = dbxdirpath + "/" + lastdir + ".sdw"

		with self.dbxclient.get_file(shadowdirfile) as df:
   			permtable = json.load(df)

   		if not self.username in  permtable.keys():
			print('You donot have permissions to do this operation')
			return
		else:
			self.cwd = dbxdirpath

  def ls(self):
	folder_metadata = self.dbxclient.metadata(self.cwd)
	for i in folder_metadata['contents']:
		'''prune file path'''
		fullpath= i['path']
		trimmedpath = os.path.split(fullpath)[1]
		'''skip shadow files'''
		if not trimmedpath.endswith('.sdw'):
			print(trimmedpath, end="\t")

	print("\n")

  def pwd(self):
	print(self.cwd)

  def rm(self, filename):
	
	'''Check permissions along the way'''
	if not self.check_pathperm(filename):
		return
	
	hostdirpath = self.cwd + "/" + filename
	shadowfile = hostdirpath + ".sdw"

	with self.dbxclient.get_file(shadowfile) as df:
   		permtable = json.load(df)

   	if not self.username in  permtable.keys():
		print('You donot have permissions to do this operation')
		return
	response = self.dbxclient.file_delete(shadowfile) 
	response = self.dbxclient.file_delete(hostdirpath) 
	return

  def rmdir(self, dirname):
	
	'''Check permissions along the way'''
	if not self.check_pathperm(dirname):
		return
	
	hostdirpath = self.cwd + "/" + dirname
	dirshadowfile = os.path.split(dirname)[1]
	shadowdir = hostdirpath + "/" + dirshadowfile + ".sdw"

	with self.dbxclient.get_file(shadowdir) as df:
   		permtable = json.load(df)

   	if not self.username in  permtable.keys():
		print('You donot have permissions to do this operation')
		return

	'''first delete shawdowfile - required for deleting dir'''
	response = self.dbxclient.file_delete(shadowdir) 
	response = self.dbxclient.file_delete(hostdirpath) 
	return

