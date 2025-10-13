# gideon_web.py
import streamlit as st
import time
import wikipedia
import requests
import random
import re
import json
import os
from deep_translator import GoogleTranslator

# ================= CONFIG =================
SECRET_KEY = "pineappleapplelock"     # ← secret keyword (do NOT display it)
SECRET_CODE = "1234"                  # SOS code
WEATHER_API_KEY = "676ebc8868d046dc914131347253009"
LOCK_FILE = "lock_state.json"

# ================= UTIL: persistent lock =================
def load_lock_state():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"locked": False}
    return {"locked": False}

def save_lock_state(state: dict):
    try:
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass  # ignore write errors on platforms without persistent FS

# ================= UTIL: typing effect (only for newest) =================
def type_text_once(text: str, delay: float = 0.01):
    """Type a single response into a placeholder, updating it in-place."""
    placeholder = st.empty()
    typed = ""
    for ch in text:
        typed += ch
        placeholder.markdown(f"**Gideon:** {typed}▌")
        time.sleep(delay)
    placeholder.markdown(f"**Gideon:** {typed}")

# ================= HELPERS: features =================
def is_math_expression(s: str) -> bool:
    s = s.strip()
    # contains digits and math operators
    return bool(re.search(r"[0-9]", s)) and bool(re.search(r"[\+\-\*/\^×]", s))

def extract_math(expr: str) -> str:
    # normalize words to symbols
    expr = expr.lower()
    expr = expr.replace("×", "*").replace("^", "**")
    expr = re.sub(r"\btimes\b", "*", expr)
    expr = re.sub(r"\bmultiplied by\b", "*", expr)
    expr = re.sub(r"\bdivided by\b", "/", expr)
    expr = re.sub(r"\bplus\b", "+", expr)
    expr = re.sub(r"\bminus\b", "-", expr)
    # extract the first run of digits/operators
    m = re.search(r"([0-9\.\s\+\-\*\/\(\)\^]+)", expr)
    if m:
        return m.group(1).strip()
    return ""

def safe_eval(expr: str):
    # very small safety: only allow digits, operators, parentheses, dot, spaces
    if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s\^]+", expr):
        raise ValueError("Unsafe expression")
    # replace ^ with ** for power
    expr = expr.replace("^", "**")
    return eval(expr)

def get_weather(city: str) -> str:
    try:
        q = city.strip() or "Athens"
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={q}&aqi=no"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "error" in data:
            return f"Weather error: {data['error'].get('message','unknown')}"
        loc = data["location"]["name"]
        country = data["location"]["country"]
        temp = data["current"]["temp_c"]
        cond = data["current"]["condition"]["text"]
        return f"Weather in {loc}, {country}: {cond}, {temp}°C."
    except Exception as e:
        return f"Could not fetch weather: {e}"

def get_wiki_summary(topic: str) -> str:
    try:
        return wikipedia.summary(topic, sentences=2, auto_suggest=True, redirect=True)
    except wikipedia.DisambiguationError as e:
        opts = ", ".join(e.options[:5])
        return f"Multiple matches. Did you mean: {opts}?"
    except wikipedia.PageError:
        return "No Wikipedia page found for that topic."
    except Exception as e:
        return f"Wikipedia error: {e}"

def tell_joke() -> str:
    jokes = [
        "Why don’t scientists trust atoms? Because they make up everything!",
        "Why did the math book look sad? It had too many problems.",
        "Why did the computer sneeze? It had a bad case of the 'flu' (function)!"
    ]
    return random.choice(jokes)

LANG_MAP = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "greek": "el", "japanese": "ja", "chinese": "zh-CN",
    "russian": "ru", "portuguese": "pt", "arabic": "ar", "hindi": "hi"
}

def translate_text(text: str, lang_name: str) -> str:
    code = LANG_MAP.get(lang_name.lower(), lang_name.lower())
    try:
        translated = GoogleTranslator(source='auto', target=code).translate(text)
        return translated
    except Exception as e:
        return f"Translation error: {e}"

# ================= STREAMLIT APP UI =================
st.set_page_config(page_title="🤖 Gideon AI", layout="centered")

# Load persistent lock (SOS lock)
lock_state = load_lock_state()
if "sos_locked" not in st.session_state:
    st.session_state.sos_locked = lock_state.get("locked", False)

# Chat history stored in session (messages are tuples: (speaker, text))
if "chat" not in st.session_state:
    st.session_state.chat = []

# Greeting flag so greeting types only once
if "greeted" not in st.session_state:
    st.session_state.greeted = False

st.title("🤖 Gideon AI Assistant")

# If persistent SOS lock active, require SOS code
if st.session_state.sos_locked:
    st.warning("🚨 System is SOS-locked. Enter the unlock code to continue.")
    sos_input = st.text_input("Enter SOS code:", type="password")
    if st.button("Unlock SOS"):
        if sos_input == SECRET_CODE:
            st.session_state.sos_locked = False
            save_lock_state({"locked": False})
            st.success("System unlocked. Refreshing...")
            st.experimental_rerun()
        else:
            st.error("Wrong code. System remains locked.")
    st.stop()

# If user not yet unlocked via keyword, show keyword input
if "user" not in st.session_state:
    st.subheader("🔐 Keyword Access")
    st.write("Enter the secret keyword to unlock the assistant.")
    kw = st.text_input("Keyword:", type="password")
    if st.button("Unlock"):
        if kw and kw == SECRET_KEY:
            st.session_state.user = "Achilleas"
            st.success("Access granted.")
            st.experimental_rerun()
        elif kw and kw.lower() == "apple":   # keep second user if desired
            st.session_state.user = "George"
            st.success("Access granted (George).")
            st.experimental_rerun()
        else:
            # wrong -> set persistent lock
            st.error("Wrong keyword. System is now locked due to failed attempts.")
            st.session_state.sos_locked = True
            save_lock_state({"locked": True})
            st.stop()
    st.stop()

# At this point user is unlocked
user = st.session_state.user
st.markdown(f"**Hello {user}!**")

# Show chat history (old messages printed normally)
for speaker, text in st.session_state.chat:
    if speaker == "user":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Gideon:** {text}")

# Input row
col1, col2 = st.columns([4,1])
with col1:
    user_prompt = st.text_input("Ask Gideon (math, weather, wiki, joke, translate, sos):", key="input_box")
with col2:
    send = st.button("Send")

# On send: process once, append history, and show typed reply only for latest message
if send and user_prompt:
    u = user_prompt.strip()
    st.session_state.chat.append(("user", u))

    # handle SOS
    if u.lower() == "sos":
        # activate persistent lock and end
        save_lock_state({"locked": True})
        st.session_state.sos_locked = True
        st.session_state.chat.append(("gideon", "SOS activated. System locked."))
        st.experimental_rerun()

    # weather
    elif u.lower().startswith("weather") or "weather in" in u.lower():
        city = re.sub(r'(?i)weather( in)?', '', u).strip()
        resp = get_weather(city)
        st.session_state.chat.append(("gideon", resp))

    # wiki
    elif u.lower().startswith("wiki ") or u.lower().startswith("search ") or u.lower().startswith("who is") or u.lower().startswith("what is"):
        # extract topic
        topic = re.sub(r'(?i)^(wiki|search|who is|what is)\s*', '', u).strip()
        if topic == "":
            resp = "Please tell me what to search on Wikipedia."
        else:
            resp = get_wiki_summary(topic)
        st.session_state.chat.append(("gideon", resp))

    # joke
    elif "joke" in u.lower():
        st.session_state.chat.append(("gideon", tell_joke()))

    # translate
    elif u.lower().startswith("translate "):
        parts = re.split(r"\bto\b", u, flags=re.IGNORECASE)
        if len(parts) == 2:
            text = parts[0].replace("translate", "", flags=re.IGNORECASE).strip()
            lang = parts[1].strip()
            code_guess = LANG_MAP.get(lang.lower(), lang.lower())
            resp = translate_text(text, code_guess)
        else:
            resp = "Use: translate <text> to <language>"
        st.session_state.chat.append(("gideon", resp))

    # math (natural language)
    else:
        expr = extract_math(u)
        if expr:
            # cleanup expr
            expr = expr.replace(" ", "")
            try:
                ans = safe_ans = safe_eval(expr)
                resp = f"The answer is {ans}"
            except Exception:
                # fallback try: replace words then eval
                expr2 = extract_math(u)
                try:
                    ans = eval(expr2.replace("^", "**"))
                    resp = f"The answer is {ans}"
                except Exception:
                    resp = "I couldn't evaluate that math expression."
        else:
            resp = "I can help with math, weather, Wikipedia, jokes, or translations."

        st.session_state.chat.append(("gideon", resp))

    # show only the newest gideon reply with typing animation
    latest = st.session_state.chat[-1][1]
    # render all history again but keep latest to animate
    st.experimental_rerun()

# If not pressing send, show the newest gideon line normally (no re-animation)
# (We re-render the whole page on each run; to avoid re-animation the chat displays
# earlier messages normally and only animates when we just appended and rerun.)
if "chat" in st.session_state and st.session_state.chat:
    # Ensure last message is displayed (if page reloaded after action)
    last_speaker, last_text = st.session_state.chat[-1]
    # If last message is Gideon and we just added it this run, animate it once
    # We detect "just added" by using a small session flag
    if "just_animated" not in st.session_state:
        # animate the newest Gideon reply if it is from Gideon
        if last_speaker == "gideon":
            type_text_once(last_text, delay=0.01)
        st.session_state.just_animated = True
    else:
        # subsequent runs: render the last message normally
        if last_speaker == "gideon":
            st.markdown(f"**Gideon:** {last_text}")
