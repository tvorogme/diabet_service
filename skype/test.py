import Skype4Py

# Create an instance of the Skype class.
skype = Skype4Py.Skype()

# Connect the Skype object to the Skype client.sk
skype.Attach()

# Obtain some information from the client and print it out.
print ('Your full name:', skype.CurrentUser.FullName)
print ('Your contacts:')
for user in skype.Friends:
    print ('    ', user.FullName)