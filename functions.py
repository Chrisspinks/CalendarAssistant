from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import os
import pyttsx3
import speech_recognition as sr
import pytz

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']   # read/write scope
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAY_EXTNS = ['st', 'th', 'rd', 'nd']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
triggers = ['do i have', 'am i busy', 'whats happening', 'plans', 'schedule', 'whats on']


def speak(output):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 3.0)
    engine.say(output)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
            # print(said)
        except Exception as e:
            print("Exception" + str(e))
    return said


def authenticate_google():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token, protocol=2)

    service = build('calendar', 'v3', credentials=creds)

    return service


def get_events(day, service):
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        if len(events) == 1:
            speak(f'you have {len(events)} event.')
        else:
            speak(f'you have {len(events)} events.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split('T')[1].split('-')[0])
            minute = start_time.split(':')[1]
            if minute == '00':
                minute = ''
            if int(start_time.split(':')[0]) < 12:
                start_time = start_time.split(':')[0] + minute + 'a m'
            else:
                start_time = str(int(start_time.split(':')[0]) - 12) + minute + 'pm'

            speak(event['summary'] + 'at' + start_time)


def add_to_calendar(date, time, description):
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)
    GCAL = discovery.build('calendar', 'v3', http=creds.authorize(Http()))

    if date.month > 10 or date.month < 4 or (date.month == 10 and date.day > 6) or (date.month == 4 and date.day < 5):
        GMT_OFF = '+11:00'
    else:
        GMT_OFF = '+10:00'  # PDT/MST/GMT Sydney time

    event_start = str(date) + 'T' + str(time) + '%s'
    temp = event_start.split('%')[0]
    temp = temp.replace('T', ' ', 1)
    temp = datetime.datetime.strptime(temp, "%Y-%m-%d %H:%M:%S")
    event_end = str(temp + datetime.timedelta(hours=1))
    event_end = event_end.split(' ')[0] + 'T' + event_end.split(' ')[1] + '%s'

    EVENT = {
        'summary': description,
        'start': {'dateTime': event_start % GMT_OFF},
        'end': {'dateTime': event_end % GMT_OFF},
    }

    e = GCAL.events().insert(calendarId='primary', sendNotifications=True, body=EVENT).execute()
    print('''*** %r event added: Start: %s End:   %s''' % (e['summary'].encode('utf-8'), e['start']['dateTime'],
                                                           e['end']['dateTime']))


def get_time(text):
    time = hours = minutes = seconds = ''
    if 'a.m.' not in text and 'p.m.' not in text:
        speak('Sorry, I didnt get the time of the event')
        return 0
    elif 'a.m.' in text:
        result = text.split(' a.')[0]
        for i, char in enumerate(reversed(result)):
            if char == ' ':
                index = len(result) - i
                time = result[index:]
                break
        if ':' in time:
            hours = int(time.strip(':')[0])
            minutes = time.split(':')[1]
            seconds = '00'
        else:
            hours = int(time)
            minutes = '00'
            seconds = '00'
        if hours == 12:
            hours = 0

    elif 'p.m.' in text:
        result = text.split(' p.')[0]
        for i, char in enumerate(reversed(result)):
            if char == ' ':
                index = len(result) - i
                time = result[index:]
                break
        if ':' in time:
            hours = int(time.strip(':')[0]) + 12
            minutes = time.split(':')[1]
            seconds = '00'
        else:
            hours = int(time) + 12
            minutes = '00'
            seconds = '00'
        if hours == 24:
            hours = 12
    time = str(hours) + ':' + minutes + ':' + seconds
    return time


def get_date(text):
        text = text
        today = datetime.date.today()

        if text.count('today') > 0:
            return today

        day = -1
        day_of_week = -1
        month = -1
        year = today.year

        for word in text.split():
            if word == 'tomorrow':
                day_of_week = today.weekday() + 1
            if word in MONTHS:
                month = MONTHS.index(word) + 1
            elif word in DAYS:
                day_of_week = DAYS.index(word)
            else:
                for ext in DAY_EXTNS:
                    found = word.find(ext)
                    if found > 0:
                        try:
                            day = int(word[:found])
                        except:
                            pass

        if month < today.month and month != -1:
            year += 1

        if day < today.day and month == -1 and day != -1:
            month += 1

        if month == -1 and day == -1 and day_of_week != -1:
            current_day_of_week = today.weekday()
            dif = day_of_week - current_day_of_week

            if dif < 0:
                dif += 7
            if 'next' in text or 'following' in text:
                dif += 7

            return today + datetime.timedelta(dif)

        if month != -1 and day != -1 and year != -1:
            return datetime.date(month=month, day=day, year=year)
        else:
            speak('Sorry, that didnt work')


def get_event_description(text):
    if 'a.m.' in text:
        description = text.split('a.m. ')[1]
    elif 'p.m.' in text:
        description = text.split('p.m. ')[1]
    else:
        description = 'error'
        speak('Sorry, I didnt get an event description')

    return description

