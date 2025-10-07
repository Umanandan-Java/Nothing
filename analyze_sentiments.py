import sqlite3
import os
from transformers import pipeline
from tqdm import tqdm

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

def analyze_and_update_sentiments_v2():
    """
    V2: Connects to the database, first handles simple rule-based sentiments,
    then analyzes the rest with the AI model, ensuring all comments are processed.
    """
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: Database file '{DATABASE_FILE}' not found.")
        print("Please run the 'setup_database.py' script first to create and populate it.")
        return

    conn = None
    try:
        # --- 1. Connect to the Database ---
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print("Successfully connected to the database.")

        # --- PRELIMINARY STEP: Handle Rule-Based Sentiments ---
        print("Processing simple rule-based sentiments first...")
        
        # Rule 1: 'Suggest removal' is always Negative
        cursor.execute("""
            UPDATE comments
            SET sentiment_label = 'Negative', sentiment_score = 1.0
            WHERE action_type = 'Suggest removal' AND sentiment_label IS NULL
        """)
        removed_count = cursor.rowcount

        # Rule 2: 'In Agreement' with no text is always Positive
        cursor.execute("""
            UPDATE comments
            SET sentiment_label = 'Positive', sentiment_score = 1.0
            WHERE action_type = 'In Agreement' AND (comment_text IS NULL OR comment_text = '') AND sentiment_label IS NULL
        """)
        agreed_count = cursor.rowcount

        conn.commit()
        
        if (removed_count + agreed_count) > 0:
            print(f"Updated {removed_count} 'Suggest removal' and {agreed_count} 'In Agreement' comments based on rules.")

        # --- 2. Fetch Remaining Unprocessed Comments with Text ---
        cursor.execute("SELECT comment_id, comment_text FROM comments WHERE sentiment_label IS NULL AND comment_text IS NOT NULL AND comment_text != ''")
        comments_to_process = cursor.fetchall()
        
        if not comments_to_process:
            print("No new comments to analyze with AI. All comments have been processed.")
            return

        print(f"Found {len(comments_to_process)} comments that require AI analysis.")

        # --- 3. Load the AI Model ---
        print(f"Loading sentiment analysis model: '{MODEL_NAME}'...")
        sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME, top_k=None)
        print("Model loaded successfully.")
        
        # --- 4. Process with AI and Prepare for Update ---
        updates_to_make = []
        print("Analyzing sentiments with AI...")
        
        for comment_id, comment_text in tqdm(comments_to_process, desc="Processing Comments"):
            try:
                results = sentiment_pipeline(comment_text)
                top_result = results[0][0] 
                label = top_result['label'].capitalize()
                score = top_result['score']
                
                sentiment_label = 'Neutral' # Default
                if label == 'Negative':
                    sentiment_label = 'Negative'
                elif label == 'Positive':
                    sentiment_label = 'Positive'
                    
                updates_to_make.append((sentiment_label, score, comment_id))
            
            except Exception as e:
                print(f"\nCould not process comment_id {comment_id}. Error: {e}")
                updates_to_make.append(('Error', 0.0, comment_id))

        # --- 5. Update the Database ---
        if updates_to_make:
            print("\nAI Analysis complete. Updating the database...")
            update_query = "UPDATE comments SET sentiment_label = ?, sentiment_score = ? WHERE comment_id = ?"
            cursor.executemany(update_query, updates_to_make)
            conn.commit()
            print(f"Successfully updated {len(updates_to_make)} records in the database with AI results.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == '__main__':
    analyze_and_update_sentiments_v2()