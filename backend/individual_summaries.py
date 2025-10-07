import sqlite3
import os
from transformers import pipeline
from tqdm import tqdm
import torch

DATABASE_FILE = "econsultation.db"
# We will use the model that has proven to be the best at following instructions.
MODEL_NAME = "google/flan-t5-base"

def generate_individual_summaries_final_simple():
    """
    (FINAL, NO CONTEXT): The simplest possible approach.
    Generates a summary of ONLY the comment text with a direct, clean prompt.
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # This query gets only what we need: the ID and the text.
        query = """
            SELECT comment_id, comment_text FROM comments
            WHERE (ai_summary IS NULL OR ai_summary = 'Error generating summary.')
              AND (comment_text IS NOT NULL AND LENGTH(comment_text) > 15)
        """
        cursor.execute(query)
        comments_to_process = cursor.fetchall()
        
        if not comments_to_process:
            print("No new comments to summarize.")
            return

        print(f"Found {len(comments_to_process)} comments for direct summarization.")

        print(f"Loading summarization model: '{MODEL_NAME}'...")
        summarizer = pipeline("text2text-generation", model=MODEL_NAME, device=device)
        print("Model loaded successfully.")
        
        updates_to_make = []
        for comment_row in tqdm(comments_to_process, desc="Summarizing Comments"):
            try:
                comment_id = comment_row['comment_id']
                comment_text = comment_row['comment_text']

                # --- THE SIMPLEST POSSIBLE PROMPT ---
                # A direct, unambiguous command.
                prompt = f"Summarize the following text in a single, concise sentence:\n\n'{comment_text}'"

                summary_text = summarizer(
                    prompt, 
                    max_length=80, 
                    min_length=10, 
                    do_sample=False,
                    truncation=True
                )[0]['generated_text']
                
                # Minimal cleanup for safety
                final_summary = summary_text.strip().strip('"')

                updates_to_make.append((final_summary, comment_id))
            except Exception as e:
                print(f"\nCould not process comment_id {comment_id}. Error: {e}")
                updates_to_make.append(('Error generating summary.', comment_id))

        if updates_to_make:
            update_query = "UPDATE comments SET ai_summary = ? WHERE comment_id = ?"
            cursor.executemany(update_query, updates_to_make)
            conn.commit()
            print(f"\nSuccessfully updated {len(updates_to_make)} records.")

    finally:
        if conn: conn.close()
        print("Individual summary generation is complete.")


if __name__ == '__main__':
    # Use your db_manager.py script to clear all old, bad summaries first.
    # python db_manager.py --reset-summaries
    
    generate_individual_summaries_final_simple()