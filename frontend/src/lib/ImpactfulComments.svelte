<script>
    export let commentsForDisplay = [];

    // The minimum number of comments required to show the "impactful" list.
    const MIN_COMMENTS_THRESHOLD = 3;

    $: topComments = (() => {
        // 1. Filter out comments that don't have an AI summary, as they can't be displayed.
        const relevantComments = commentsForDisplay.filter(c => c.ai_summary);

        // 2. Separate comments into 'Positive' and 'Negative' based on their sentiment_label.
        const positiveComments = relevantComments.filter(c => c.sentiment_label === 'Positive');
        const negativeComments = relevantComments.filter(c => c.sentiment_label === 'Negative');

        let topPositive = [];
        let topNegative = [];

        // 3. Process POSITIVE comments
        // Check if we have enough positive comments to meet the threshold.
        if (positiveComments.length >= MIN_COMMENTS_THRESHOLD) {
            // Sort by the 'score_positive' in descending order (highest score first).
            const sortedPositive = positiveComments.sort((a, b) => 
                (b.score_positive || 0) - (a.score_positive || 0)
            );
            // Take the top 3.
            topPositive = sortedPositive.slice(0, 3);
        }

        // 4. Process NEGATIVE comments
        // Check if we have enough negative comments to meet the threshold.
        if (negativeComments.length >= MIN_COMMENTS_THRESHOLD) {
            // Sort by the 'score_negative' in descending order (highest score first).
            const sortedNegative = negativeComments.sort((a, b) => 
                (b.score_negative || 0) - (a.score_negative || 0)
            );
            // Take the top 3.
            topNegative = sortedNegative.slice(0, 3);
        }

        // 5. Return the final lists. They will be empty if the threshold isn't met.
        return { topPositive, topNegative };
    })();
</script>

<div class="impactful-comments">
    <div class="comment-section positive-section">
        <h4>Most Positive Comments</h4>
        
        {#if topComments.topPositive.length > 0}
            {#each topComments.topPositive as comment}
                <div class="comment-card positive">
                    <div class="comment-header">
                        <span class="section-badge">{comment.section_title}</span>
                        <span class="action-badge">{comment.action_type}</span>
                        <span class="sentiment-score">
                            👍 {comment.score_positive?.toFixed(2)}
                        </span>
                    </div>
                    <p class="comment-summary">{comment.ai_summary}</p>
                    <div class="comment-meta">
                        <span class="industry">{comment.industry || 'Individual'}</span>
                        <span class="state">{comment.state}</span>
                    </div>
                </div>
            {/each}
        {:else}
            <div class="no-comments-message">
                Not enough positive comments in this selection to display a top list.
            </div>
        {/if}
    </div>

    <div class="comment-section negative-section">
        <h4>Most Critical Comments</h4>

        {#if topComments.topNegative.length > 0}
            {#each topComments.topNegative as comment}
                <div class="comment-card negative">
                     <div class="comment-header">
                        <span class="section-badge">{comment.section_title}</span>
                        <span class="action-badge">{comment.action_type}</span>
                        <span class="sentiment-score">
                            👎 {comment.score_negative?.toFixed(2)}
                        </span>
                    </div>
                    <p class="comment-summary">{comment.ai_summary}</p>
                    <div class="comment-meta">
                        <span class="industry">{comment.industry || 'Individual'}</span>
                        <span class="state">{comment.state}</span>
                    </div>
                </div>
            {/each}
        {:else}
             <div class="no-comments-message">
                Not enough negative comments in this selection to display a top list.
            </div>
        {/if}
    </div>
</div>
<style>
    .impactful-comments {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }

    .comment-section h4 {
        margin: 0 0 1rem 0;
        padding: 0.75rem;
        background: #fafafa;
        border-radius: 8px;
        text-align: center;
        font-size: 0.95rem;
        font-weight: 600;
        color: #495057;
    }
    /* ... add this at the end of your existing styles ... */

.no-comments-message {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
    height: 100%;
    color: #6c757d;
    background-color: #f8f9fa;
    border-radius: 8px;
    font-style: italic;
    font-size: 0.9rem;
}

    .comment-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
        border-left: 4px solid;
    }

    .comment-card.positive {
        border-left-color: #28a745;
        background-color: #DBFAE6;
    }

    .comment-card.negative {
        border-left-color: #dc3545;
        background-color: #FDE8E8;
    }

    .comment-header {
        display: flex;
        justify-content: space-between;
        align-items: center; /* Vertically align items in the header */
        margin-bottom: 0.75rem;
        gap: 0.5rem;
    }

    .section-badge, .action-badge {
        font-size: 0.7rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 600;
    }

    .section-badge {
        /* background: #e3f2fd; */
        color: #1976d2;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .action-badge {
        background: #f5f5f5;
        color: #666;
    }

    .comment-summary {
        font-size: 0.85rem;
        line-height: 1.5;
        color: #333;
        margin: 0 0 0.75rem 0;
    }

    .comment-meta {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        color: #6c757d;
    }

    .industry {
        font-weight: 600;
    }

    .sentiment-score {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
    }

    .comment-card.positive .sentiment-score {
        background-color: rgba(40, 167, 69, 0.1); 
        color: #28a745;
    }

    .comment-card.negative .sentiment-score {
        background-color: rgba(220, 53, 69, 0.1); /* Light red */
        color: #dc3545;
    }

    .sentiment-score .icon {
        font-size: 0.8rem;
    }
</style>