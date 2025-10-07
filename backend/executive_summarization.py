import sqlite3
import os
import torch
from tqdm import tqdm
from transformers import pipeline

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
SUMMARIZER_MODEL_NAME = "facebook/bart-large-cnn"
KEY_POINTS_MODEL_NAME = "google/flan-t5-base"


def generate_summary_for_group(comments, summarizer):
    """A helper function to generate a summary for a list of comments."""
    if not comments:
        return None
    
    combined_text = "\n\n".join(comments)
    try:
        summary = summarizer(
            combined_text, max_length=256, min_length=64, do_sample=False, truncation=True
        )[0]['summary_text']
        return summary
    except Exception as e:
        print(f"    - Error during summarization: {e}")
        return None


def run_section_analysis(conn, summarizer, key_points_extractor):
    """
    Part 1: Generates an overall summary, sentiment-specific summaries,
    and bulleted key points for each section.
    """
    cursor = conn.cursor()
    print("--- Starting Part 1: Section-Wise Analysis (with Sentiment Splits) ---")
    
    cursor.execute("SELECT section_id FROM sections")
    all_section_ids = [row['section_id'] for row in cursor.fetchall()]
    
    for section_id in tqdm(all_section_ids, desc="Analyzing Sections"):
        print(f"\nProcessing Section ID: {section_id}")
        
        # Gather all comments for the section, including their sentiment
        cursor.execute("""
            SELECT comment_text, sentiment_label FROM comments 
            WHERE section_id = ? AND comment_text IS NOT NULL AND LENGTH(comment_text) > 20
        """, (section_id,))
        
        all_comments = cursor.fetchall()
        
        if len(all_comments) < 2:
            print("    - Skipping section (not enough comments).")
            continue

        # Filter comments by sentiment
        positive_comments = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Positive']
        negative_comments = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Negative']
        neutral_comments = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Neutral']

        # Generate summaries for each group
        print("    - Generating overall and sentiment-specific summaries...")
        summary_overall = generate_summary_for_group([row['comment_text'] for row in all_comments], summarizer)
        summary_pos = generate_summary_for_group(positive_comments, summarizer)
        summary_neg = generate_summary_for_group(negative_comments, summarizer)
        summary_neu = generate_summary_for_group(neutral_comments, summarizer)

        # Generate key points from the overall summary
        key_points = None
        if summary_overall:
            print("    - Generating key points...")
            try:
                key_point_prompt = f"Extract the key points as a bulleted list from the following text:\n{summary_overall}"
                key_points = key_points_extractor(key_point_prompt, max_length=256, truncation=True)[0]['generated_text']
            except Exception as e:
                print(f"    - Error generating key points: {e}")

        # Update the database for this section
        cursor.execute("""
            UPDATE sections SET 
                section_ai_summary = ?,
                section_ai_key_points = ?,
                summary_positive = ?,
                summary_negative = ?,
                summary_neutral = ?
            WHERE section_id = ?
        """, (summary_overall, key_points, summary_pos, summary_neg, summary_neu, section_id))
        conn.commit()

    print("\nPart 1 Complete: All sections have been analyzed.")


def run_draft_analysis(conn, summarizer):
    """
    Part 2: Generates an overall summary and sentiment-specific summaries
    for each draft by rolling up the section-level summaries.
    """
    cursor = conn.cursor()
    print("\n--- Starting Part 2: Draft-Wise Roll-up Analysis ---")
    
    cursor.execute("SELECT draft_id FROM drafts")
    all_draft_ids = [row['draft_id'] for row in cursor.fetchall()]
    
    for draft_id in tqdm(all_draft_ids, desc="Analyzing Drafts"):
        print(f"\nProcessing Draft ID: {draft_id}")
        
        # Gather all section summaries (overall and by sentiment)
        cursor.execute("""
            SELECT section_ai_summary, summary_positive, summary_negative, summary_neutral 
            FROM sections 
            WHERE draft_id = ? AND section_ai_summary IS NOT NULL
        """, (draft_id,))
        
        section_summaries = cursor.fetchall()
        
        if not section_summaries:
            print("    - Skipping draft (no section summaries to roll up).")
            continue
            
        print(f"    - Rolling up {len(section_summaries)} section summaries...")
        
        # Combine and summarize for each category
        summary_overall = generate_summary_for_group([row['section_ai_summary'] for row in section_summaries if row['section_ai_summary']], summarizer)
        summary_pos = generate_summary_for_group([row['summary_positive'] for row in section_summaries if row['summary_positive']], summarizer)
        summary_neg = generate_summary_for_group([row['summary_negative'] for row in section_summaries if row['summary_negative']], summarizer)
        summary_neu = generate_summary_for_group([row['summary_neutral'] for row in section_summaries if row['summary_neutral']], summarizer)

        # Update the database for this draft
        cursor.execute("""
            UPDATE drafts SET
                draft_ai_summary = ?,
                summary_positive = ?,
                summary_negative = ?,
                summary_neutral = ?
            WHERE draft_id = ?
        """, (summary_overall, summary_pos, summary_neg, summary_neu, draft_id))
        conn.commit()

    print("\nPart 2 Complete: All drafts have been analyzed.")


def main():
    """
    Main orchestrator for the entire summarization process.
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        print("Successfully connected to the database.")

        print("Loading AI models...")
        summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, device=device)
        key_points_extractor = pipeline("text2text-generation", model=KEY_POINTS_MODEL_NAME, device=device)
        print("All models loaded successfully.\n")

        # --- RUN THE PROCESS IN THE CORRECT ORDER ---
        run_section_analysis(conn, summarizer, key_points_extractor)
        run_draft_analysis(conn, summarizer)

    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("\nExecutive summary generation is complete.")


if __name__ == '__main__':
    main()