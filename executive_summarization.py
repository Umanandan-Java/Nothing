import sqlite3
import os
import torch
from tqdm import tqdm
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
# We only need the summarizer and key points models for this final version
SUMMARIZER_MODEL_NAME = "facebook/bart-large-cnn"
KEY_POINTS_MODEL_NAME = "google/flan-t5-base"


def run_section_analysis(conn, summarizer, key_points_extractor):
    """
    Part 1: Generates a summary paragraph and bulleted key points for
    each section based on all of its comments.
    """
    cursor = conn.cursor()
    print("--- Starting Part 1: Section-Wise Executive Analysis ---")
    
    cursor.execute("SELECT section_id FROM sections")
    all_section_ids = [row['section_id'] for row in cursor.fetchall()]
    
    section_updates = []
    for section_id in tqdm(all_section_ids, desc="Analyzing Sections"):
        # Check if already processed to allow re-running the script
        cursor.execute("SELECT section_ai_key_points FROM sections WHERE section_id = ?", (section_id,))
        if cursor.fetchone()['section_ai_key_points']:
             print(f"\nSkipping Section ID: {section_id} - already analyzed.")
             continue

        # Gather all relevant comments for the section
        cursor.execute("""
            SELECT comment_text FROM comments 
            WHERE section_id = ? AND comment_text IS NOT NULL AND LENGTH(comment_text) > 20
        """, (section_id,))
        
        comments = [row['comment_text'] for row in cursor.fetchall()]
        
        if len(comments) < 2:
            print(f"\nSkipping Section ID: {section_id} (not enough comments for a meaningful summary).")
            continue

        print(f"\nProcessing Section ID: {section_id} with {len(comments)} comments...")
        
        combined_text = "\n\n".join(comments)

        try:
            # Generate the executive summary paragraph for the whole section
            summary_paragraph = summarizer(
                combined_text, max_length=256, min_length=64, do_sample=False, truncation=True
            )[0]['summary_text']
            
            # Use the instruction model to extract clean bullet points from that summary
            key_point_prompt = f"Extract the key points as a bulleted list from the following text:\n{summary_paragraph}"
            key_points = key_points_extractor(
                key_point_prompt, max_length=256, truncation=True
            )[0]['generated_text']

            section_updates.append((summary_paragraph, key_points, section_id))
        except Exception as e:
            print(f"    - ERROR processing Section ID {section_id}: {e}")

    if section_updates:
        update_query = "UPDATE sections SET section_ai_summary = ?, section_ai_key_points = ? WHERE section_id = ?"
        cursor.executemany(update_query, section_updates)
        conn.commit()
        print(f"\nPart 1 Complete: Successfully updated {len(section_updates)} sections with executive analysis.")
    else:
        print("\nPart 1 Complete: No new sections to update.")


def run_draft_analysis_simplified(conn, summarizer):
    """
    Part 2 (Simplified): Generates a single summary paragraph for each draft by
    rolling up the section-level summaries.
    """
    cursor = conn.cursor()
    print("\n--- Starting Part 2: Draft-Wise Roll-up Analysis ---")
    
    cursor.execute("SELECT draft_id FROM drafts")
    all_draft_ids = [row['draft_id'] for row in cursor.fetchall()]
    
    draft_updates = []
    for draft_id in tqdm(all_draft_ids, desc="Analyzing Drafts"):
        # Check if already processed
        cursor.execute("SELECT draft_ai_summary FROM drafts WHERE draft_id = ?", (draft_id,))
        if cursor.fetchone()['draft_ai_summary']:
             print(f"\nSkipping Draft ID: {draft_id} - already analyzed.")
             continue

        # Gather the summaries from the child sections
        cursor.execute("""
            SELECT section_ai_summary FROM sections 
            WHERE draft_id = ? AND section_ai_summary IS NOT NULL AND section_ai_summary != ''
        """, (draft_id,))
        
        section_summaries = [row['section_ai_summary'] for row in cursor.fetchall()]
        
        if not section_summaries:
            print(f"\nSkipping Draft ID: {draft_id} (no section summaries to roll up).")
            continue

        print(f"\nProcessing Draft ID: {draft_id} by rolling up {len(section_summaries)} section summaries...")
        
        try:
            # Create a "summary of summaries"
            combined_summaries = "\n\n".join(section_summaries)
            draft_summary_paragraph = summarizer(
                combined_summaries, max_length=400, min_length=100, do_sample=False, truncation=True
            )[0]['summary_text']
            
            draft_updates.append((draft_summary_paragraph, draft_id))
        except Exception as e:
            print(f"    - ERROR processing Draft ID {draft_id}: {e}")

    if draft_updates:
        # Note: We are only updating one column now.
        update_query = "UPDATE drafts SET draft_ai_summary = ? WHERE draft_id = ?"
        cursor.executemany(update_query, draft_updates)
        conn.commit()
        print(f"\nPart 2 Complete: Successfully updated {len(draft_updates)} drafts.")
    else:
        print("\nPart 2 Complete: No new drafts to update.")


def main():
    """
    Main orchestrator for the entire Phase 2 process.
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        print("Successfully connected to the database.")

        print("Loading AI models... (This may take several minutes)")
        summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, device=device)
        key_points_extractor = pipeline("text2text-generation", model=KEY_POINTS_MODEL_NAME, device=device)
        print("All models loaded successfully.\n")

        # --- RUN THE PROCESS IN THE CORRECT ORDER ---
        run_section_analysis(conn, summarizer, key_points_extractor)
        run_draft_analysis_simplified(conn, summarizer)

    except Exception as e:
        print(f"A critical error occurred in the main process: {e}")
    finally:
        if conn:
            conn.close()
            print("\nPhase 2 analysis is complete. Database connection closed.")


if __name__ == '__main__':
    main()