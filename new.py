import requests

# NOTE: use the PRODUCTION webhook path (no "-test"), and make sure the
# workflow is toggled "Active" / Published in n8n. The "-test" webhook only
# fires once per click of "Execute workflow" in the editor, so any command
# sent after the first one (e.g. a separate "search" or "close" command)
# will just hang until timeout since n8n isn't listening anymore.
WEBHOOK_URL = "http://localhost:5678/webhook/friday"

# Fixed session id so n8n's Memory node treats every command from this
# client as one continuous conversation, letting "search for X" and
# "play it" (sent as separate commands) resolve using earlier context.
SESSION_ID = "friday-main-session"

def send_to_n8n(user_text):
    payload = {
        "text": user_text,
        "session_id": SESSION_ID
    }

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=60
        )

        print("Status:", response.status_code)
        #print("Raw response:", response.text)

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            print("n8n did not return JSON")
            return None

       # print("n8n data:", data)

        if "reply" in data:
            print("Assistant:", data["reply"])

        return data

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


if __name__ == "__main__":
    while True:
        command = input("You: ").strip()

        if command.lower() in ["exit", "quit", "stop"]:
            break

        send_to_n8n(command)