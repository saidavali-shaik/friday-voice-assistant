# Friday AI Voice Assistant

A Windows desktop AI voice assistant inspired by a futuristic JARVIS/FRIDAY-style interface.

Friday combines **Python**, **SpeechRecognition**, **n8n**, **Groq**, **Edge TTS**, **PyGame**, **Flask**, **PyQt5**, and an animated **HTML/CSS/JavaScript orb**.

The Python application listens to the microphone, sends the user's request to an n8n webhook, receives a structured response, performs the required automation through the local Flask server, and speaks the response using Microsoft Edge TTS.

---

## ✨ Features

- 🎙️ Voice input through the computer microphone
- 🧠 AI request processing through n8n
- 🔗 Local communication with n8n through an HTTP webhook
- 🔊 Text-to-speech using Microsoft Edge TTS
- 🌍 Multilingual support:
  - English
  - Telugu
  - Hindi
  - Tamil
  - Kannada
  - Malayalam
  - Romanized versions of supported languages
- 🔮 Futuristic animated Friday orb
- 🖥️ Frameless desktop orb window using PyQt5
- 🟢 Orb states:
  - Idle
  - Listening
  - Responding
- 💤 Wake-word activation using `Friday`
- ⏸️ Sleep mode
- 🛑 Shutdown commands
- ⚙️ n8n-based AI and automation workflow
- 🌦️ Weather integration
- 📰 News integration
- 🌐 Google/website search automation
- ▶️ YouTube search and playback controls
- 💬 WhatsApp automation
- 📷 Instagram automation
- 🎵 Spotify/app opening support
- 💻 VS Code, Terminal and File Explorer automation
- 📄 File opening support
- 🔄 Persistent Chrome tabs for Chrome-based services

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      Microphone      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Python Friday     │
                         │ SpeechRecognition   │
                         └──────────┬───────────┘
                                    │
                           HTTP POST / Webhook
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        n8n           │
                         │ AI + Routing + APIs  │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
                 Groq/API       Weather/News    Automation JSON
                                                    │
                                                    ▼
                                      ┌────────────────────────┐
                                      │     Flask server.py    │
                                      │ Windows automation     │
                                      └────────────┬───────────┘
                                                   │
                    ┌──────────────┬──────────────┼──────────────┐
                    ▼              ▼              ▼              ▼
                 Chrome         WhatsApp       VS Code      File Explorer
                    │
                    ▼
             YouTube / Google /
             Instagram / Spotify

                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Python Friday     │
                         │ reply + language     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Edge TTS        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                              🔊 Speaker

                 ┌─────────────────────────────────────┐
                 │          Friday Orb UI              │
                 │ HTML/CSS/JS + PyQt5 + Flask state  │
                 └─────────────────────────────────────┘
```

---

# 📁 Project Structure

A recommended GitHub repository structure is:

```text
Friday-AI-Assistant/
│
├── friday.py
├── server.py
├── OrbWindow.py
├── orb.html
│
├── n8n/
│   └── friday-workflow.json
│
├── README.md
├── requirements.txt
├── .gitignore
│
└── voice.mp3              # generated at runtime; do not commit
```

Your actual filenames can be different. The important parts are:

| File | Purpose |
|---|---|
| `friday.py` | Main voice assistant |
| `server.py` | Local Windows automation + orb state server |
| `OrbWindow.py` | Opens the orb as a desktop window |
| `orb.html` | Animated Friday HUD/orb |
| `friday-workflow.json` | Exported n8n workflow |
| `README.md` | Project documentation |

---

# 🧰 Technologies

| Technology | Purpose |
|---|---|
| Python | Main assistant |
| SpeechRecognition | Microphone speech recognition |
| Google Speech Recognition | Speech-to-text backend used by the Python code |
| Edge TTS | Text-to-speech |
| PyGame | Plays generated speech |
| PyQt5 | Desktop orb window |
| Qt WebEngine | Displays `orb.html` inside the desktop window |
| HTML/CSS/JavaScript | Animated orb/HUD |
| Flask | Local API and automation server |
| Flask-CORS | Local cross-origin communication |
| Requests | HTTP communication |
| WebSocket Client | Chrome DevTools Protocol communication |
| PyWinAuto | Windows UI automation |
| n8n | AI workflow and automation orchestration |
| Groq | LLM/API processing in the n8n workflow |
| OpenWeatherMap | Weather data |
| NewsAPI | News data |
| Google Chrome | Browser automation for web services |

---

# 💻 Requirements

## Operating system

Recommended:

- Windows 10 or Windows 11
- Working microphone
- Speakers/headphones
- Internet connection
- Google Chrome
- Python 3.10 or newer
- Docker Desktop if n8n is running in Docker

The project is designed around Windows-specific automation, so Windows is required for the full feature set.

---

# 🐍 1. Create a Python Virtual Environment

Open PowerShell in the project folder.

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can temporarily allow local scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

---

# 📦 2. Install Python Dependencies

Install the main dependencies:

```powershell
pip install requests SpeechRecognition edge-tts pygame PyQt5 PyQtWebEngine
```

Install the local automation server dependencies:

```powershell
pip install flask flask-cors websocket-client pywinauto
```

If your Python environment needs PyAudio for `SpeechRecognition`, install a PyAudio package compatible with your Python and Windows setup.

You can verify the packages with:

```powershell
pip list
```

---

# 🔧 3. Prepare Google Chrome

The automation server uses Chrome DevTools Protocol for browser-based automation.

The current configuration expects Chrome at:

```text
C:\Program Files\Google\Chrome\Application\chrome.exe
```

If Chrome is installed somewhere else, change `CHROME_PATH` in `server.py`.

The server uses a separate Chrome profile:

```text
%USERPROFILE%\FridayChromeProfile
```

This profile is created/used by the automation server so that the project does not need your normal Chrome profile.

---

# 🤖 4. Install and Start n8n

This project uses n8n as the AI and automation orchestration layer.

If n8n is running through Docker, start your existing container:

```powershell
docker start n8n
```

Check running containers:

```powershell
docker ps
```

n8n should normally be available at:

```text
http://localhost:5678
```

Open that address in your browser.

---

# 📥 5. Import the n8n Workflow

The repository should contain the GitHub-safe n8n workflow JSON.

For example:

```text
n8n/friday-workflow.json
```

In n8n:

1. Open n8n.
2. Open your workspace.
3. Import the workflow JSON.
4. Check the imported nodes.
5. Reconnect/select your own credentials where required.
6. Save the workflow.
7. Activate the workflow when you are ready.

The workflow contains a webhook with the path:

```text
friday
```

The Python application therefore sends requests to:

```text
http://localhost:5678/webhook/friday
```

---

# 🔐 6. Configure n8n Credentials

Do **not** put real API keys directly into the GitHub repository.

The project uses external services such as:

- Groq
- OpenWeatherMap
- NewsAPI

Configure these through n8n credentials or another secure secret-management method.

The public/GitHub-safe workflow should contain placeholders instead of real secrets, for example:

```text
YOUR_OPENWEATHERMAP_API_KEY
YOUR_NEWSAPI_KEY
```

If the imported workflow contains credential references, n8n may reconnect them automatically when the matching credentials already exist in the same n8n instance. Otherwise, select/create your own credentials.

### Important

Credential IDs and credential names are not the same thing as the actual API secret.

Never publish:

```text
API keys
Bearer tokens
Passwords
Private tokens
Secret credentials
```

---

# 🔗 7. n8n Webhook Configuration

The Python application expects:

```text
POST http://localhost:5678/webhook/friday
```

The request body is approximately:

```json
{
  "text": "what is the weather today",
  "session_id": "friday-main-session"
}
```

The n8n workflow processes the request and returns a response containing:

```json
{
  "reply": "Assistant response",
  "language": "English"
}
```

The Python application reads the `reply` and `language` fields.

---

# 🧠 8. What the n8n Workflow Does

The n8n workflow acts as the intelligence and routing layer.

The workflow can distinguish between normal conversation and automation requests.

Examples of supported automation categories include:

```text
open
close
open_file
play
youtube_search
whatsapp_search
spotify_search
google_search
instagram_search
terminal_search
filemanager_search
youtube_play
youtube_pause
youtube_stop
youtube_back
whatsapp_send
whatsapp_send_file
instagram_send
weather
location
datetime
news
chat
```

The workflow uses structured output so the automation layer can determine which action should be performed.

---

# 🗣️ 9. Language Support

The Python assistant supports these Edge TTS voices:

```text
English    → en-US-AriaNeural
Telugu     → te-IN-ShrutiNeural
Hindi      → hi-IN-SwaraNeural
Tamil      → ta-IN-PallaviNeural
Kannada    → kn-IN-SapnaNeural
Malayalam  → ml-IN-SobhanaNeural
```

The Python code detects the Unicode script in the assistant response.

For example:

```text
Telugu script     → Telugu voice
Devanagari        → Hindi voice
Tamil script      → Tamil voice
Kannada script    → Kannada voice
Malayalam script  → Malayalam voice
Latin/English     → English voice
```

Romanized input can be interpreted by the n8n AI layer according to the workflow prompt.

---

# 🔮 10. Friday Orb

The orb is built with:

- HTML
- CSS
- JavaScript
- Canvas
- Particle animation
- HUD elements
- Scanlines
- Waveform animation
- Status indicators

The orb supports three main states:

```text
idle
listening
responding
```

The HTML interface requests the current state from:

```text
http://localhost:5000/state
```

The Python application changes the state through:

```text
http://localhost:5000/set/<mode>
```

For example:

```text
POST /set/listening
POST /set/responding
POST /set/idle
```

---

# 🖥️ 11. OrbWindow.py

`OrbWindow.py` loads the HTML orb into a PyQt5 desktop window using `QWebEngineView`.

The desktop window:

- Uses a custom title bar
- Can be dragged
- Has minimize/close controls
- Can remain above other windows
- Loads the local `orb.html`
- Appears near the bottom-right of the screen
- Can be closed using the window controls/right-click behavior implemented by the project

The main Python assistant launches the orb window.

---

# 🖥️ 12. Start the Local Automation Server

Open a PowerShell terminal in the project directory.

Activate your environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Start:

```powershell
python server.py
```

The Flask server provides the local API on:

```text
http://localhost:5000
```

Important endpoints include:

```text
GET  /state
POST /set/<mode>
```

The same server also handles Windows/browser automation.

Keep this terminal running.

---

# 🎙️ 13. Start Friday

After the Flask server is running, open another PowerShell terminal.

Activate the same virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Start the assistant:

```powershell
python friday.py
```

Friday should start the orb and initialize the voice assistant.

---

# 🔄 14. Correct Startup Order

For the complete project, use this order:

### Step 1 — Start Docker/n8n

```powershell
docker start n8n
```

Confirm:

```text
http://localhost:5678
```

is accessible.

### Step 2 — Start the Flask server

```powershell
python server.py
```

Keep it running.

### Step 3 — Start Friday

Open another terminal:

```powershell
python friday.py
```

### Step 4 — Wake Friday

Say:

```text
Friday
```

Friday should respond:

```text
Yes boss.
```

Then give your command.

---

# 🎤 15. How the Voice Flow Works

The complete flow is:

```text
Microphone
    ↓
SpeechRecognition
    ↓
Speech-to-text
    ↓
Wake word / command detection
    ↓
POST request to n8n
    ↓
n8n AI Agent
    ↓
Structured action
    ↓
Automation/API node
    ↓
Response
    ↓
Python receives reply
    ↓
Language detection
    ↓
Edge TTS
    ↓
PyGame
    ↓
Speaker
```

At the same time:

```text
Python
   ↓
Flask /set/<mode>
   ↓
orb.html
   ↓
Visual state changes
```

---

# 💤 16. Sleep Mode

Friday can return to an inactive listening state using commands such as:

```text
goodbye
good bye
go to sleep
sleep
sleep Friday
```

After entering sleep mode, Friday waits for the wake word again.

Wake it by saying:

```text
Friday
```

---

# 🛑 17. Shutdown Friday

Shutdown commands include:

```text
shutdown Friday
shut down Friday
exit Friday
quit Friday
close Friday
```

These terminate the main Friday loop.

---

# 🧪 18. Test the System

Test each layer separately.

## Test 1 — n8n

Open:

```text
http://localhost:5678
```

Verify the workflow is imported and active.

Test the webhook from inside n8n or with a suitable HTTP client.

---

## Test 2 — Flask Server

With `server.py` running, open:

```text
http://localhost:5000/state
```

You should receive JSON similar to:

```json
{
  "mode": "idle"
}
```

You can test the state endpoint with PowerShell:

```powershell
Invoke-WebRequest -Uri "http://localhost:5000/state"
```

---

## Test 3 — Python Assistant

Start:

```powershell
python friday.py
```

Check that:

- The orb opens.
- The microphone is detected.
- Friday can hear the wake word.
- Friday sends requests to n8n.
- A response is returned.
- Edge TTS speaks the response.

---

# 🗣️ 19. Example Commands

## General conversation

```text
Friday
```

Then:

```text
Who are you?
```

---

## Weather

```text
What's the weather in Hyderabad?
```

or:

```text
Hyderabad weather
```

---

## Open an application

```text
Open Chrome
```

```text
Open VS Code
```

```text
Open Spotify
```

```text
Open WhatsApp
```

---

## YouTube

```text
Open YouTube
```

```text
Search YouTube for Python tutorials
```

```text
Play it
```

```text
Pause YouTube
```

```text
Stop YouTube
```

```text
Go back
```

---

## Google

```text
Search Google for Python decorators
```

---

## WhatsApp

Depending on the configured automation and WhatsApp state:

```text
Search WhatsApp for a contact
```

```text
Send a WhatsApp message
```

```text
Send a file on WhatsApp
```

---

## Instagram

```text
Search Instagram
```

```text
Send an Instagram message
```

---

## Files

```text
Open resume.pdf
```

The server resolves bare filenames inside its configured Documents directory.

---

# 🌐 20. Chrome-Based Automation

The server uses Chrome DevTools Protocol for several web-based integrations.

Chrome-backed services include:

- YouTube
- WhatsApp Web fallback
- Instagram
- Google

The server maintains separate browser sessions/tabs for these services so that multi-step requests can continue using the same browser context.

For example:

```text
Open YouTube
      ↓
Search for Python tutorials
      ↓
Play it
      ↓
Pause
```

---

# 💬 21. WhatsApp Desktop and Web Fallback

The automation server can use WhatsApp Desktop when it is installed.

If WhatsApp Desktop is unavailable, the project can use WhatsApp Web through Chrome for supported operations.

The WhatsApp automation therefore depends on the Windows installation/login state available on the computer.

---

# 📂 22. File Automation

The server has a configured base directory:

```python
FILES_BASE_DIR = os.path.join(
    os.path.expanduser("~"),
    "Documents"
)
```

This avoids hard-coding a specific Windows username.

For a command such as:

```text
Open resume.pdf
```

the server resolves the filename relative to the configured Documents directory.

Do not place sensitive files in the automation directory if you do not want the assistant to access them.

---

# 🔐 23. Security

This project is intended to be suitable for a public GitHub repository, but the local automation layer can control applications and browser sessions.

## Never commit

```text
API keys
Access tokens
Bearer tokens
Passwords
Private credentials
OAuth secrets
Personal authentication data
```

Before pushing the repository, search for:

```text
gsk_
apiKey
apikey
api_key
Authorization
Bearer
password
secret
token
```

Also search the entire n8n JSON for accidentally embedded values.

### If a secret was exposed

If a real API key was previously committed to GitHub or shared publicly:

1. Revoke/rotate the key.
2. Create a replacement key.
3. Store the replacement in n8n credentials or environment variables.
4. Remove the old secret from the repository history where appropriate.

---

# 🧹 24. GitHub-Safe n8n Workflow

The repository should contain a cleaned workflow export.

Do not publish the original workflow if it contains hard-coded API keys.

Use the GitHub-safe version with placeholders such as:

```text
YOUR_OPENWEATHERMAP_API_KEY
YOUR_NEWSAPI_KEY
```

When another person imports the workflow, they must configure their own credentials.

---

# 🚫 25. Files That Should Usually Be Ignored

Create a `.gitignore` similar to:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual environment
venv/
.venv/
env/

# Runtime audio
voice.mp3

# Local configuration
.env
*.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Local Chrome profile
FridayChromeProfile/
```

Do not add API keys to `.gitignore` and assume they are protected. The safer approach is to never place secrets in tracked source files in the first place.

---

# 📋 26. Recommended requirements.txt

You can create a `requirements.txt` containing:

```text
requests
SpeechRecognition
edge-tts
pygame
PyQt5
PyQtWebEngine
Flask
Flask-Cors
websocket-client
pywinauto
```

Install everything with:

```powershell
pip install -r requirements.txt
```

If PyAudio is required separately for your Windows/Python environment, install a compatible package for your setup.

---

# 🧩 27. Troubleshooting

## Problem: n8n is not reachable

Check:

```powershell
docker ps
```

Then open:

```text
http://localhost:5678
```

If the container is stopped:

```powershell
docker start n8n
```

---

## Problem: Friday says it cannot connect to n8n

Check the configuration in `friday.py`:

```python
WEBHOOK_URL = "http://localhost:5678/webhook/friday"
```

Then confirm the n8n workflow webhook path is:

```text
friday
```

Also confirm the workflow is running/active as required by your n8n configuration.

---

## Problem: Orb does not update

Make sure `server.py` is running.

Test:

```text
http://localhost:5000/state
```

The response should contain:

```json
{
  "mode": "idle"
}
```

---

## Problem: Orb window does not open

Check that these packages are installed:

```powershell
pip install PyQt5 PyQtWebEngine
```

Also confirm `orb.html` is in the location expected by `OrbWindow.py`.

---

## Problem: Microphone is not working

Check:

1. Windows microphone permissions.
2. The correct microphone is selected.
3. SpeechRecognition is installed.
4. PyAudio is available for your Python installation.
5. No other application is exclusively using the microphone.

---

## Problem: No voice response

Check Edge TTS:

```powershell
pip install --upgrade edge-tts
```

Then test your Internet connection.

Also make sure PyGame is installed:

```powershell
pip install pygame
```

---

## Problem: YouTube/Google/Instagram automation does not work

Check:

1. Google Chrome is installed.
2. `CHROME_PATH` points to the correct Chrome executable.
3. Port `9222` is available.
4. `server.py` is running.
5. The required website is logged in when necessary.
6. Chrome is allowed to open the automation profile.

---

## Problem: WhatsApp automation does not work

Check:

1. WhatsApp Desktop is installed if you want desktop automation.
2. You are logged into WhatsApp.
3. WhatsApp Web is logged in if the web fallback is used.
4. `server.py` is running.
5. Windows UI automation permissions are not blocking the application.

---

## Problem: A file cannot be opened

Check that the file exists inside:

```text
%USERPROFILE%\Documents
```

The current server uses the user's Documents directory rather than a hard-coded personal Windows username.

---

# 🔍 28. Debugging Checklist

When the complete system does not work, check each component in this order:

```text
1. Is Docker/n8n running?
        ↓
2. Is the n8n workflow imported?
        ↓
3. Are n8n credentials configured?
        ↓
4. Is server.py running?
        ↓
5. Does localhost:5000/state respond?
        ↓
6. Is Friday running?
        ↓
7. Is the microphone working?
        ↓
8. Does the wake word work?
        ↓
9. Does n8n receive the request?
        ↓
10. Does n8n return reply + language?
        ↓
11. Does Edge TTS generate audio?
        ↓
12. Does PyGame play the audio?
```

This makes it much easier to find which layer is failing.

---

# 🧪 29. Development Mode

For development, keep three terminals open.

### Terminal 1 — n8n

```powershell
docker start n8n
```

### Terminal 2 — Flask automation server

```powershell
.\venv\Scripts\Activate.ps1
python server.py
```

### Terminal 3 — Friday

```powershell
.\venv\Scripts\Activate.ps1
python friday.py
```

This setup makes it easier to see logs from each component independently.

---

# 🔄 30. Request/Response Example

### Python → n8n

```json
{
  "text": "open youtube",
  "session_id": "friday-main-session"
}
```

### n8n → Python

A normal response can look like:

```json
{
  "reply": "Opening YouTube.",
  "language": "English"
}
```

For an automation request, the internal n8n workflow can produce structured action data and route it to the corresponding automation node.

---

# 🧠 31. Why n8n Is Used

n8n separates AI decision-making from Windows automation.

The Python application does not need to contain every AI rule.

Instead:

```text
Python
    ↓
Voice input
    ↓
n8n
    ↓
AI understands request
    ↓
Structured action
    ↓
Automation
```

This makes it easier to add new integrations without rewriting the entire Python voice application.

---

# 🛠️ 32. Customization

## Change the wake word

The current Python logic uses:

```text
Friday
```

as the wake word.

The wake-word detection logic can be modified in `friday.py`.

---

## Change TTS voice

The voice mapping is defined in the Python application.

For example:

```python
VOICES = {
    "en": "en-US-AriaNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural"
}
```

---

## Change TTS speed/pitch

The current configuration uses:

```text
Rate: +10%
Pitch: +2Hz
```

These values can be changed in the Edge TTS configuration.

---

## Change the orb design

Edit:

```text
orb.html
```

You can customize:

- Orb size
- HUD layout
- Text
- Animation
- Particle count
- Scanlines
- Waveform
- Status indicators
- Visual effects

---

# 🚀 33. Adding New Commands

A new command normally requires changes in two places:

### 1. n8n

Add the action/schema/routing required to understand the new command.

### 2. server.py

Add the Windows/browser automation required to execute that action.

The general flow remains:

```text
Voice command
     ↓
n8n identifies action
     ↓
Structured JSON
     ↓
Automation route
     ↓
server.py
     ↓
Windows/browser action
```

---

# 📌 34. Important Local Ports

| Service | Port | Purpose |
|---|---:|---|
| n8n | `5678` | AI workflow/webhook |
| Flask server | `5000` | Orb state + local automation |
| Chrome CDP | `9222` | Browser automation |

The project expects these local services to be available.

---

# 🧭 35. Quick Start

After the project is installed, the normal daily startup is:

### 1. Start n8n

```powershell
docker start n8n
```

### 2. Start server.py

```powershell
python server.py
```

### 3. Start Friday

```powershell
python friday.py
```

### 4. Wake Friday

```text
Friday
```

### 5. Give a command

```text
Open YouTube
```

or:

```text
What's the weather in Hyderabad?
```

### 6. Put Friday to sleep

```text
Goodbye
```

### 7. Shut down Friday

```text
Shutdown Friday
```

---

# 📸 Suggested GitHub Screenshots

For a portfolio repository, useful screenshots include:

1. Friday orb running on the Windows desktop.
2. n8n workflow overview.
3. n8n AI Agent configuration.
4. Terminal showing `server.py`.
5. Terminal showing `friday.py`.
6. Example voice command and response.
7. YouTube/Google automation demonstration.
8. Project folder structure.

Do not include screenshots containing API keys, tokens, passwords, personal phone numbers, or other private information.

---

# 🎯 Future Improvements

Possible future improvements include:

- True offline wake-word detection
- Offline speech recognition
- Better conversation memory
- Persistent user preferences
- More Windows application integrations
- More browser integrations
- Calendar integration
- Email integration
- Smart-home control
- Better error recovery
- Configurable wake word
- GUI settings panel
- Startup with Windows
- Background service mode
- Better permission/security controls
- More natural interruption handling
- Streaming speech responses

---

# ⚠️ Limitations

This project depends on several external components.

For example:

- Speech recognition requires the configured speech recognition service/network.
- Edge TTS requires network access.
- n8n must be available.
- External APIs may have usage limits.
- Browser automation depends on Chrome and website UI behavior.
- WhatsApp/Instagram automation depends on login state and UI behavior.
- Windows UI automation can behave differently depending on installed applications and permissions.

Because browser and desktop automation interacts with applications outside this repository, an integration can stop working if the external application's UI or behavior changes.

---

# 🤝 Contributing

Contributions are welcome.

A typical contribution workflow is:

```text
Fork repository
      ↓
Create feature branch
      ↓
Make changes
      ↓
Test locally
      ↓
Commit changes
      ↓
Push branch
      ↓
Create Pull Request
```

Before submitting changes:

- Do not include API keys.
- Do not include personal credentials.
- Test the affected automation.
- Update documentation when behavior changes.

---

# 📄 License

Add your preferred open-source license here.

For example:

```text
MIT License
```

If you choose a license, add the corresponding `LICENSE` file to the repository.

---

# 👨‍💻 Project Summary

Friday is a modular Windows AI voice assistant.

The main responsibilities are separated like this:

```text
friday.py
    → microphone
    → wake word
    → n8n communication
    → response speech
    → orb state

n8n
    → AI understanding
    → structured actions
    → API integrations
    → routing

server.py
    → Windows automation
    → browser automation
    → file/application actions
    → orb state API

OrbWindow.py
    → desktop window

orb.html
    → futuristic visual interface
```

The result is a local AI assistant that combines voice interaction, AI reasoning, automation, and a visual desktop interface.

---

# ⭐ Final Setup Checklist

Before running the complete project, verify:

- [ ] Windows 10/11
- [ ] Python installed
- [ ] Virtual environment created
- [ ] Python dependencies installed
- [ ] Google Chrome installed
- [ ] Microphone working
- [ ] Docker Desktop installed if using Docker n8n
- [ ] n8n running
- [ ] Friday n8n workflow imported
- [ ] Groq credential configured
- [ ] OpenWeatherMap credential configured
- [ ] NewsAPI credential configured
- [ ] `server.py` running
- [ ] `localhost:5000/state` responds
- [ ] `friday.py` starts successfully
- [ ] Orb window opens
- [ ] Wake word works
- [ ] n8n receives commands
- [ ] AI response is returned
- [ ] Edge TTS speaks the response
- [ ] No real secrets are committed to GitHub

---

## 🚀 Start Friday

Once everything is configured:

```powershell
docker start n8n
```

Then:

```powershell
python server.py
```

Then, in another terminal:

```powershell
python friday.py
```

Say:

```text
Friday
```

and start talking to your assistant.
