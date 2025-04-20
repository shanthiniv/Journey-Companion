import requests
import pyttsx3
import speech_recognition as sr
import wikipedia
import pyautogui
import google.generativeai as genai
import psutil
from youtubesearchpython import VideosSearch
import yt_dlp
from ecapture import ecapture as ec
import screen_brightness_control as sbc
from pytube import Search


try:
    from gui_main import write_to_gui
except ImportError:
    def write_to_gui(msg):  # fallback for terminal use
        print(msg)


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API Keys Configuration
NEWS_API_KEY = "add your key"
NEWS_API_URL = "add your key"
ORS_API_KEY = 'add your key'
GEMINI_API_KEY = "add your key"
WEATHER_API_KEY = "add your key"


FROM_ADDRESS = "xxxxxxxx"  # Change to your Gmail
PASSWORD = "yyyyyyy"  # Use an app password for security


engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 160)

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)


expenses = {
    'food': {'transactions': [], 'budget': 5000},
    'transport': {'transactions': [], 'budget': 3000},
    'shopping': {'transactions': [], 'budget': 4000},
    'bills': {'transactions': [], 'budget': 6000},
    'entertainment': {'transactions': [], 'budget': 2000},
    'other': {'transactions': [], 'budget': 1000}
}


contacts = {
    'john': 'john.doe@gmail.com',
    'alice': 'alice123@gmail.com'
}

last_joke = None
last_riddle = None

def speak(text):
    """Convert text to speech, print it, and show in GUI if available."""
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    output = f"Assistant: {text}"
    print(output, flush=True)
    write_to_gui(output)  # 👈 add this line
    engine.say(text)
    engine.runAndWait()

def wish_me():
    """Greet the user based on time of day"""
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Hello, Good Morning")
    elif 12 <= hour < 18:
        speak("Hello, Good Afternoon")
    else:
        speak("Hello, Good Evening")

def listen():
    """Listen to user's voice and return the recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        msg = "Listening..."
        print(msg, flush=True)
        write_to_gui(msg)

        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            output = f"You said: {command}"
            print(output, flush=True)
            write_to_gui(output)

            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand. Please try again.")
            return None
        except sr.RequestError:
            speak("Error: Check your internet connection.")
            return None
        except sr.WaitTimeoutError:
            speak("Timed out. Please try again.")
            return None

def listen_for_email():
    """ Function to listen to the user's voice command for email specific tasks """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for email command...")
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower().strip()
            print(f"You said: {command}")
            return command

        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that. Please repeat.")
            return listen_for_email()

        except sr.RequestError:
            speak("Sorry, I'm having trouble connecting.")
            return ""


def add_expense():
    """Adds a new expense through voice interaction"""
    speak("Which category? You can say food, transport, shopping, bills, entertainment or other")
    category = listen()

    if not category or category not in expenses:
        speak("Sorry, I didn't understand the category. Please try again.")
        return

    speak(f"How much did you spend on {category}? Say the amount in numbers.")
    amount_str = listen()

    try:
        amount = float(''.join(filter(str.isdigit, amount_str)))
        expenses[category]['transactions'].append({
            'amount': amount,
            'date': datetime.now()
        })
        speak(f"Added {amount} rupees to {category} expenses.")
        check_budget(category)
    except:
        speak("Sorry, I couldn't understand the amount. Please try again.")

def check_budget(category):
    """Checks if spending is nearing budget limit"""
    spent = sum(t['amount'] for t in expenses[category]['transactions'])
    budget = expenses[category]['budget']
    remaining = budget - spent

    if remaining <= 0:
        speak(f"Warning! You've exceeded your {category} budget by {-remaining} rupees!")
    elif remaining <= budget * 0.2:
        speak(f"Alert! You only have {remaining} rupees left in your {category} budget.")
    elif remaining <= budget * 0.5:
        speak(f"Reminder: You have {remaining} rupees remaining in your {category} budget.")

def get_expense_summary(timeframe='all'):
    """Generates expense summary for different time periods"""
    if not any(v['transactions'] for v in expenses.values()):
        speak("You haven't recorded any expenses yet.")
        return

    total_spent = 0
    summary = f"Here's your {timeframe} expense summary: "

    for category, data in expenses.items():
        if timeframe == 'weekly':
            transactions = [t for t in data['transactions']
                            if t['date'] > datetime.now() - timedelta(days=7)]
        elif timeframe == 'monthly':
            transactions = [t for t in data['transactions']
                            if t['date'].month == datetime.now().month]
        else:
            transactions = data['transactions']

        if transactions:
            category_total = sum(t['amount'] for t in transactions)
            total_spent += category_total
            budget_percent = (category_total / data['budget']) * 100
            summary += (f"You spent {category_total} rupees on {category} "
                            f"which is {budget_percent:.0f}% of your budget. ")

    summary += f"Your total {timeframe} expenses are {total_spent} rupees."
    speak(summary)

def set_budget():
    """Allows user to set budgets for categories"""
    speak("Which category would you like to set budget for?")
    category = listen()

    if not category or category not in expenses:
        speak("Invalid category. Please try again.")
        return

    speak(f"What should be the monthly budget for {category}? Say the amount in numbers.")
    amount_str = listen()

    try:
        amount = float(''.join(filter(str.isdigit, amount_str)))
        expenses[category]['budget'] = amount
        speak(f"Budget for {category} set to {amount} rupees.")
    except:
        speak("Sorry, I couldn't understand the amount. Please try again.")

def handle_map_command(command):
    if "navigate to" in command:
        place = command.replace("navigate to", "").strip()
        if place:
            speak(f"Opening route to {place}...")
            webbrowser.open(f"https://www.google.com/maps/dir//{place}")
        else:
            speak("Please specify a destination.")

    elif "open route" in command or "open location" in command:
        match = re.search(r"(?:open route|open location) from (.?) to (.)", command)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            speak(f"Opening route from {origin} to {destination}...")
            webbrowser.open(f"https://www.google.com/maps/dir/{origin}/{destination}")
        else:
            speak("Please say 'Open route from place A to place B'.")

    elif "how far is" in command:
        match = re.search(r"how far is (.?) from (.)", command)
        if match:
            destination = match.group(1).strip()
            origin = match.group(2).strip()
            speak(f"Calculating distance from {origin} to {destination}...")
            eta, distance = get_eta(origin, destination)
            if eta and distance:
                minutes = round(eta / 60)
                km = round(distance / 1000, 2)
                speak(f"It's approximately {km} kilometers and will take about {minutes} minutes.")
            else:
                speak("Please say 'How far is place A from place B'.")

    elif "nearby" in command:
        keyword = command.replace("find nearby", "").replace("show nearby", "").strip()
        if keyword:
            speak(f"Showing nearby {keyword}...")
            webbrowser.open(f"https://www.google.com/maps/search/{keyword}+near+me")
        else:
            speak("Please specify what you're looking for nearby.")

def get_eta(origin, destination):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        "coordinates": [get_coordinates(origin), get_coordinates(destination)]
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        if 'routes' not in data or not data['routes']:
            speak("Sorry, I couldn't get the route details.")
            return None, None

        duration = data['routes'][0]['summary']['duration']
        distance = data['routes'][0]['summary']['distance']
        return duration, distance
    except Exception as e:
        speak(f"Error retrieving route details: {e}")
        return None, None

def get_coordinates(place_name):
    url = f"https://api.openrouteservice.org/geocode/search?api_key={ORS_API_KEY}&text={place_name}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'features' in data and data['features']:
            coords = data['features'][0]['geometry']['coordinates']
            return coords
        else:
            speak(f"Couldn't find location: {place_name}")
            return None
    except Exception as e:
        speak(f"Error retrieving coordinates: {e}")
        return None


def clean_email_address(email_text):
    """ Convert spoken email to valid format """
    email_text = email_text.replace(" at ", "@").replace(" dot ", ".").replace(" underscore ", "_")
    return email_text.replace(" ", "")  # Remove extra spaces

def send_email(to_address, subject, message_body):
    """Sends an email using the configured Gmail account."""
    msg = MIMEMultipart()
    msg['From'] = FROM_ADDRESS
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(message_body, 'plain'))

    try:
        # Connect to Gmail SMTP server and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(FROM_ADDRESS, PASSWORD)
        server.send_message(msg)
        server.quit()

        speak("Email has been sent successfully!")

    except Exception as e:
        speak("Sorry, I was unable to send the email.")
        print(f"Error: {e}")

def ask_gemini(query):
    """ Gets responses from Gemini AI for general queries, limited to 2 lines """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")  # Load Gemini Model
        response = model.generate_content(query)  # Generate response
        answer = response.text
        # Limit response to 2 lines
        answer = "\n".join(answer.splitlines()[:2])
        speak(answer)  # Speak the response
        print(f"AI Response: {answer}") # Print response
        return answer
    except Exception as e:
        error_msg = f"Error with Gemini AI: {e}"
        speak("Sorry, I couldn't process that request.")
        print(error_msg)
        return error_msg


def system_status():
    """Check and report system status"""
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "Unknown"
    
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    status = f"Battery is at {battery_percent} percent. CPU usage is at {cpu_usage} percent. Memory usage is at {memory_usage} percent."
    return status

def adjust_volume(action):
    """Adjust system volume"""
    if action == "increase":
        pyautogui.press("volumedown")  # Decrease volume
    elif action == "decrease":
        pyautogui.press("volumeup")  # Increase volume
    speak(f"Volume has been {action}d.")
    print(f"Volume {action}d.")

def adjust_brightness(action):
    """Adjust screen brightness"""
    try:
        current_brightness = sbc.get_brightness(display=0)[0]  # Get current brightness
        if "increase" in action:
            new_brightness = min(current_brightness + 20, 100)
        elif "decrease" in action:
            new_brightness = max(current_brightness - 20, 0)
        else:
            return "Please specify increase or decrease."

        sbc.set_brightness(new_brightness, display=0)  # Set new brightness
        speak(f"Brightness adjusted to {new_brightness} percent.")
        print(f"Brightness adjusted to {new_brightness} percent.")
    except Exception as e:
        speak(f"Failed to adjust brightness: {str(e)}")
        print(f"Failed to adjust brightness: {str(e)}")

def open_application(app_name):
    """Open specified application"""
    try:
        if app_name.lower() == "notepad":
            subprocess.run("notepad", shell=True)
            speak("Opening Notepad.")
        elif app_name.lower() == "calculator":
            subprocess.run("calc", shell=True)
            speak("Opening Calculator.")
        elif app_name.lower() == "microsoft word":
            os.system("start winword")  # Opens Microsoft Word
            speak("Opening Microsoft Word.")
        elif app_name.lower() == "microsoft excel":
            os.system("start excel")  # Opens Microsoft Excel
            speak("Opening Microsoft Excel.")
        elif app_name.lower() == "microsoft powerpoint":
            os.system("start powerpnt")  # Opens Microsoft PowerPoint
            speak("Opening Microsoft PowerPoint.")
        elif app_name.lower() == "microsoft edge":
            os.system("start msedge")  # Opens Microsoft Edge
            speak("Opening Microsoft Edge.")
        elif app_name.lower() == "settings":
            os.system("start ms-settings:")  # Opens Windows Settings
            speak("Opening PC Settings.")
        else:
            speak("Sorry, I couldn't find that application.")
    except Exception as e:
        speak("Sorry, I couldn't open the application.")
        print(f"Error opening application: {e}")

def play_music(song_name):
    """ Searches YouTube and plays the first song automatically """
    search_query = f"ytsearch:{song_name}"  # Search query for yt_dlp

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(search_query, download=False)['entries'][0]
            video_url = info['webpage_url']  # Get video link
            speak(f"Playing {song_name} on YouTube")
            webbrowser.open(video_url)
            print(f"Playing: {video_url}")
    except Exception as e:
        speak("Sorry, I couldn't find the song.")
        print("Error finding song:", e)

def tell_joke():
    """Tell a random joke"""
    global last_joke
    jokes = [
        "Why don't skeletons fight each other? They don't have the guts.",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "Why don't programmers like nature? It has too many bugs.",
        "Why did the computer go to the doctor? It had a virus.",
        "Why did the scarecrow win an award? Because he was outstanding in his field.",
        "I asked the librarian if the library had any books on paranoia. She whispered, 'They're right behind you.'",
        "I told my computer I needed a break, and it froze."
    ]
    
  
    joke = random.choice(jokes)
    while joke == last_joke:
        joke = random.choice(jokes)
    
    last_joke = joke
    speak(joke)
    print(joke)

def tell_riddle():
    """Tell a riddle and check the answer"""
    global last_riddle
    riddles = [
        {"question": "What has keys but can't open locks?", "answer": "A piano."},
        {"question": "What can travel around the world while staying in the corner?", "answer": "A stamp."},
        {"question": "What is full of holes but still holds a lot of weight?", "answer": "A net."},
    ]
    
    riddle = random.choice(riddles)
    while riddle == last_riddle:
        riddle = random.choice(riddles)
    
    last_riddle = riddle
    speak(f"Here's a riddle: {riddle['question']}")
    print(f"Riddle: {riddle['question']}")
    answer = listen()
    
    if answer and answer.lower() == riddle["answer"].lower():
        speak("Correct!")
        print("Correct!")
    else:
        speak(f"Wrong. The correct answer is: {riddle['answer']}")
        print(f"Wrong. The correct answer is: {riddle['answer']}")


def search_google(query):
    """ Searches Google and opens the results """
    search_url = f"https://www.google.com/search?q={query}"
    webbrowser.open(search_url)
    speak(f"Here are the search results for {query}")

def get_top_news(topic):
    """Fetch top 3 news headlines for a given topic"""
    params = {
        "q": topic,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3
    }

    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code != 200:
        return ["Error: Unable to fetch news."]

    news_data = response.json()
    return [article["title"] for article in news_data.get("articles", [])[:3]] or ["No relevant news found."]

def speak_news():
    """Fetch and read top 3 news based on user's topic"""
    speak("What topic do you want news about?")
    topic = listen()
    if topic:
        news_list = get_top_news(topic)
        news_summary = f"Here are the top 3 news about {topic}:\n"
        for i, news in enumerate(news_list, 1):
            news_summary += f"{i}. {news}\n"
        speak(news_summary)

def get_wikipedia_info(topic):
    """Fetch summary from Wikipedia and read it out loud"""
    try:
        summary = wikipedia.summary(topic, sentences=10)
        speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        speak("There are multiple results. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("Sorry, I couldn't find any information.")


def get_weather():
    """ Fetch weather information from OpenWeatherMap API """
    speak("Please tell me the city name.")
    city_name = listen()

    if not city_name:
        speak("Sorry, I didn't get the city name.")
        return

    base_url = "https://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city_name}&appid={WEATHER_API_KEY}&units=metric"

    try:
        response = requests.get(complete_url)
        x = response.json()

        if x.get("cod") != 200:
            speak("City Not Found. Please try again.")
            return

        y = x.get("main", {})
        current_temperature = y.get("temp", "N/A")
        current_humidity = y.get("humidity", "N/A")

        z = x.get("weather", [{}])
        weather_description = z[0].get("description", "N/A")

        speak(f"Temperature is {current_temperature} degree Celsius. "
              f"Humidity is {current_humidity} percent. "
              f"Weather description: {weather_description}.")
        
        print(f"Temperature: {current_temperature}°C")
        print(f"Humidity: {current_humidity}%")
        print(f"Weather: {weather_description}")

    except requests.exceptions.RequestException as e:
        speak("Sorry, I couldn't fetch the weather data.")
        print(f"Request error: {e}")
    except KeyError:
        speak("Sorry, I couldn't find weather details for this location.")
        print("Error: Unexpected response format. Check the API response.")


def emergency_assistance():
    """Provide emergency contacts and nearby hospitals"""
    emergency_contacts = {
        "Police": "100",
        "Ambulance": "108",
        "Fire": "101",
        "Women Helpline": "1091",
        "Child Helpline": "1098",
        "Cyber Crime": "1930"
    }

    speak("Emergency contacts in Tamil Nadu are as follows. "
          "Police can be reached at 100, Ambulance at 108, and Fire Services at 101. "
          "For women's safety, call 1091, and for child helpline, dial 1098.")

def take_notes():
    """Open Notepad and take notes using voice input"""
    subprocess.Popen("notepad.exe")
    time.sleep(2)

    speak("I'm listening, please dictate your notes.")
    notes = listen()

    if notes:
        pyautogui.write(notes, interval=0.1)
        speak("Your notes have been taken successfully!")

def take_photo():
    """Take a photo using the webcam"""
    ec.capture(0, "robo camera", "img.jpg")
    speak("Photo has been taken and saved.")

def get_time():
    """Get current time"""
    strTime = datetime.datetime.now().strftime("%H:%M:%S")
    speak(f"The time is {strTime}")


def process_command(command):
    """Process user command and call the appropriate function"""
    if not command:
        return

   
    if "goodbye" in command or "ok bye" in command or "stop" in command:
        speak('Your assistant is shutting down. Goodbye!')
        sys.exit()
    elif "log off" in command or "sign out" in command:
        speak("Ok, your PC will log off in 10 seconds. Make sure you exit all applications.")
        subprocess.call(["shutdown", "/l"])
    elif "who are you" in command or "what can you do" in command:
        speak('I am your personal assistant. I can open websites, search Wikipedia, predict weather, play songs, manage expenses, help with navigation, send emails, and much more!')
    elif "who made you" in command or "who created you" in command:
        speak("I was built by Shanthini")
    
   
    elif "take notes" in command:
        take_notes()
    elif "emergency assistance" in command or "help me" in command:
        emergency_assistance()
    elif 'time' in command:
        get_time()
    elif "camera" in command or "take a photo" in command:
        take_photo()
    

    elif "today's news" in command or "news" in command:
        speak_news()
    elif "wikipedia about" in command:
        topic = command.replace("wikipedia about", "").strip()
        if topic:
            get_wikipedia_info(topic)
    elif "weather" in command:
        get_weather()
    elif 'web news' in command:
        webbrowser.open_new_tab("https://timesofindia.indiatimes.com/home/headlines")
        speak('Here are some headlines from the Times of India. Happy reading!')
        time.sleep(6)
    

    elif "navigate to" in command or "open route" in command or "how far is" in command or "nearby" in command:
        handle_map_command(command)
    
    # Expense tracker commands
    elif 'add expense' in command:
        add_expense()
    elif 'expense summary' in command:
        get_expense_summary()
    elif 'weekly summary' in command:
        get_expense_summary('weekly')
    elif 'monthly summary' in command:
        get_expense_summary('monthly')
    elif 'set budget' in command:
        set_budget()
    elif 'reset expenses' in command:
        global expenses
        expenses = {k: {'transactions': [], 'budget': v['budget']} for k, v in expenses.items()}
        speak("All expenses have been reset. Budgets remain unchanged.")
    
  
    elif "send email" in command:
        try:
            speak("Who is the recipient?")
            recipient_name = listen()

            if recipient_name in contacts:
                to_address = contacts[recipient_name]
            else:
                speak("Please say the full email address.")
                raw_email = listen()
                if raw_email:
                    to_address = clean_email_address(raw_email)
                else:
                    speak("Couldn't get the recipient's email address.")
                    return

            speak("What is the subject of your email?")
            subject = listen()
            if not subject:
                speak("Subject cannot be empty. Please try again.")
                return

            speak("What should I say in your email?")
            message_body = listen()
            if not message_body:
                speak("Message body cannot be empty. Please try again.")
                return

            send_email(to_address, subject, message_body)

        except Exception as e:
            speak("Sorry, something went wrong while trying to send the email.")
            print(f"Error: {e}")

    elif "open gmail" in command:
        speak("Opening Gmail for you.")
        webbrowser.open_new_tab("https://mail.google.com")
        time.sleep(5)
    
 
    elif 'play' in command and 'song' in command:
        song_name = command.replace('play', '').replace('song', '').strip()
        play_music(song_name)
    elif 'joke' in command:
        tell_joke()
    elif 'riddle' in command:
        tell_riddle()
  
    elif 'increase volume' in command:
        adjust_volume("increase")
    elif 'decrease volume' in command:
        adjust_volume("decrease")
    elif 'increase brightness' in command:
        adjust_brightness("increase")
    elif 'decrease brightness' in command:
        adjust_brightness("decrease")
    elif "battery status" in command or "system status" in command:
        status = system_status()
        speak(status)
        print(status)
    

    elif 'open notepad' in command:
        open_application("notepad")
    elif 'open calculator' in command:
        open_application("calculator")
    elif 'open microsoft word' in command:
        open_application("microsoft word")
    elif 'open microsoft excel' in command:
        open_application("microsoft excel")
    elif 'open microsoft powerpoint' in command:
        open_application("microsoft powerpoint")
    elif 'open microsoft edge' in command:
        open_application("microsoft edge")
    elif 'open settings' in command:
        open_application("settings")
    elif 'open youtube' in command:
        webbrowser.open_new_tab("https://www.youtube.com")
        speak("YouTube is open now")
        time.sleep(5)
    elif 'open google' in command:
        webbrowser.open_new_tab("https://www.google.com")
        speak("Google Chrome is open now")
        time.sleep(5)
    elif "open stackoverflow" in command:
        webbrowser.open_new_tab("https://stackoverflow.com/login")
        speak("Here is Stack Overflow")
    
    # Search commands
    elif 'search' in command:
        statement = command.replace("search", "").strip()
        search_google(statement)
    
    # Gemini AI commands
    elif "assistant" in command:
        query = command.replace("assistant", "").strip()
        if query:
            ask_gemini(query)
        else:
            speak("Yes, how can I assist you?")
    
    else:
        help_text = ("I can: take notes, get news, provide emergency contacts, "
                     "help with navigation, manage expenses, send emails, play music, "
                     "tell jokes and riddles, control system volume and brightness, "
                     "open applications, search the web, and answer questions using AI. "
                     "For expenses, say 'add expense', 'expense summary', 'set budget', "
                     "or 'reset expenses'. For navigation, say 'navigate to', 'how far is', "
                     "or 'find nearby'. For emails, say 'send email' or 'open gmail'.")
        speak(help_text)



def main(write_callback=None):
    def speak(message):
        print("Assistant:", message)
        if write_callback:
            write_callback(f"Assistant: {message}")

    def listen():
        print("Listening...")
        if write_callback:
            write_callback("Listening...")
        # rest of your code...

