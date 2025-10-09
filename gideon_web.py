import streamlit as st
import time
import wikipedia
import requests
import random
import re
from googletrans import Translator

# === CONFIG ===
SECRET_CODE = "1234"
WEATHER_API_KEY = "676ebc8868d046dc914131347253009"
translator = Translator()

# === Typing Effect ===
def type_text(text, delay=0.02):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(f"**Gideon:** {typed}█")
        time.sleep(delay)
    placeholder.markdown(f"**Gideon:** {typed}")

# === Lock System ===
def keyword_unlock():
    st.title("🔒 Keyword Access")
    max_wrong = 3
    if "wrong" not in st.session_state:
        st.session_state.wrong = 0

    if st.session_state.wrong >= max_wrong:
        st.error("Too many wrong attempts — system locked.")
        return False

    keyword = st.text_input("Enter keyword:").strip().lower()

    if st.button("Unlock"):
        if keyword == "pineapple":
            st.session_state.user = "Achilleas"
            st.success("Access granted. Welcome Achilleas!")
            time.sleep(1)
            st.rerun()
        elif keyword == "apple":
            st.session_state.user = "George"
            st.success("Access granted. Welcome George!")
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.wrong += 1
            remaining = max_wrong - st.session_state.wrong
            if remaining > 0:
                st.warning(f"Wrong keyword. {remaining} attempt(s) left.")
            else:
                st.error("Too many wrong attempts — system locked.")
    return "user" in st.session_state

# === Greeting ===
def greeting_system():
    user = st.session_state.user
    st.title(f"Hello {user}, welcome to Gideon Web Interface!")
    type_text(f"Hello {user}, I'm your virtual AI, Gideon!")
    st.info("Ask me anything — math, Wikipedia, weather, jokes, or translations.")

# === Math Expression Detection ===
def extract_math_expression(s):
    """Extracts math expression from natural language (e.g., 'What is 2+2')."""
    match = re.search(r"([\d\.\+\-\*/\(\) ]+)", s)
    if match:
        return match.group(1)
    return None

# === Wikipedia ===
def handle_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        type_text(summary)
    except Exception:
        type_text("Sorry, I couldn’t find anything on Wikipedia for that topic.")

# === Weather ===
def handle_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
        data = requests.get(url).json()
        if "error" in data:
            type_text("City not found. Please try another one.")
        else:
            condition = data["current"]["condition"]["text"]
            temp = data["current"]["temp_c"]
            feels = data["current"]["feelslike_c"]
            type_text(f"The weather in {city} is {condition}, {temp}°C (feels like {feels}°C).")
    except Exception:
        type_text("Sorry, there was an error fetching the weather.")

# === Jokes ===
def handle_joke():
    jokes = [
        "Why don’t scientists trust atoms? Because they make up everything!",
        "Why was the math book sad? It had too many problems.",
        "What did the ocean say to the shore? Nothing, it just waved!",
    ]
    type_text(random.choice(jokes))

# === Translation ===
def handle_translation(text, target_lang):
    lang_map = {
        "english": "en", "greek": "el", "spanish": "es",
        "french": "fr", "german": "de", "italian": "it",
        "japanese": "ja", "chinese": "zh-cn"
    }
    lang_code = lang_map.get(target_lang.lower(), target_lang)
    try:
        result = translator.translate(text, dest=lang_code)
        type_text(f"Translation in {target_lang.capitalize()}: {result.text}")
    except Exception:
        type_text("Sorry, I couldn’t translate that right now.")

# === SOS Lock ===
def handle_sos():
    st.warning("🚨 SOS mode activated! The AI is locked until you enter the correct code.")
    code = st.text_input("Enter unlock code:", type="password")
    if st.button("Unlock AI"):
        if code == SECRET_CODE:
            st.session_state.sos_active = False
            type_text("AI unlocked. You may continue.")
        else:
            type_text("Wrong code. System locked.")
            st.stop()

# === AI Loop ===
def ai_loop():
    if "sos_active" not in st.session_state:
        st.session_state.sos_active = False

    # If SOS active, only unlock screen
    if st.session_state.sos_active:
        handle_sos()
        return

    user_input = st.text_input("Ask me something (or type 'exit'):").strip()

    if st.button("Send"):
        if user_input.lower() == "exit":
            type_text("Goodbye! See you next time.")
            st.stop()

        elif user_input.lower() == "sos":
            st.session_state.sos_active = True
            st.rerun()

        elif user_input.lower().startswith("wiki "):
            topic = user_input[5:].strip()
            handle_wikipedia(topic)

        elif user_input.lower().startswith("weather "):
            city = user_input[8:].strip()
            handle_weather(city)

        elif user_input.lower() == "joke":
            handle_joke()

        elif user_input.lower().startswith("translate "):
            try:
                parts = user_input.split(" to ")
                text = parts[0].replace("translate ", "").strip()
                lang = parts[1].strip()
                handle_translation(text, lang)
            except Exception:
                type_text("Use format: translate [text] to [language]")

        else:
            # Try to detect math in natural language
            expr = extract_math_expression(user_input)
            if expr:
                try:
                    answer = eval(expr)
                    type_text(f"The answer is {answer}")
                except Exception:
                    type_text("Invalid math expression.")
            else:
                type_text("I can answer questions, tell jokes, fetch weather, search Wikipedia, or translate!")

# === Run App ===
if "user" not in st.session_state:
    keyword_unlock()
else:
    # Prevent greeting from repeating on every refresh
    if "greeted" not in st.session_state:
        greeting_system()
        st.session_state.greeted = True
    ai_loop()
