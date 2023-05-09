from __future__ import print_function

import os.path
from base64 import urlsafe_b64decode

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

QUERY_SPEECH_INVOICE = "subject:statement from Progressive Speech Therapy, LLC"


class ServiceHandler():

    def __init__(self):
        self.creds = self.generate_creds()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.msg_obj = self.service.users().messages()
        self.messages = []
        self.attachments = []
    
    
    def generate_creds(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and
        # is created automatically when the authorization flow completes for 
        # the first time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    
    def query_messages(self, query):
        results = self.msg_obj.list(userId='me', q=query).execute()
        return results.get('messages', []) 
    
    
    def batch_request(self, queried_messages):
        def add(id, msg, err):
            if err:
                print(err)
            else:
                self.messages.append(msg)
        batch = self.service.new_batch_http_request()
        for msg in queried_messages:
            batch.add(self.msg_obj.get(userId='me', id=msg['id']), add)
        batch.execute()


    def batch_attachments(self):
        def add(id, msg, err):
            if err:
                print(err)
            else:
                self.attachments.append(msg)
        
        batch = self.service.new_batch_http_request()
        attachment_data = self.get_attachments_data()
        
        for key,val in self.get_attachments_data().items(): 
            batch.add(self.msg_obj.attachments().get(
                userId='me',
                messageId=val['messageId'],
                id=val['attachmentId']), add)
        batch.execute()
    
    
    def clear_list(self):
        self.messages = []


    def get_attachments_data(self):
        att_obj = {}
        for msg in self.messages:
            for part in msg.get('payload').get('parts'):
                fname = part.get('filename')
                if fname:
                    att_obj[fname] = {}
                    att_obj[fname]['messageId'] = msg['id']
                    att_obj[fname]['attachmentId'] = part.get('body').get('attachmentId')
        return att_obj

    
    def get_attachments(self, query):
        results = self.query_messages(query)
        self.batch_request(results)
        self.batch_attachments()
        
        print(self.attachments[0])

        with open("whatwhat.pdf", "wb") as f:
            b64s = self.attachments[0].get('data')
            f.write(urlsafe_b64decode(b64s))



# ------------------------------------------------------- //
def main():
    
    svc = ServiceHandler()
    svc.get_attachments(QUERY_SPEECH_INVOICE)



if __name__ == '__main__':
    main()
