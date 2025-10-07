import sqlite3
import os
from transformers import pipeline
from tqdm import tqdm
import torch

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

def analyze_all_sentiments_detailed():
    """
    Analyzes every comment, stores the probability scores for Positive, Negative,
    and Neutral sentiments in separate columns, and then determines the final
    sentiment_label based on the highest of these three scores.
    """
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: Database file '{DATABASE_FILE}' not found.")
        return

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print("Successfully connected to the database.")

        # --- Fetch all comments that need analysis ---
        # We check if 'score_positive' is NULL as our new marker for unprocessed comments
        cursor.execute("""
            SELECT comment_id, comment_text FROM comments 
            WHERE 
                (score_positive IS NULL) AND 
                (comment_text IS NOT NULL AND comment_text != '')
        """)
        comments_to_process = cursor.fetchall()
        
        if not comments_to_process:
            print("No new comments to analyze.")
            return

        print(f"Found {len(comments_to_process)} comments that require AI analysis.")

        # --- Load the AI Model ---
        # 'top_k=None' ensures the model returns scores for all available labels
        sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME, device=device, top_k=None)
        print("Model loaded successfully.")
        
        updates_to_make = []
        print("Analyzing sentiments for all comments...")
        
        for comment_id, comment_text in tqdm(comments_to_process, desc="Processing Comments"):
            try:
                # The model returns a list containing a list of dictionaries, one for each label.
                # e.g., [[{'label': 'positive', 'score': 0.8}, {'label': 'negative', 'score': 0.1}, ...]]
                results = sentiment_pipeline(comment_text)
                
                # --- THIS IS THE NEW LOGIC ---
                
                # 1. Create a dictionary for easy score lookup
                scores = {item['label']: item['score'] for item in results[0]}
                
                score_pos = scores.get('positive', 0.0)
                score_neg = scores.get('negative', 0.0)
                score_neu = scores.get('neutral', 0.0)
                
                # 2. Determine the final label based on the highest score
                if score_pos > score_neg and score_pos > score_neu:
                    final_label = 'Positive'
                    # For sentiment_score column, we use the [-1, 1] format
                    final_score_db = score_pos
                elif score_neg > score_pos and score_neg > score_neu:
                    final_label = 'Negative'
                    final_score_db = -score_neg # Make the score negative
                else:
                    final_label = 'Neutral'
                    final_score_db = 0.0 # Neutral is represented as 0
                
                # 3. Prepare all values for the database update
                updates_to_make.append((
                    final_label, 
                    final_score_db,
                    score_pos,
                    score_neg,
                    score_neu,
                    comment_id
                ))
            
            except Exception as e:
                print(f"\nCould not process comment_id {comment_id}. Error: {e}")
                updates_to_make.append(('Error', 0.0, 0.0, 0.0, 0.0, comment_id))

        # --- Update the Database with the new, detailed information ---
        if updates_to_make:
            print("\nAI Analysis complete. Updating the database...")
            # This query now updates all 5 columns
            update_query = """
                UPDATE comments SET 
                    sentiment_label = ?, 
                    sentiment_score = ?, 
                    score_positive = ?,
                    score_negative = ?,
                    score_neutral = ?
                WHERE comment_id = ?
            """
            cursor.executemany(update_query, updates_to_make)
            conn.commit()
            print(f"Successfully updated {len(updates_to_make)} records with detailed sentiment scores.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == '__main__':
    # You can use your db_manager.py script or run a one-time query to reset
    # the new columns if you need to re-run the analysis.
    # e.g., UPDATE comments SET score_positive = NULL, sentiment_label = NULL, ...
    
    analyze_all_sentiments_detailed()