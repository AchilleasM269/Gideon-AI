import streamlit as st
import wikipedia
import requests
import random
import time
import json
import os
from deep_translator import GoogleTranslator

# ========== CONFIG ==========
API_KEY = "676ebc8868d046dc914131347253009"
LOCK_FILE = "lock_state.json"
SECRET_CODE = "1234"

# ========== HELPER FUNCTIONS ==========
def type_text(text, delay=0.015):
    """Typing animation."""
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(f"**Gideon:** {typed}█")
        time.sleep(delay)
    placeholder.markdown(f"**Gideon:** {typed}")

def save_lock_state(locked: bool):
    with open(LOCK_FILE, "w") as f:
        json.dump({"locked": locked}, f)

def load_lock_state() -> bool:
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as f:
            data = json.load(f)
            return data.get("locked", False)
    return False

def is_math_expression(s):
    allowed_chars = "0123456789+-*/(). "
    return all(c in allowed_chars for c in s) and any(c.isdigit() for c in s)

def evaluate_math(expr):
    try:
        return eval(expr)
    except:
        return "Invalid math expression."

def tell_joke():
    jokes = [
        "Why did the math book look sad? Because it had too many problems!",
        "I told my computer I needed a break, and it said 'No problem, I’ll go to sleep.'",
        "Why did the robot go to the doctor? Because it had a virus!"
    ]
    return random.choice(jokes)

def get_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}"
        data = requests.get(url).json()
        if "current" in data:
            loc = data["location"]["name"]
            temp = data["current"]["temp_c"]
            condition = data["current"]["condition"]["text"]
            return f"The weather in {loc} is {condition} with {temp}°C."
        else:
            return "Couldn't retrieve weather data. Please check the city name."
    except:
        return "Error fetching weather data."

def get_wikipedia_summary(topic):
    try:
        return wikipedia.summary(topic, sentences=2)
    except:
        return "I couldn’t find anything about that on Wikipedia."

def translate_text(text, lang):
    try:
        translated = GoogleTranslator(source='auto', target=lang).translate(text)
        return translated
    except Exception as e:
        return f"Translation error: {e}"

# ========== STREAMLIT UI ==========
st.title("🤖 Gideon AI Assistant")

# Lock check
locked = load_lock_state()

if locked:
    st.warning("🔒 System is locked. Enter SOS code to unlock.")
    code = st.text_input("Enter unlock code", type="password")
    if st.button("Unlock"):
        if code == SECRET_CODE:
            save_lock_state(False)
            st.success("✅ System unlocked. Please refresh the page.")
        else:
            st.error("Wrong code.")
    st.stop()

# Keyword unlock
if "user" not in st.session_state:
    keyword = st.text_input("Enter keyword to access (pineapple/apple):")
    if st.button("Unlock"):
        if keyword.lower() == "pineapple":
            st.session_state["user"] = "Achilleas"
            type_text("Access granted.")
        elif keyword.lower() == "apple":
            st.session_state["user"] = "George"
            type_text("Access granted.")
        else:
            st.error("Wrong keyword. System locked.")
            save_lock_state(True)
            st.stop()
    st.stop()

user = st.session_state["user"]

st.write(f"Hello **{user}**, welcome to Gideon!")
prompt = st.text_input("Ask me something (math, weather, Wikipedia, joke, or translate):")

if prompt:
    user_input = prompt.strip()

    if user_input.lower() == "sos":
        type_text("SOS activated. System locked.")
        save_lock_state(True)
        st.stop()

    elif "weather" in user_input.lower():
        city = user_input.lower().replace("weather", "").strip()
        response = get_weather(city or "Athens")

    elif "translate" in user_input.lower():
        parts = user_input.split("to")
        if len(parts) == 2:
            text = parts[0].replace("translate", "").strip()
            lang = parts[1].strip().lower()
            response = translate_text(text, lang)
        else:
            response = "Please say: Translate [text] to [language]."

    elif "joke" in user_input.lower():
        response = tell_joke()

    elif "who is" in user_input.lower() or "what is" in user_input.lower():
        topic = user_input.replace("who is", "").replace("what is", "").strip()
        response = get_wikipedia_summary(topic)

    elif is_math_expression(user_input) or "what’s" in user_input.lower() or "what is" in user_input.lower():
        expr = user_input.lower().replace("what’s", "").replace("what is", "").replace("?", "").strip()
        response = f"The answer is {evaluate_math(expr)}."

    else:
        response = "I can tell jokes, solve math, fetch weather, translate, and search Wikipedia."

    type_text(response)
