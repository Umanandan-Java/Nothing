import sqlite3
import os
import re
from transformers import pipeline
from tqdm import tqdm
import torch

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
# Reverting to the model that worked best for true summarization
SUMMARIZER_MODEL_NAME = "facebook/bart-large-cnn"

def clean_summary(raw_text):
    """
    The robust function to clean the AI's output by removing common,
    unwanted conversational prefixes.
    """
    # A comprehensive list of phrases to find and remove
    prefixes_to_remove = [
        "User:", "User commented:", "User's comment:", "User states:", "USER's COMMENT:", "USER COMMENT:",
        "The user is commenting on the draft law section titled", "The user commented on the draft law section",
        "The draft law section titled", "comment:", "SUMMARY OF THE USER'S COMMENT:",
        "The user is commenting on"
    ]
    cleaned_text = raw_text
    for prefix in prefixes_to_remove:
        # Use a case-insensitive search
        if cleaned_text.lower().strip().startswith(prefix.lower()):
            # Strip the prefix by its length to preserve the case of the rest of the string
            cleaned_text = cleaned_text.strip()[len(prefix):].strip()
            
    # Final cleanup of any stray characters left after stripping
    return cleaned_text.strip().lstrip(':"\' ').capitalize()


def generate_individual_summaries_bart_final():
    """
    (FINAL, BART-BASED): Uses the robust Bart-large-cnn model combined with
    a direct prompt and a powerful post-processing function to guarantee clean,
    high-quality summaries.
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("Successfully connected to the database.")
        
        # This query now correctly identifies unprocessed comments based on the schema
        query = """
            SELECT c.comment_id, c.comment_text, s.section_title
            FROM comments c
            JOIN sections s ON c.section_id = s.section_id
            WHERE 
                (c.ai_summary IS NULL OR c.ai_summary = 'Error generating summary.') AND
                (c.comment_text IS NOT NULL AND LENGTH(c.comment_text) > 20)
        """
        cursor.execute(query)
        comments_to_process = cursor.fetchall()
        
        if not comments_to_process:
            print("No new comments to summarize.")
            return

        print(f"Found {len(comments_to_process)} comments to re-process with the Bart model.")

        print(f"Loading summarization model: '{SUMMARIZER_MODEL_NAME}'... (This may take a moment)")
        summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, device=device)
        print("Model loaded successfully.")
        
        updates_to_make = []
        print("\nStarting final summarization run with robust post-processing.")
        
        for comment_row in tqdm(comments_to_process, desc="Summarizing Comments"):
            try:
                comment_id = comment_row['comment_id']
                
                # A simple, direct prompt that has proven to work well with this model
                prompt = (
                    f"Summarize the following user comment regarding the law section '{comment_row['section_title']}':\n\n"
                    f"\"{comment_row['comment_text']}\""
                )

                summary_result = summarizer(
                    prompt, max_length=80, min_length=15, do_sample=False
                )
                
                raw_summary = summary_result[0]['summary_text']
                
                # Use our powerful function to clean the output perfectly
                clean_summary_text = clean_summary(raw_summary)
                
                updates_to_make.append((clean_summary_text, comment_id))
            
            except Exception as e:
                print(f"\nCould not process comment_id {comment_id}. Error: {e}")
                updates_to_make.append(('Error generating summary.', comment_id))

        if updates_to_make:
            print("\nSummarization complete. Updating the database with final, clean results...")
            update_query = "UPDATE comments SET ai_summary = ? WHERE comment_id = ?"
            cursor.executemany(update_query, updates_to_make)
            conn.commit()
            print(f"Successfully updated {len(updates_to_make)} records.")

    finally:
        if conn:
            conn.close()
            print("\nIndividual summary generation is complete.")

if __name__ == '__main__':
    # Use your db_manager.py script to clear all old, bad summaries first.
    # python db_manager.py --reset-summaries
    generate_individual_summaries_bart_final()