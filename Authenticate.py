# Include the Dropbox SDK
import dropbox

class DropBoxSDK():

  # Get your app key and secret from the Dropbox developer website
  app_key = ''
  app_secret = ''
  
  def authorize(self):
   flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
   authorize_url = flow.start()

   # Have the user sign in and authorize this token
   authorize_url = flow.start()
   print '1. Go to: ' + authorize_url
   print '2. Click "Allow" (you might have to log in first)'
   print '3. Copy the authorization code.'
   code = raw_input("Enter the authorization code here: ").strip()

   # This will fail if the user enters an invalid authorization code
   self.access_token, user_id = flow.finish(code)

   client = dropbox.client.DropboxClient(self.access_token)
   #print 'linked account: ', client.account_info()
   return client


