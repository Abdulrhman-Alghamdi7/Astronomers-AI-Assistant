from flask import Flask, render_template, request, jsonify
from datetime import datetime
import csv
import openai
from skyfield.api import load, Topos, utc
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from dotenv import load_dotenv
import os

app = Flask(__name__)

def configure():
    load_dotenv()

configure()
api_key = os.getenv('api_key')

data = []

with open('/Users/abdulrhmanalghamdi/Library/Mobile Documents/com~apple~CloudDocs/programming💻/AstronomersAiAssistant/web/astronomicalEvents.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        data.append(row)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    question = request.json['question']
    prompt = f"consider that you are an astronomer who can answer any astronomical or scientific question, but you cannot answer any non-astronomical or scientific question. You answer with (this is outside the scope of my knowledge). Based on the previous information, answer the following question: {question} within 500 characters."
    answer = ask_gpt3_5_chat(prompt)
    return jsonify({'answer': answer})

@app.route('/object', methods=['POST'])
def object_info():
    obj_name = request.json['object_name']
    info = get_celestial_body_info(obj_name)
    return jsonify({'info': info})

@app.route('/events', methods=['POST'])
def events():
    start_date = request.json['start_date']
    end_date = request.json['end_date']
    events = get_events_in_date_range(start_date, end_date)
    return jsonify({'events': events})

def askfordistance(a, model="gpt-3.5-turbo", max_tokens=10):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a chatbot."},
                {"role": "user", "content": f"give me just the distance from earth to {a} in 10 characters max"}
            ],
            max_tokens=max_tokens,
            api_key=api_key
        )

        if response.choices:
            return response.choices[0].message["content"].strip()
        else:
            return "No answer provided."
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
def askforinfo(a, model="gpt-3.5-turbo", max_tokens=100):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a chatbot."},
                {"role": "user", "content": f"give me a summary about {a} in 100 characters max"}
            ],
            max_tokens=max_tokens,
            api_key=api_key
        )

        if response.choices:
            return response.choices[0].message["content"].strip()
        else:
            return "No answer provided."

    except Exception as e:
        return f"An error occurred: {str(e)}"
r = []
def get_user_location():
    
    try:
        geolocator = Nominatim(user_agent="get_user_location")
        location = geolocator.geocode("")

        if location:
            return location.latitude, location.longitude
        else:
            r.append("\nUnable to determine your location. Using default location(0,0).")
            default_latitude = 0.0
            default_longitude = 0.0
            return default_latitude, default_longitude
    except GeocoderTimedOut:
        r.append("\nGeocoding service timed out. Unable to determine your location. Using default location(0,0).")
        default_latitude = 0.0
        default_longitude = 0.0
        return default_latitude, default_longitude

def get_celestial_body_info(body_name):
    planets = load('de421.bsp')

    object = planets[body_name]

    observer_location = get_user_location()

    if observer_location is not None:
        observer_latitude, observer_longitude = observer_location

        ts = load.timescale()
        time = ts.now()
        
        observer = Topos(observer_latitude, observer_longitude)

        observer_position = observer.at(time)
        object_position = object.at(time)

        separation = object_position.separation_from(observer_position)

        r.append(f'\nRight Ascension: {object_position.radec()[0].hours}\nDeclination: {object_position.radec()[1].degrees}\nseparation: {separation.degrees}')
        return f"Name: {body_name}\nAbout: {askforinfo(body_name)} {''.join(r)}"
    else:
        return None

def get_events_in_date_range(start_date, end_date):
    events_in_range = []
    start_date = datetime.strptime(start_date, '%Y/%m/%d')
    end_date = datetime.strptime(end_date, '%Y/%m/%d')
    for event in data[1:]:  # Skip the header row
        event_start_date = datetime.strptime(event[2].strip(), '%Y/%m/%d')
        event_end_date = datetime.strptime(event[3].strip(), '%Y/%m/%d')
        if start_date <= event_end_date and end_date >= event_start_date:
            events_in_range.append(event[1:])
    s = ''
    for i in events_in_range:
        s += f'Event name: {i[0]}\nStart date: {i[1]}\nEnd date: {i[2]}\nEvent description: {i[3]}\n\n'
    return s

def ask_gpt3_5_chat(question, model="gpt-3.5-turbo", max_tokens=500):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a chatbot."},
                {"role": "user", "content": question}
            ],
            max_tokens=max_tokens,
            api_key=api_key
        )

        if response.choices:
            return response.choices[0].message["content"].strip()
        else:
            return "No answer provided."

    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
