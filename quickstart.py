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

QUERY = "subject:statement from Progressive Speech Therapy, LLC"



def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', q=QUERY).execute()
        message_ids = results.get('messages', [])
        
        messages = []

        def add(id, msg, err):
            # id is given because this will not be called in the same order
            if err:
                print(err)
            else:
                messages.append(msg)

        batch = service.new_batch_http_request()
        for msg in message_ids:
            batch.add(service.users().messages().get(userId='me', id=msg['id']), add)
        batch.execute()

        if not messages:
            print('No messages found.')
            return

 
        attachments = {}

        for msg in messages:
            #print(msg)
            for list_item in msg.get('payload').get('parts'):
                fname = list_item.get('filename')
                if fname:
                    attachments[fname] = {}
                    attachments[fname]['msgId'] = msg['id']
                    attachments[fname]['atcId'] = list_item.get('body').get('attachmentId')
        
        attachments_data = []
        def add_attachment(id, msg, err):
            # id is given because this will not be called in the same order
            if err:
                print(err)
            else:
                attachments_data.append(msg)


        for key,val in attachments.items():
            print(f"======{key}")
            print(f"{val}")
            print("-- attachment data --")
            batch.add(service.users().messages().attachments().get(userId='me',messageId=val['msgId'],id=val['atcId']), add_attachment)
            
        batch.execute()

        #for a in attachments_data:
        #    print(a.keys())
        print(attachments_data[0])
        with open("test.pdf", "wb") as f:
            b64s = attachments_data[0].get('data')
            print(b64s)
            f.write(urlsafe_b64decode(b64s))

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
