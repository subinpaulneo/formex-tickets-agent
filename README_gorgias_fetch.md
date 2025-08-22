# Gorgias Ticket and Message Fetcher

This script fetches all tickets and their corresponding messages from the Gorgias API and saves them to a CSV file.

## Features

*   **Efficient Streaming**: Processes data row-by-row to handle large datasets with low memory usage.
*   **Robust Rate Limiting**: Automatically handles API rate limits by waiting and retrying.
*   **Resume Functionality**: If the script is interrupted, it can be restarted and will automatically resume where it left off.

## Setup

1.  **Prerequisites:**
    *   Python 3.6+

2.  **Create a Virtual Environment (Recommended)**

    It's a good practice to use a virtual environment to manage project-specific dependencies.

    ```bash
    # Create a virtual environment named 'venv'
    python3 -m venv venv

    # Activate the virtual environment
    # On macOS and Linux:
    source venv/bin/activate
    # On Windows:
    # .\venv\Scripts\activate
    ```

3.  **Installation:**
    
    With your virtual environment activated, install the required Python libraries:
    ```bash
    pip install requests python-dotenv
    ```

4.  **Configuration:**

    Create a `.env` file in the same directory as the script. This file will store your Gorgias API credentials. You have two options for authentication:

    **Option 1: Basic Auth String (Recommended)**

    Add your base64-encoded credentials to the `.env` file:

    ```
    GORGIAS_AUTH_STRING=your_base64_encoded_credentials
    ```

    **Option 2: Username and API Key**

    If you don't have a pre-encoded string, you can use your username and API key:

    ```
    GORGIAS_API_USER=your_username
    GORGIAS_API_KEY=your_api_key
    ```

    *Note: The script will prioritize `GORGIAS_AUTH_STRING` if it is present.*

## Usage

Once you have completed the setup, run the script from your terminal (make sure your virtual environment is activated):

```bash
python gorgias_fetch.py
```

The script will create `gorgias_tickets.csv` and begin fetching data. 

### Resuming Interrupted Downloads

If the script is stopped or interrupted, it will create a `resume_state.log` file. To resume the download, simply run the script again:

```bash
python gorgias_fetch.py
```

The script will detect the log file, skip the tickets that have already been fetched, and continue from where it left off, appending the new data to the existing `gorgias_tickets.csv` file.

### Starting a Fresh Download

To ignore the resume state and start a completely new download from the beginning, **delete the `resume_state.log` file** before running the script.

When you are finished, you can deactivate the virtual environment:

```bash
deactivate
```

## Output CSV Columns

*   `ticket_id`
*   `channel`
*   `subject`
*   `body` (will contain `body_text`, `body_html`, or `stripped_text`)
*   `sender`
*   `receiver`
*   `created_datetime`
*   `sent_datetime`
*   `status`
