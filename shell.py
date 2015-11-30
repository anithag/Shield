import cmd, sys
import subprocess
import os
import ShieldBackend
import Authenticate

class Shieldshell(cmd.Cmd):
    intro = 'Welcome to the Shield.   Type help or ? to list commands.\n'
    prompt = '(Shield>) '
    efsbackend = None
    loggedIn = False
    dbxclient = None
 
    def __init__(self):
       self.authobj = Authenticate.DropBoxSDK();
       self.dbxclient = self.authobj.authorize()
       
       #super(Shieldhell, self).__init__()
       cmd.Cmd.__init__(self)

    def do_signup(self, arg):
	   'Sign-up! signup <username>' 
           self.username = arg
           self.userdir= 'users/' + arg + '/'
	   if not os.path.exists(self.userdir):
              os.mkdir(self.userdir)
           self.loggedIn = True
           self.efsbackend = ShieldBackend.ShieldBackend()
	   self.efsbackend.setclient(self.dbxclient)
	   self.efsbackend.register(arg)
   
    def do_login(self, arg):
	'Login! login <username>'
	self.username = arg
        self.efsbackend = ShieldBackend.ShieldBackend()
	self.efsbackend.setclient(self.dbxclient)
	issucc = self.efsbackend.login(arg)
	if not issucc:
		print "Login Failed"
	else:
                self.userdir= 'users/' + arg + '/'
	        if not os.path.exists(self.userdir):
                   os.mkdir(self.userdir)
		self.loggedIn = True

    def checklogin(self):
        if self.loggedIn:
            return True
        print 'Must login or register'
        return False

    def do_create(self, arg):
	'Create a file: create <filename>'
	
	if not self.checklogin():
	  return 

	if not self.efsbackend.check_perm():
	  return

	if not self.efsbackend.check_pathperm(arg):
	  return

	'''check path and create directory accordingly'''
	workdir = self.userdir + "/" + arg
	basepath = os.path.split(workdir)[0]
	if not os.path.exists(basepath):
	    os.makedirs(basepath)
        openFileCommand = ['/usr/bin/vi', arg]
        try:
            process = subprocess.Popen(openFileCommand, stdout=subprocess.PIPE, cwd=self.userdir)
            output = process.communicate()[0]
        except:
            print "Error opening file."

	print 'Preparing to upload ...'
	self.efsbackend.create(self.userdir + "/" + arg, arg) 
        return

    def do_mkdir(self, arg):
	'Create a file: create <dirname>'
	if not self.checklogin():
	  return 

	if not self.efsbackend.check_perm():
	  return

	self.efsbackend.mkdir(self.userdir + "/" + arg, arg) 
        return

    def do_open(self, arg):
	'Open a file: open <filename>'
	if not self.checklogin():
	  return 
	self.efsbackend.open(arg, self.userdir + "/" + arg) 
   
    def do_rm(self, arg):
	'delete a file: rm <relpath-filename>'
	if not self.checklogin():
		return
	self.efsbackend.rm(arg)

    def do_rmdir(self, arg):
	'delete a file: rm <relpath-dirname>'
	if not self.checklogin():
		return
	self.efsbackend.rmdir(arg)

    def do_chmod(self, line):
        'Share files: chmod <file/dir> <user>'
	if not self.checklogin():
	   return
	l = line.split()
	fname = l[0]
	user = l[1]
	self.efsbackend.share(fname, user)

    def do_cd(self, arg):
	'Change directory. Use .. to get to parent directory: cd <dir>'
	if not self.checklogin():
	   return
	self.efsbackend.cd(arg)
	
    def do_ls(self, arg):
	'List files and directories in current directory: ls'
	if not self.checklogin():
	   return
	self.efsbackend.ls()

    def do_pwd(self, arg):
	'Print current directory: pwd'
	if not self.checklogin():
	   return
	self.efsbackend.pwd()
	
	
    def do_bye(self, arg):
        'exit:  BYE'
        return True

def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

if __name__ == '__main__':
    efs = Shieldshell()
    efs.cmdloop()
