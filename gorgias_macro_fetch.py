
import os
import requests
import json
from dotenv import load_dotenv

def fetch_gorgias_macros():
    """
    Fetches macros from the Gorgias API for a predefined list of search queries,
    extracts relevant information, and saves it to a markdown file.
    """
    load_dotenv()
    auth_string = os.getenv("GORGIAS_AUTH_STRING")
    if not auth_string:
        print("Error: GORGIAS_AUTH_STRING not found in .env file.")
        return

    headers = {
        'accept': 'application/json',
        'authorization': f'Basic {auth_string}'
    }

    search_queries = [
        "general", "shopping questions", "question about a watch",
        "straps, bracelets, bezels", "shipping", "payment",
        "gift options", "returns", "service and repairs"
    ]

    unique_macros = {}

    for query in search_queries:
        url = f'https://formexwatch.gorgias.com/api/macros?limit=30&message_id=null&order_by=usage&search={query}&ticket_id=null&number_predictions=0&archived=false'
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            macros = response.json().get('data', [])

            for macro in macros:
                if macro['id'] not in unique_macros:
                    actions = macro.get('actions', [])
                    if actions:
                        arguments = actions[0].get('arguments', {})
                        body_text = arguments.get('body_text', 'N/A')
                        title = actions[0].get('title', 'N/A')
                    else:
                        body_text = 'N/A'
                        title = 'N/A'

                    unique_macros[macro['id']] = {
                        'name': macro.get('name', 'N/A'),
                        'body_text': body_text,
                        'title': title
                    }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching macros for query '{query}': {e}")
            continue

    output_file = os.path.join('data', 'knowledge', 'macros.md')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for macro_id, macro_data in unique_macros.items():
            f.write(f"## {macro_data['name']}\n\n")
            f.write(f"**Title:** {macro_data['title']}\n\n")
            f.write(f"**Body:**\n{macro_data['body_text']}\n\n")
            f.write("---\n\n")

    print(f"Successfully fetched and wrote {len(unique_macros)} unique macros to {output_file}")

if __name__ == "__main__":
    fetch_gorgias_macros()
