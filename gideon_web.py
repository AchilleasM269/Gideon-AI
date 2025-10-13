import streamlit as st
import wikipedia
import requests
import time
import random
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
SECRET_CODE = "676ebc8868d046dc914131347253009"
SOS_CODE = "1234"
WEATHER_API_KEY = "676ebc8868d046dc914131347253009"
TYPING_DELAY = 0.02  # typing speed

# ---------------- HELPER FUNCTIONS ----------------
def type_text(text):
    """Simulates Gideon typing text."""
    typed = ""
    text_placeholder = st.empty()
    for char in text:
        typed += char
        text_placeholder.markdown(f"**Gideon:** {typed}█")
        time.sleep(TYPING_DELAY)
    text_placeholder.markdown(f"**Gideon:** {text}**")

def keyword_unlock():
    """Keyword unlock system."""
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return True

    st.title("🔒 Access Locked")
    keyword = st.text_input("Enter keyword to access", type="password")

    if keyword.lower() == "pineapple":
        st.session_state.user = "Achilleas"
        st.success("Access granted. Welcome Achilleas!")
        time.sleep(1)
        st.rerun()
    elif keyword.lower() == "apple":
        st.session_state.user = "George"
        st.success("Access granted. Welcome George!")
        time.sleep(1)
        st.rerun()
    elif keyword:
        st.error("Wrong keyword. Try again.")
    return False

def get_weather(city):
    """Fetch weather from WeatherAPI."""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        location = data["location"]["name"]
        temp = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        return f"The weather in {location} is {condition} with {temp}°C."
    else:
        return "Couldn't retrieve weather data."

def get_wikipedia_summary(query):
    """Fetch summary from Wikipedia."""
    try:
        return wikipedia.summary(query, sentences=2)
    except wikipedia.DisambiguationError as e:
        return f"Multiple results found: {e.options[:5]}"
    except wikipedia.PageError:
        return "No Wikipedia page found for that topic."

def get_joke():
    """Return a random joke."""
    jokes = [
        "Why don’t scientists trust atoms? Because they make up everything!",
        "I told my computer I needed a break... and it said 'No problem, I'll go to sleep.'",
        "Parallel lines have so much in common... it’s a shame they’ll never meet.",
    ]
    return random.choice(jokes)

def translate_text(text, target_lang):
    """Translate text using GoogleTranslator."""
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception:
        return "Translation failed."

# ---------------- MAIN AI LOOP ----------------
def ai_loop():
    user_name = st.session_state.user
    st.title(f"🤖 Hello {user_name}, I'm Gideon")
    user_input = st.text_input("Ask me something:", key="user_input")

    if not user_input:
        return

    if user_input.lower() == "exit":
        type_text("Goodbye!")
        st.session_state.user = None
        time.sleep(1)
        st.rerun()

    elif user_input.lower() == "sos":
        type_text("⚠️ SOS activated! Gideon locked.")
        code = st.text_input("Enter unlock code:", type="password", key="sos_input")
        if code:
            if code == SOS_CODE:
                type_text("System unlocked. Refreshing...")
                time.sleep(1)
                st.rerun()
            else:
                type_text("Wrong code.")
        return

    # Shortcuts
    if user_input.lower().startswith("what's") or user_input.lower().startswith("whats"):
        expr = user_input.lower().replace("what's", "").replace("whats", "").strip("? ")
        try:
            result = eval(expr)
            type_text(f"The answer is {result}")
        except:
            type_text("Invalid math expression.")
        return

    elif user_input.lower().startswith("weather in"):
        city = user_input.split("in", 1)[1].strip()
        reply = get_weather(city)
        type_text(reply)
        return

    elif user_input.lower().startswith("wiki"):
        topic = user_input.split("wiki", 1)[1].strip()
        reply = get_wikipedia_summary(topic)
        type_text(reply)
        return

    elif user_input.lower().startswith("translate"):
        try:
            _, text, lang = user_input.split(" ", 2)
            reply = translate_text(text, lang)
        except:
            reply = "Use format: translate <text> <language>"
        type_text(reply)
        return

    elif "joke" in user_input.lower():
        reply = get_joke()
        type_text(reply)
        return

    else:
        type_text("I can tell jokes, do math, get Wikipedia info, translate text, or show the weather!")

# ---------------- APP START ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    ai_loop()
else:
    if keyword_unlock():
        ai_loop()
