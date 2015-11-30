# Shield
Client-Side Encryption for DropBox. Shield encrypts the file-contents before they are stored into DropBox. It uses DropBox SDK API to communicate with hosting account.

Usage:

python shell.py

This brings up Shield shell and requires you to authorize the app to access your DropBox.

1. Go to: https://www.dropbox.com/1/oauth2/authorize?response_type=code&client_id=sw5ubcmq2ohe74g
2. Click "Allow" (you might have to log in first)
3. Copy the authorization code.
Enter the authorization code here: 


Once authorization succeeds, you can Shield to create/remove/share files. The commands are self explanatory.

Welcome to the Shield.   Type help or ? to list commands.

(Shield>) ?

Documented commands (type help <topic>):
========================================
bye  cd  chmod  create  help  login  ls  mkdir  open  pwd  rm  rmdir  signup

(Shield>)

