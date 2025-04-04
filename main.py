import time

import sqlite3

import numpy as np

import pyttsx3
from hx711 import HX711

from google.oauth2 import service_account
from googleapiclient.discovery import build

import RPi.GPIO as GPIO

WEIGHT_SENSOR_PIN = 17  
GPIO.setmode(GPIO.BCM)
GPIO.setup(WEIGHT_SENSOR_PIN, GPIO.IN)

engine = pyttsx3.init()
engine.setProperty('rate', 150) 

conn = sqlite3.connect('medication_log.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS medication_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        event_name TEXT,
        status TEXT
    )
''')
conn.commit()

# Constants
THRESHOLD = 0.8  
SLEEP_DURATION = 60 
SCALE_RATIO = 20500 

hx = HX711(dout_pin=17, pd_sck_pin=27)
hx.set_reading_format("MSB", "MSB")
hx.set_scale(SCALE_RATIO)
hx.tare()


def read_weight_sensor() -> float:
    weight = hx.get_weight(5)
    normalized_weight = weight / 100000  
    return normalized_weight


def detect_wake_up() -> bool:
    weight_initial = read_weight_sensor()
    time.sleep(SLEEP_DURATION)
    weight_after = read_weight_sensor()

    weight_diff = weight_initial - weight_after

    if weight_diff >= THRESHOLD:
        return True
    return False


def authenticate_google_calendar():
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=["https://www.googleapis.com/auth/calendar.readonly"])

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_upcoming_events(service):
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    medication_events = []
    for event in events:
        if 'medication' in event['summary'].lower():
            medication_events.append(event)
    return medication_events


def log_event(event_name, status):
    cursor.execute("INSERT INTO medication_log (date, event_name, status) VALUES (?, ?, ?)",
                   (time.strftime('%Y-%m-%d %H:%M:%S'), event_name, status))
    conn.commit()


def speak(text):
    engine.say(text)
    engine.runAndWait()


def main():
    print("System initializing...")
    speak("System initializing. Good morning!")
    service = authenticate_google_calendar()

    while True:
        if detect_wake_up():
            speak("Good morning! Today’s a good day to be energized, isn’t it?")
            medication_events = get_upcoming_events(service)

            if medication_events:
                for event in medication_events:
                    summary = event['summary']
                    start_time = event['start'].get('dateTime', event['start'].get('date'))
                    message = f"Reminder: {summary} at {start_time}."
                    speak(message)
                    log_event(summary, "reminded")
            else:
                speak("No medication reminders for today.")

            time.sleep(300) 
        else:
            time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        conn.close()
