import pandas as pd
import os
import csv

# --- Constants ---
DUMP_CSV_PATH = 'gorgias_tickets_dump.csv'
BATCH_CSV_PATH = 'gorgias_tickets.csv'
RESUME_LOG_PATH = 'last_processed_ticket_id.log'
BATCH_SIZE_TICKETS = 500  # Number of unique closed tickets to process per batch
CHUNK_SIZE_ROWS = 10000   # Number of rows to read from the dump CSV at a time

# --- Helper Functions ---
def read_resume_state():
    """Reads the last processed ticket ID from the log file."""
    if os.path.exists(RESUME_LOG_PATH):
        with open(RESUME_LOG_PATH, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None # Log file might be empty or corrupted
    return None

def write_resume_state(ticket_id):
    """Writes the last processed ticket ID to the log file."""
    with open(RESUME_LOG_PATH, 'w') as f:
        f.write(str(ticket_id))

def get_existing_ticket_ids(file_path):
    """Reads existing ticket IDs from a CSV file to avoid reprocessing."""
    existing_ids = set()
    if os.path.exists(file_path):
        try:
            # Read only the 'ticket_id' column to save memory
            df = pd.read_csv(file_path, usecols=['ticket_id'], dtype={'ticket_id': int})
            existing_ids.update(df['ticket_id'].unique())
        except Exception as e:
            print(f"Warning: Could not read existing ticket IDs from {file_path}: {e}")
    return existing_ids

# --- Main Processing Logic ---
def main():
    print(f"Starting batch fetch from {DUMP_CSV_PATH}...")

    if not os.path.exists(DUMP_CSV_PATH):
        print(f"Error: Dump file not found at {DUMP_CSV_PATH}")
        return

    last_processed_id = read_resume_state()
    print(f"Last processed ticket ID: {last_processed_id if last_processed_id is not None else 'None'}")

    # Get IDs of tickets already in the batch file to avoid duplicates across runs
    existing_batch_ticket_ids = get_existing_ticket_ids(BATCH_CSV_PATH)
    print(f"Existing tickets in {BATCH_CSV_PATH}: {len(existing_batch_ticket_ids)}")

    processed_tickets_count = 0
    tickets_for_batch = []
    current_ticket_ids_in_batch = set() # To track unique tickets in the current batch
    header_written = os.path.exists(BATCH_CSV_PATH) # Check if file exists to decide if header is needed

    try:
        # Use iterator=True with chunksize to read the large CSV efficiently
        csv_iterator = pd.read_csv(DUMP_CSV_PATH, chunksize=CHUNK_SIZE_ROWS, iterator=True, dtype={'ticket_id': int})
        
        # Skip chunks until we pass the last_processed_id
        skipped_to_resume = False
        if last_processed_id is not None:
            print(f"Skipping to ticket ID {last_processed_id}...")

        for i, chunk in enumerate(csv_iterator):
            # Filter for closed tickets
            closed_tickets_chunk = chunk[chunk['status'] == 'closed'].copy()
            if closed_tickets_chunk.empty:
                continue

            # Sort by ticket_id to ensure consistent processing order for resume
            closed_tickets_chunk = closed_tickets_chunk.sort_values(by='ticket_id')

            for ticket_id, group in closed_tickets_chunk.groupby('ticket_id'):
                if last_processed_id is not None and ticket_id <= last_processed_id and not skipped_to_resume:
                    continue # Skip already processed tickets
                else:
                    skipped_to_resume = True # We have passed the last processed ID

                if ticket_id in existing_batch_ticket_ids:
                    continue # Skip if already in the batch file from previous runs

                if ticket_id in current_ticket_ids_in_batch:
                    continue # Skip if already added in this batch run

                if processed_tickets_count >= BATCH_SIZE_TICKETS:
                    break # Batch limit reached

                # Add all messages for this unique ticket_id
                tickets_for_batch.append(group)
                current_ticket_ids_in_batch.add(ticket_id)
                processed_tickets_count += 1
                print(f"  - Added ticket {ticket_id}. Current batch size: {processed_tickets_count}")
            
            if processed_tickets_count >= BATCH_SIZE_TICKETS:
                break # Batch limit reached after processing a chunk

        if not tickets_for_batch:
            print("No new closed tickets found to add to the batch.")
            return

        # Concatenate all collected ticket groups into a single DataFrame
        final_batch_df = pd.concat(tickets_for_batch)

        # Append to the batch CSV file
        mode = 'a' if header_written else 'w'
        header = not header_written
        final_batch_df.to_csv(BATCH_CSV_PATH, mode=mode, header=header, index=False, quoting=csv.QUOTE_ALL)
        print(f"Successfully wrote {processed_tickets_count} new closed tickets to {BATCH_CSV_PATH}")

        # Update resume state with the last ticket ID written to the batch file
        # This assumes ticket_id is monotonically increasing or we take the max of the current batch
        if not final_batch_df.empty:
            max_ticket_id_in_batch = final_batch_df['ticket_id'].max()
            write_resume_state(max_ticket_id_in_batch)
            print(f"Updated resume state to: {max_ticket_id_in_batch}")

    except FileNotFoundError:
        print(f"Error: The dump file was not found at {DUMP_CSV_PATH}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()