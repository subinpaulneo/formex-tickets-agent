import os
import requests
import csv
import time
import base64
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---
LOG_FILE = "resume_state.log"
CSV_FILE = "gorgias_tickets.csv"

# --- Authentication Setup ---
gorgias_auth_string = os.getenv("GORGIAS_AUTH_STRING")
gorgias_api_user = os.getenv("GORGIAS_API_USER")
gorgias_api_key = os.getenv("GORGIAS_API_KEY")

auth_header = ""
if gorgias_auth_string:
    auth_header = f"Basic {gorgias_auth_string}"
elif gorgias_api_user and gorgias_api_key:
    auth_string = f"{gorgias_api_user}:{gorgias_api_key}"
    auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
else:
    print("Error: Please provide authentication credentials in the .env file.")
    exit()

BASE_URL = "https://formexwatch.gorgias.com/api"
HEADERS = {
    "accept": "application/json",
    "authorization": auth_header
}

# --- Robust Request Function with Rate Limit Handling ---
def make_request(url, params):
    retries = 3
    while retries > 0:
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()

            # Proactive delay based on the X-Gorgias-Account-Api-Call-Limit header
            limit_header = response.headers.get("X-Gorgias-Account-Api-Call-Limit")
            if limit_header:
                try:
                    count_str, limit_str = limit_header.split('/')
                    count = int(count_str)
                    limit = int(limit_str)
                    # If we are within 5 requests of the limit, pause briefly
                    if count >= (limit - 5):
                        print(f"Approaching rate limit ({limit_header}). Proactively sleeping for 5 seconds.")
                        time.sleep(5)
                except (ValueError, IndexError):
                    # Ignore if the header format is unexpected
                    pass
            
            return response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                print(f"Rate limit exceeded. Waiting for {retry_after} seconds.")
                time.sleep(retry_after)
                continue
            else:
                print(f"HTTP Error: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}. Retrying in 10 seconds...")
            retries -= 1
            time.sleep(10)
            continue
            
    print(f"Failed to fetch data from {url} after multiple retries.")
    return None

# --- Data Streaming Generators with Resume Logic ---
def stream_all_tickets(start_cursor=None):
    url = f"{BASE_URL}/tickets"
    params = {"limit": 100, "order_by": "created_datetime:desc"}
    if start_cursor:
        params["cursor"] = start_cursor
    
    while url:
        response = make_request(url, params)
        if not response:
            break

        data = response.json()
        tickets = data.get("data", [])
        for ticket in tickets:
            yield ticket
        
        next_cursor = data.get("meta", {}).get("next_cursor")
        if next_cursor:
            params["cursor"] = next_cursor
            with open(LOG_FILE, 'w') as f:
                f.write(next_cursor)
            url = f"{BASE_URL}/tickets"
        else:
            url = None

def stream_messages_for_ticket(ticket_id):
    url = f"{BASE_URL}/messages"
    params = {"limit": 100, "order_by": "created_datetime:desc", "ticket_id": ticket_id}
    while url:
        response = make_request(url, params)
        if not response:
            break
        data = response.json()
        messages = data.get("data", [])
        for message in messages:
            yield message
        next_cursor = data.get("meta", {}).get("next_cursor")
        if next_cursor:
            params["cursor"] = next_cursor
            url = f"{BASE_URL}/messages"
        else:
            url = None

# --- Main Execution Logic ---
def main():
    resume_cursor = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            resume_cursor = f.read().strip()
        print(f"Found resume file. Resuming from cursor: {resume_cursor}")
        file_mode = 'a'
        write_header = False
    else:
        print("Starting a fresh sync.")
        file_mode = 'w'
        write_header = True

    with open(CSV_FILE, file_mode, newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "ticket_id", "channel", "subject", "body", "sender", "receiver", 
            "created_datetime", "sent_datetime", "status"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        
        ticket_count = 0
        for ticket in stream_all_tickets(start_cursor=resume_cursor):
            ticket_count += 1
            if ticket_count % 50 == 0:
                print(f"Processing ticket #{ticket_count} (ID: {ticket.get('id')})...")

            for message in stream_messages_for_ticket(ticket["id"]):
                body = message.get("body_text") or message.get("body_html") or message.get("stripped_text")
                writer.writerow({
                    "ticket_id": ticket.get("id"),
                    "channel": ticket.get("channel"),
                    "subject": ticket.get("subject"),
                    "body": body,
                    "sender": (message.get("sender") or {}).get("email"),
                    "receiver": (message.get("receiver") or {}).get("email"),
                    "created_datetime": ticket.get("created_datetime"),
                    "sent_datetime": message.get("sent_datetime"),
                    "status": ticket.get("status")
                })

    # Clean up log file on successful completion
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    print(f"\nSuccessfully processed tickets and wrote data to {CSV_FILE}")
    if resume_cursor:
        print(f"(Resumed from a previous session)")

if __name__ == "__main__":
    main()