# gideon_web.py
import streamlit as st
import time
import wikipedia
import requests
import random
import re
import json
import os
import ast
import operator as op
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
SECRET_KEY = "pineappleapplelock"   # secret keyword (kept in code, not shown)
SECOND_USER_KEY = "apple"           # optional second user keyword
SOS_CODE = "1234"                   # SOS unlock code
WEATHER_API_KEY = "676ebc8868d046dc914131347253009"
LOCK_FILE = "lock_state.json"
TYPE_DELAY = 0.01

# ---------------- SAFE MATH (AST) ----------------
# allowed operators map
_allowed_ops = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}

def safe_eval(expr: str):
    """
    Safely evaluate a math expression using AST. Supports + - * / ** % // unary -.
    """
    def _eval(node):
        if isinstance(node, ast.Constant):  # python3.8+: numbers are Constant
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed")
        if isinstance(node, ast.Num):  # legacy
            return node.n
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _allowed_ops:
                raise ValueError("Operator not allowed")
            return _allowed_ops[op_type](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _allowed_ops:
                raise ValueError("Operator not allowed")
            return _allowed_ops[op_type](_eval(node.operand))
        raise ValueError("Invalid syntax")
    # compile and evaluate
    node = ast.parse(expr, mode="eval").body
    return _eval(node)

# ---------------- UTIL: lock persistence ----------------
def save_lock_state(state: dict):
    try:
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass

def load_lock_state() -> dict:
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"sos_locked": False}
    return {"sos_locked": False}

# ---------------- UTIL: typing effect (only for newest) ----------------
def type_text_once(text: str, delay: float = TYPE_DELAY):
    placeholder = st.empty()
    current = ""
    for ch in text:
        current += ch
        placeholder.markdown(f"**Gideon:** {current}▌")
        time.sleep(delay)
    placeholder.markdown(f"**Gideon:** {current}")

# ---------------- FEATURES ----------------
LANG_MAP = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "greek": "el", "japanese": "ja", "chinese": "zh-CN",
    "russian": "ru", "portuguese": "pt", "arabic": "ar", "hindi": "hi"
}

def translate_text(text: str, lang_name: str) -> str:
    code = LANG_MAP.get(lang_name.lower(), lang_name.lower())
    try:
        return GoogleTranslator(source='auto', target=code).translate(text)
    except Exception as e:
        return f"Translation error: {e}"

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
        "What did the ocean say to the shore? Nothing, it just waved!"
    ]
    return random.choice(jokes)

# ---------------- MATH EXTRACTION ----------------
def extract_math_expression(s: str) -> str:
    """
    Try to extract a math expression from natural language.
    Returns a cleaned expression string (e.g. '2+2', '3*(4+1)') or empty string.
    """
    s = s.lower()
    # word -> operator substitutions
    s = s.replace("×", "*").replace("x", "*").replace("✕", "*")
    s = re.sub(r"\bmultiplied by\b", "*", s)
    s = re.sub(r"\btimes\b", "*", s)
    s = re.sub(r"\bdivided by\b", "/", s)
    s = re.sub(r"\bover\b", "/", s)
    s = re.sub(r"\bplus\b", "+", s)
    s = re.sub(r"\bminus\b", "-", s)
    s = re.sub(r"[^\d\.\+\-\*\/\(\)\s\^]", " ", s)  # remove other chars
    # find longest continuous chunk that looks like an expression
    m = re.search(r"([0-9\.\s\+\-\*\/\(\)\^]+)", s)
    if m:
        expr = m.group(1).strip()
        expr = expr.replace(" ", "")
        expr = expr.replace("^", "**")
        return expr
    return ""

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="🤖 Gideon AI", layout="centered")

# load persistent lock state
lock_state = load_lock_state()
if "sos_locked" not in st.session_state:
    st.session_state.sos_locked = lock_state.get("sos_locked", False)

# session chat history and flags
if "chat" not in st.session_state:
    st.session_state.chat = []    # list of (speaker, text)
if "greeted" not in st.session_state:
    st.session_state.greeted = False

st.title("🤖 Gideon AI Assistant")

# If SOS locked: show only SOS unlock UI
if st.session_state.sos_locked:
    st.warning("🚨 SYSTEM LOCKED (SOS). Enter SOS unlock code to continue.")
    sos_in = st.text_input("SOS code:", type="password", key="sos_input")
    if st.button("Unlock SOS"):
        if sos_in == SOS_CODE:
            st.session_state.sos_locked = False
            save_lock_state({"sos_locked": False})
            st.success("System unlocked. Please refresh.")
            st.rerun()
        else:
            st.error("Wrong SOS code. System remains locked.")
    st.stop()

# Keyword unlock flow
if "user" not in st.session_state:
    st.subheader("🔐 Keyword Access")
    kw = st.text_input("Enter keyword:", type="password", key="kw_input")
    if st.button("Unlock"):
        if kw and kw == SECRET_KEY:
            st.session_state.user = "Achilleas"
            st.success("Access granted.")
            st.rerun()
        elif kw and kw.lower() == SECOND_USER_KEY:
            st.session_state.user = "George"
            st.success("Access granted (George).")
            st.rerun()
        elif kw:
            # wrong attempt -> lock persistently
            st.error("Wrong keyword — system locked.")
            st.session_state.sos_locked = True
            save_lock_state({"sos_locked": True})
            st.stop()
    st.stop()

# main UI once unlocked
user = st.session_state.user
# greet once
if not st.session_state.greeted:
    st.session_state.greeted = True
    st.markdown(f"**Hello {user}!**")
    type_text_once(f"Hello {user}, I'm your virtual AI, Gideon!")

# display chat history (previous messages shown normally)
for speaker, text in st.session_state.chat:
    if speaker == "user":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Gideon:** {text}")

# input area
col1, col2 = st.columns([4,1])
with col1:
    user_prompt = st.text_input("Ask Gideon (math, weather, wiki, joke, translate, sos):", key="main_input")
with col2:
    send = st.button("Send")

# handle send
if send and user_prompt:
    u = user_prompt.strip()
    st.session_state.chat.append(("user", u))

    # SOS command
    if u.lower() == "sos":
        # activate persistent lock
        save_lock_state({"sos_locked": True})
        st.session_state.sos_locked = True
        st.session_state.chat.append(("gideon", "SOS activated. System locked."))
        # immediately rerun to show lock UI
        st.rerun()

    # weather
    elif re.search(r"\bweather\b", u, re.I):
        city = re.sub(r'(?i)\bweather( in)?\b', '', u).strip()
        resp = get_weather(city)
        st.session_state.chat.append(("gideon", resp))

    # wiki
    elif re.search(r"^(wiki|search|who is|what is)\b", u, re.I):
        topic = re.sub(r'(?i)^(wiki|search|who is|what is)\s*', '', u).strip()
        if not topic:
            resp = "Please tell me what to search."
        else:
            resp = get_wiki_summary(topic)
        st.session_state.chat.append(("gideon", resp))

    # translate
    elif re.search(r'(?i)^translate\b', u):
        parts = re.split(r'(?i)\bto\b', u, maxsplit=1)
        if len(parts) == 2:
            text = re.sub(r'(?i)^translate\b', '', parts[0]).strip()
            lang = parts[1].strip()
            code = LANG_MAP.get(lang.lower(), lang.lower())
            resp = translate_text(text, code)
        else:
            resp = "Use: translate <text> to <language>"
        st.session_state.chat.append(("gideon", resp))

    # joke
    elif re.search(r'\bjoke\b', u, re.I):
        st.session_state.chat.append(("gideon", tell_joke()))

    # math: try to extract expression
    else:
        expr = extract_math_expression(u)
        if expr:
            try:
                val = safe_eval(expr)
                resp = f"The answer is {val}"
            except Exception:
                resp = "I couldn't evaluate that math expression."
        else:
            resp = "I can help with math, weather, Wikipedia, jokes, or translation."
        st.session_state.chat.append(("gideon", resp))

    # after appending the newest gideon reply, animate only that reply once
    # set a flag so we animate once and then show normally
    st.experimental_rerun()

# If the page loads and the last message is Gideon's and we haven't animated it this session,
# animate the newest Gideon message once; otherwise show normally.
if st.session_state.chat:
    last_speaker, last_text = st.session_state.chat[-1]
    if last_speaker == "gideon":
        if not st.session_state.get("animated_last", False):
            type_text_once(last_text)
            st.session_state.animated_last = True
        else:
            # already animated previously; ensure last message shown normally (avoid duplicate)
            st.markdown(f"**Gideon:** {last_text}")
