import sqlite3
import argparse
import os

DATABASE_FILE = "econsultation.db"

def run_query(query, params=(), commit=False):
    """A helper function to connect to the DB and run a single query."""
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: Database file '{DATABASE_FILE}' not found.")
        return None
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
            print("Query executed and changes were committed.")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def execute_sql_from_string(sql_string):
    """Executes a raw SQL string containing one or more commands."""
    print("Executing custom SQL query...")
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: Database file '{DATABASE_FILE}' not found.")
        return
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # executescript can handle multiple SQL statements separated by semicolons
        cursor.executescript(sql_string)
        conn.commit()
        print("Custom SQL executed successfully and changes were committed.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def reset_sentiment_analysis():
    """Resets all sentiment-related columns in the comments table."""
    print("Resetting all sentiment analysis columns in 'comments' table...")
    query = """
        UPDATE comments SET
            sentiment_label = NULL,
            sentiment_score = NULL,
            score_positive = NULL,
            score_negative = NULL,
            score_neutral = NULL;
    """
    run_query(query, commit=True)
    print("Sentiment analysis columns have been reset.")

def reset_summaries():
    """Resets all AI-generated summary and key point columns in all tables."""
    print("Resetting all summary and key point columns...")
    queries = [
        "UPDATE comments SET ai_summary = NULL;",
        "UPDATE sections SET section_ai_summary = NULL, section_ai_key_points = NULL, summary_positive = NULL, summary_negative = NULL, summary_neutral = NULL;",
        "UPDATE drafts SET draft_ai_summary = NULL, summary_positive = NULL, summary_negative = NULL, summary_neutral = NULL;"
    ]
    for query in queries:
        run_query(query, commit=True)
    print("All summary-related columns have been reset.")

def reset_wordclouds():
    """Resets all word cloud image path columns in all tables."""
    print("Resetting all word cloud paths...")
    queries = [
        "UPDATE comments SET word_cloud_image_path = NULL;",
        "UPDATE sections SET word_cloud_image_path = NULL, wordcloud_positive_path = NULL, wordcloud_negative_path = NULL, wordcloud_neutral_path = NULL;",
        "UPDATE drafts SET word_cloud_image_path = NULL, wordcloud_positive_path = NULL, wordcloud_negative_path = NULL, wordcloud_neutral_path = NULL;"
    ]
    for query in queries:
        run_query(query, commit=True)
    print("All word cloud path columns have been reset.")
    
def reset_all_ai_data():
    """A master function to reset ALL AI-generated data."""
    print("--- RESETTING ALL AI-GENERATED DATA ---")
    reset_sentiment_analysis()
    reset_summaries()
    reset_wordclouds()
    print("\n--- All AI data has been cleared. ---")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A utility script to manage the econsultation.db database.")
    
    # --- ADD ARGUMENTS FOR EACH FUNCTION ---
    
    parser.add_argument(
        '--reset-all', 
        action='store_true',
        help="MASTER RESET: Resets ALL AI-generated columns (sentiment, summaries, wordclouds)."
    )
    parser.add_argument(
        '--reset-sentiment', 
        action='store_true',
        help="Resets all 5 sentiment score and label columns in the comments table."
    )
    parser.add_argument(
        '--reset-summaries',
        action='store_true',
        help="Resets all summary and key point columns in drafts, sections, and comments."
    )
    parser.add_argument(
        '--reset-wordclouds',
        action='store_true',
        help="Resets all word cloud image path columns in all tables."
    )
    parser.add_argument(
        '--execute-sql',
        type=str,
        help="Executes a given SQL query string directly on the database. Use with caution. Example: --execute-sql \"INSERT INTO ...\""
    )
    
    args = parser.parse_args()

    # --- EXECUTE THE CORRECT FUNCTION ---
    if args.reset_all:
        reset_all_ai_data()
    elif args.reset_sentiment:
        reset_sentiment_analysis()
    elif args.reset_summaries:
        reset_summaries()
    elif args.reset_wordclouds:
        reset_wordclouds()
    elif args.execute_sql:
        execute_sql_from_string(args.execute_sql)
    else:
        print("No action specified. Please provide an argument to perform an operation.")
        parser.print_help()