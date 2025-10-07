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
    Generic function to generate and save a word cloud image.
    'identifier' includes level (draft/section) and id.
    'subfolder' groups images by level.
    """
    if not text_list:
        return None # No text, no word cloud

    full_text = " ".join(text_list)
    if len(full_text.split()) < 3: # Need at least a few words
        return None

    doc = nlp(full_text)
    meaningful_words = [
        token.lemma_.lower() for token in doc
        if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']
        and token.lemma_.lower() not in CUSTOM_STOP_WORDS
    ]
    
    bigram_counts = Counter(ngrams(meaningful_words, 2))
    top_phrases = {"_".join(phrase): count for phrase, count in bigram_counts.most_common(30) if count > 1}
        
    word_counts = Counter(meaningful_words)
    word_counts.update(top_phrases)

    if not word_counts:
        return None

    # Determine color scheme based on sentiment in identifier
    colormap = 'viridis' # Default
    if 'positive' in identifier: colormap = 'Greens'
    if 'negative' in identifier: colormap = 'Reds'
    if 'neutral' in identifier: colormap = 'Blues'
        
    wc = WordCloud(
        width=1200, height=600, background_color='white',
        colormap=colormap, collocations=False
    ).generate_from_frequencies(word_counts)

    final_output_folder = os.path.join(OUTPUT_FOLDER, subfolder)
    if not os.path.exists(final_output_folder):
        os.makedirs(final_output_folder)

    # Use a safe filename
    safe_identifier = re.sub(r'[^a-zA-Z0-9_-]+', '', identifier)
    image_path = os.path.join(final_output_folder, f"{safe_identifier}.png")
    wc.to_file(image_path)
    
    return image_path


def main():
    """
    Main orchestrator to generate overall, sentiment-specific, and individual word clouds.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("Successfully connected to the database.")
        
        # --- Process Sections First ---
        print("\n--- Starting Section-Level Word Cloud Generation ---")
        cursor.execute("SELECT section_id FROM sections")
        section_ids = [row['section_id'] for row in cursor.fetchall()]
        
        for section_id in tqdm(section_ids, desc="Processing Sections"):
            print(f"\nProcessing Section ID: {section_id}")
            
            cursor.execute("SELECT comment_text, sentiment_label FROM comments WHERE section_id = ? AND comment_text IS NOT NULL", (section_id,))
            all_comments = cursor.fetchall()

            if not all_comments: continue

            # Filter comments by sentiment
            all_texts = [row['comment_text'] for row in all_comments]
            pos_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Positive']
            neg_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Negative']
            neu_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Neutral']
            
            # Generate word clouds for each group
            wc_overall = generate_word_cloud(all_texts, f"section_{section_id}_overall", "sections")
            wc_pos = generate_word_cloud(pos_texts, f"section_{section_id}_positive", "sections")
            wc_neg = generate_word_cloud(neg_texts, f"section_{section_id}_negative", "sections")
            wc_neu = generate_word_cloud(neu_texts, f"section_{section_id}_neutral", "sections")

            # Update database
            cursor.execute("""
                UPDATE sections SET 
                    word_cloud_image_path = ?, wordcloud_positive_path = ?, 
                    wordcloud_negative_path = ?, wordcloud_neutral_path = ?
                WHERE section_id = ?
            """, (wc_overall, wc_pos, wc_neg, wc_neu, section_id))
            conn.commit()

        # --- Process Drafts (Roll-up) ---
        print("\n--- Starting Draft-Level Word Cloud Generation ---")
        cursor.execute("SELECT draft_id FROM drafts")
        draft_ids = [row['draft_id'] for row in cursor.fetchall()]

        for draft_id in tqdm(draft_ids, desc="Processing Drafts"):
            print(f"\nProcessing Draft ID: {draft_id}")

            cursor.execute("""
                SELECT c.comment_text, c.sentiment_label
                FROM comments c JOIN submissions s ON c.submission_id = s.submission_id
                WHERE s.draft_id = ? AND c.comment_text IS NOT NULL
            """, (draft_id,))
            all_comments = cursor.fetchall()
            
            if not all_comments: continue
                
            all_texts = [row['comment_text'] for row in all_comments]
            pos_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Positive']
            neg_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Negative']
            neu_texts = [row['comment_text'] for row in all_comments if row['sentiment_label'] == 'Neutral']
            
            wc_overall = generate_word_cloud(all_texts, f"draft_{draft_id}_overall", "drafts")
            wc_pos = generate_word_cloud(pos_texts, f"draft_{draft_id}_positive", "drafts")
            wc_neg = generate_word_cloud(neg_texts, f"draft_{draft_id}_negative", "drafts")
            wc_neu = generate_word_cloud(neu_texts, f"draft_{draft_id}_neutral", "drafts")
            
            cursor.execute("""
                UPDATE drafts SET
                    word_cloud_image_path = ?, wordcloud_positive_path = ?,
                    wordcloud_negative_path = ?, wordcloud_neutral_path = ?
                WHERE draft_id = ?
            """, (wc_overall, wc_pos, wc_neg, wc_neu, draft_id))
            conn.commit()

        # --- Process Individual Comments ---
        print("\n--- Starting Individual Comment-Level Word Clouds ---")
        cursor.execute("SELECT comment_id, comment_text FROM comments WHERE comment_text IS NOT NULL")
        all_individual_comments = cursor.fetchall()
        
        comment_updates = []
        for comment in tqdm(all_individual_comments, desc="Processing Individual Comments"):
            path = generate_word_cloud([comment['comment_text']], f"comment_{comment['comment_id']}", "comments")
            if path:
                comment_updates.append((path, comment['comment_id']))
                
        if comment_updates:
             cursor.executemany("UPDATE comments SET word_cloud_image_path = ? WHERE comment_id = ?", comment_updates)
             conn.commit()
             print(f"\nSuccessfully updated {len(comment_updates)} individual comments.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("\nAll word cloud generation is complete.")


if __name__ == '__main__':
    main()