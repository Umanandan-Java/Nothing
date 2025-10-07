import sqlite3
import os
import re
from collections import Counter
import spacy
from wordcloud import WordCloud
from nltk.util import ngrams
from tqdm import tqdm

# --- Configuration ---
DATABASE_FILE = "econsultation.db"
# A single, organized folder for all our images
OUTPUT_FOLDER = "static/wordclouds"

# --- NLP Model Setup ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    exit()

CUSTOM_STOP_WORDS = [
    'user', 'comment', 'suggestion', 'propose', 'draft', 'legislation', 'amendment', 'provision',
    'section', 'act', 'rule', 'mca', 'stakeholder', 'company', 'government', 'clause',
    'say', 'propose', 'recommend', 'proviso', 'submit', 'state'
]

def generate_word_cloud(text_list, identifier, subfolder):
    """
    A generic function to generate and save a word cloud image for a given list of texts.
    'identifier' can be a draft_id, section_id, or comment_id.
    'subfolder' will be 'drafts', 'sections', or 'comments'.
    """
    if not text_list:
        print(f"    - No text provided for {identifier}, skipping.")
        return None

    full_text = " ".join(text_list)
    if len(full_text.split()) < 5: # Don't generate for very short comments
        print(f"    - Not enough text for {identifier}, skipping.")
        return None

    # 1. Clean and Lemmatize
    doc = nlp(full_text)
    meaningful_words = [
        token.lemma_.lower() for token in doc
        if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']
        and token.lemma_.lower() not in CUSTOM_STOP_WORDS
    ]
    
    # 2. Identify Key Phrases (only for multi-comment clouds)
    if len(text_list) > 1:
        bigram_counts = Counter(ngrams(meaningful_words, 2))
        top_phrases = {"_".join(phrase): count for phrase, count in bigram_counts.most_common(30) if count > 1}
    else:
        top_phrases = {}
        
    # 3. Combine Counts
    word_counts = Counter(meaningful_words)
    word_counts.update(top_phrases)

    if not word_counts:
        print(f"    - No meaningful words for {identifier}, skipping.")
        return None

    # 4. Generate Image
    wc = WordCloud(
        width=1200, height=600, background_color='white',
        colormap='magma', collocations=False, contour_width=1, contour_color='grey'
    ).generate_from_frequencies(word_counts)

    # 5. Save Image
    final_output_folder = os.path.join(OUTPUT_FOLDER, subfolder)
    if not os.path.exists(final_output_folder):
        os.makedirs(final_output_folder)

    image_path = os.path.join(final_output_folder, f"{identifier}.png")
    wc.to_file(image_path)
    
    return image_path


def run_all_word_cloud_generation():
    """
    Main orchestrator to generate word clouds for all levels:
    Drafts, Sections, and Individual Comments.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("Successfully connected to the database.")

        # --- Part 1: Generate Draft-Level Word Clouds ---
        print("\n--- Starting Part 1: Draft-Level Word Clouds ---")
        cursor.execute("SELECT draft_id FROM drafts")
        draft_ids = [row['draft_id'] for row in cursor.fetchall()]
        draft_updates = []
        for draft_id in tqdm(draft_ids, desc="Processing Drafts"):
            cursor.execute("SELECT c.comment_text FROM comments c JOIN submissions s ON c.submission_id = s.submission_id WHERE s.draft_id = ? AND c.comment_text IS NOT NULL", (draft_id,))
            comments = [row['comment_text'] for row in cursor.fetchall()]
            image_path = generate_word_cloud(comments, f"draft_{draft_id}", "drafts")
            if image_path: draft_updates.append((image_path, draft_id))
        
        if draft_updates:
            cursor.executemany("UPDATE drafts SET word_cloud_image_path = ? WHERE draft_id = ?", draft_updates)
            print(f"Successfully updated {len(draft_updates)} drafts.")


        # --- Part 2: Generate Section-Level Word Clouds ---
        print("\n--- Starting Part 2: Section-Level Word Clouds ---")
        cursor.execute("SELECT section_id FROM sections")
        section_ids = [row['section_id'] for row in cursor.fetchall()]
        section_updates = []
        for section_id in tqdm(section_ids, desc="Processing Sections"):
            cursor.execute("SELECT comment_text FROM comments WHERE section_id = ? AND comment_text IS NOT NULL", (section_id,))
            comments = [row['comment_text'] for row in cursor.fetchall()]
            image_path = generate_word_cloud(comments, f"section_{section_id}", "sections")
            if image_path: section_updates.append((image_path, section_id))

        if section_updates:
            cursor.executemany("UPDATE sections SET word_cloud_image_path = ? WHERE section_id = ?", section_updates)
            print(f"Successfully updated {len(section_updates)} sections.")

        
        # --- Part 3: Generate Individual Comment-Level Word Clouds ---
        print("\n--- Starting Part 3: Individual Comment-Level Word Clouds ---")
        cursor.execute("SELECT comment_id, comment_text FROM comments WHERE comment_text IS NOT NULL")
        all_comments = cursor.fetchall()
        comment_updates = []
        for comment in tqdm(all_comments, desc="Processing Comments"):
            comment_id = comment['comment_id']
            comment_text = comment['comment_text']
            # Pass the text as a list with one item
            image_path = generate_word_cloud([comment_text], f"comment_{comment_id}", "comments")
            if image_path: comment_updates.append((image_path, comment_id))
        
        if comment_updates:
             cursor.executemany("UPDATE comments SET word_cloud_image_path = ? WHERE comment_id = ?", comment_updates)
             print(f"Successfully updated {len(comment_updates)} comments.")
        
        conn.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("\nAll word cloud generation is complete. Database connection closed.")


if __name__ == '__main__':
    run_all_word_cloud_generation()