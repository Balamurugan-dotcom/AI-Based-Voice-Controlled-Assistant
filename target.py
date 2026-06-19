import pyttsx3

# -------------------------------
# 🔊 INIT ENGINE
# -------------------------------
engine = pyttsx3.init()

# -------------------------------
# 🎙️ SELECT BEST VOICE
# -------------------------------
voices = engine.getProperty('voices')

for v in voices:
    if "zira" in v.name.lower():   # better natural voice
        engine.setProperty('voice', v.id)
        break

# -------------------------------
# ⚙️ SETTINGS
# -------------------------------
engine.setProperty('rate', 160)   # slower = more natural
engine.setProperty('volume', 1.0)


# -------------------------------
# 🗣️ SPEAK FUNCTION
# -------------------------------
def speak(text):
    try:
        print(f"🗣️ Agent: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(" TTS error:", e)


# -------------------------------
# 💬 SIMPLE REPLIES
# -------------------------------
def reply(goal):
    goal = goal.lower()

    if "thank" in goal:
        speak("You're welcome")

    elif "hello" in goal or "hi" in goal:
        speak("Hi, how can I help you?")

    elif "bye" in goal:
        speak("Goodbye")

    else:
        speak("Okay")