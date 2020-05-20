from __future__ import print_function
import json
import sys
from adapt.intent import IntentBuilder
from adapt.engine import IntentDeterminationEngine
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.util.parse import extract_datetime
from datetime import datetime, timedelta
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools

import string
import pytz
#in the raspberry we add __main__.py for the authorization
UTC_TZ = u'+00:00'
SCOPES = ['https://www.googleapis.com/auth/calendar']
FLOW = OAuth2WebServerFlow(
    client_id='73558912455-smu6u0uha6c2t56n2sigrp76imm2p35j.apps.googleusercontent.com',
    client_secret='0X_IKOiJbLIU_E5gN3NefNns',
    scope='https://www.googleapis.com/auth/contacts.readonly',
    user_agent='Smart assistant box')
# TODO: Change "Template" to a unique name for your skill
class RegSkill(MycroftSkill):
    def __init__(self):
        super(RegSkill, self).__init__(name="Regskill")

    #def initialize(self):
        #add_event_intent = IntentBuilder('EventIntent') \
            #.require('Add') \
            #.require('Event') \
            #.require('Person') \
            #.optionally('Location') \
            #.optionally('time') \
            #.build()
        #self.register_intent(add_event_intent, self.createevent)
    @property
    def utc_offset(self):
        return timedelta(seconds=self.location['timezone']['offset'] / 1000)

    @intent_handler(IntentBuilder("add_event_intent").require('Add').require('Event').require('Person').optionally('Location').optionally('time').build())
    def createevent(self,message):
        #AUTHORIZE
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/opt/mycroft/skills/regskill.hanabouzid/client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

            # Refer to the Python quickstart on how to setup the environment:
            # https://developers.google.com/calendar/quickstart/python
            # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
            # stored credentials.
        # If the Credentials don't exist or are invalid, run through the
        # installed application flow. The Storage object will ensure that,
        # if successful, the good Credentials will get written back to a
        # file.
        storage = Storage('info.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid == True:
            credentials = tools.run_flow(FLOW, storage)

        # Create an httplib2.Http object to handle our HTTP requests and
        # authorize it with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)

        # Build a service object for interacting with the API. To get an API key for
        # your application, visit the Google API Console
        # and look at your application's credentials page.
        people_service = build(serviceName='people', version='v1', http=http)
        # To get the person information for any Google Account, use the following code:
        # profile = people_service.people().get('people/me', pageSize=100, personFields='names,emailAddresses').execute()
        # To get a list of people in the user's contacts,
        # results = service.people().connections().list(resourceName='people/me',personFields='names,emailAddresses',fields='connections,totalItems,nextSyncToken').execute()
        results = people_service.people().connections().list(resourceName='people/me', pageSize=100,
                                                             personFields='names,emailAddresses,events',
                                                             fields='connections,totalItems,nextSyncToken').execute()
        connections = results.get('connections', [])
        print("connections:", connections)
        utt = message.data.get("utterance", None)
        # extract the location
        #location = message.data.get("Location", None)
        print(utt)
        lister = utt.split(" in ")
        lister2 = lister[1].split(" starts ")
        location = lister2[0]
        print(location)
        strtdate = lister2[1]
        st = extract_datetime(strtdate)
        st = st[0] - self.utc_offset
        et = st + timedelta(hours=1)
        datestart = st.strftime('%Y-%m-%dT%H:%M:00')
        datend = et.strftime('%Y-%m-%dT%H:%M:00')
        datestart += UTC_TZ
        datend += UTC_TZ
        print(datestart)
        print(datend)
        listp=[]
        list1 = utt.split("with ")
        list2 = list1[1].split(" in")
        if ("and") in list2[0]:
            listp = list2[0].split(" and ")
        else:
            listp.append(list2[0])
        print(listp)
        #extraire l'email des invitees et de la salle
        attendee = []
        namerooms = ['midoune room','aiguilles room','barrouta room','kantaoui room','gorges room','ichkeul room','khemir room','tamaghza room','friguia room','ksour room','medeina room','thyna room']
        emailrooms = ["focus-corporation.com_3436373433373035363932@resource.calendar.google.com","focus-corporation.com_3132323634363237333835@resource.calendar.google.com","focus-corporation.com_3335353934333838383834@resource.calendar.google.com","focus-corporation.com_3335343331353831343533@resource.calendar.google.com","focus-corporation.com_3436383331343336343130@resource.calendar.google.com","focus-corporation.com_36323631393136363531@resource.calendar.google.com","focus-corporation.com_3935343631343936373336@resource.calendar.google.com","focus-corporation.com_3739333735323735393039@resource.calendar.google.com","focus-corporation.com_3132343934363632383933@resource.calendar.google.com","focus-corporation.com_@resource.calendar.google.com","focus-corporation.com_@resource.calendar.google.com","focus-corporation.com_@resource.calendar.google.com"]
        indiceroom =None
        for j, e in enumerate(namerooms):
            if e == location:
                indiceroom=j
        if(indiceroom != None):
            #register the room mail
            idmailr = emailrooms[indiceroom]
            #freebusy
            # freebusy
            body = {
                "timeMin": datestart,
                "timeMax": datend,
                "timeZone": 'America/Los_Angeles',
                "items": [{"id": idmailr}]
            }
            eventsResult = service.freebusy().query(body=body).execute()
            cal_dict = eventsResult[u'calendars']
            print(cal_dict)
            for cal_name in cal_dict:
                print(cal_name, ':', cal_dict[cal_name])
                statut = cal_dict[cal_name]
                for i in statut:
                    if (i == 'busy' and statut[i] == []):
                        self.speak_dialog("roomfree",data={"room":location})
                        # ajouter l'email de x ala liste des attendee
                        attendee.append(idmailr)
                    elif (i == 'busy' and statut[i] != []):
                        self.speak_dialog("roombusy",data={"room":location})
        else:
            self.speak_dialog("notRoom")

        # liste de contacts
        nameliste = []
        adsmails = []
        for person in connections:
            emails = person.get('emailAddresses', [])
            adsmails.append(emails[0].get('value'))
            names = person.get('names', [])
            nameliste.append(names[0].get('displayName'))
        #recherche des mails des invités
        n = len(listp)
        for i in listp:
            indiceperson=None
            for j, e in enumerate(nameliste):
                if e == i:
                    att=i
                    indiceperson=j
            if(indiceperson!=None):
                self.speak_dialog("exist")
                idmailp=adsmails[indiceperson]
                print(idmailp)
                print(att)
                    #freebusy
                body = {
                    "timeMin": datestart,
                    "timeMax": datend,
                    "timeZone": 'America/Los_Angeles',
                    "items": [{"id":idmailp}]
                }
                eventsResult = service.freebusy().query(body=body).execute()
                cal_dict = eventsResult[u'calendars']
                print(cal_dict)
                for cal_name in cal_dict:
                    print(cal_name, ':', cal_dict[cal_name])
                    statut = cal_dict[cal_name]
                    for i in statut:
                        if (i == 'busy' and statut[i] == []):
                            self.speak_dialog("attendeefree",data={"att":att})
                            # ajouter l'email de x ala liste des attendee
                            attendee.append(idmailp)
                        elif (i == 'busy' and statut[i] != []):
                            self.speak_dialog("attendeebusy",data={"att":att})
                            n -= 1
            else:
                self.speak_dialog("notExist")
            # creation d'un evenement
        attendeess = []
        for i in range(len(attendee)):
            email = {'email': attendee[i]}
            attendeess.append(email)
        event = {
            'summary':'meeting',
            'location': location,
            'description': '',
            'start': {
                'dateTime': datestart,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': datend,
                'timeZone': 'America/Los_Angeles',
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=1'
            ],
            'attendees': attendeess,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        if n == 0:
            self.speak_dialog("cancellEvent")
        elif n == len(listp):
            event = service.events().insert(calendarId='primary', sendNotifications=True,body=event).execute()
            print('Event created: %s' % (event.get('htmlLink')))
            self.speak_dialog("eventCreated")
        else :
            res=self.get_response('Some of the attendees are busy would you like to continue creating the event yes or no?')
            if res == 'yes':
                event = service.events().insert(calendarId='primary', sendNotifications=True, body=event).execute()
                print('Event created: %s' % (event.get('htmlLink')))
                self.speak_dialog("eventCreated")
            elif res == 'no':
                self.speak_dialog("eventCancelled")
def create_skill():
    return RegSkill()