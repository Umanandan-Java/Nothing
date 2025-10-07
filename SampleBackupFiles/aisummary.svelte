<script>
    import { onMount } from 'svelte';
    import { chart } from '$lib/chartAction.js';

    // --- State Management ---
    let drafts = [];
    let allComments = [];
    let sections = [];
    let selectedDraftId = '';
    let selectedSectionId = 'all';

    // --- Derived State ---
    $: commentsForDisplay = (() => {
        if (!selectedDraftId) return [];
        if (selectedSectionId === 'all') return allComments;
        return allComments.filter(c => c.section_id == selectedSectionId);
    })();

    let sentimentScore = 0;
    let gaugeChartConfig = {};
    let barChartConfig = {};

    $: {
        if (!commentsForDisplay || commentsForDisplay.length === 0) {
            sentimentScore = 0;
        } else {
            const total = commentsForDisplay.reduce((acc, c) => {
                if (c.sentiment_label === 'Positive') return acc + 1;
                if (c.sentiment_label === 'Negative') return acc - 1;
                return acc;
            }, 0);
            sentimentScore = (total / commentsForDisplay.length) * 100;
        }

        // Calculate sentiment counts for bar chart
        const positiveCount = commentsForDisplay.filter(c => c.sentiment_label === 'Positive').length;
        const neutralCount = commentsForDisplay.filter(c => c.sentiment_label === 'Neutral').length;
        const negativeCount = commentsForDisplay.filter(c => c.sentiment_label === 'Negative').length;

        const normalizedScore = sentimentScore + 100; // [-100, 100] to [0, 200]
        const sentimentColor = getSentimentColor(sentimentScore);
        
        gaugeChartConfig = {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [normalizedScore, 200 - normalizedScore],
                    backgroundColor: [sentimentColor, '#f0f0f0'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    tooltip: { enabled: false },
                    legend: { display: false },
                    datalabels: { display: false }
                }
            },
            plugins: []
        };

        // Bar Chart Configuration
        barChartConfig = {
            type: 'bar',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    label: 'No of Comments',
                    data: [positiveCount, neutralCount, negativeCount],
                    backgroundColor: ['#28a745', '#007bff', '#dc3545'],
                    borderRadius: 8,
                    barThickness: 60
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#fff',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return 'Comments: ' + context.parsed.y;
                            }
                        }
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        color: '#333',
                        font: {
                            weight: 'bold',
                            size: 14
                        },
                        formatter: function(value) {
                            return value;
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: '#666',
                            font: { size: 12 }
                        },
                        grid: {
                            color: '#e9ecef',
                            drawBorder: false
                        },
                        title: {
                            display: true,
                            text: 'No of Comments received in each Sentiment Label',
                            color: '#333',
                            font: {
                                size: 11,
                                weight: 'normal'
                            },
                            padding: { top: 0, bottom: 10 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#333',
                            font: { 
                                size: 13,
                                weight: '600'
                            }
                        }
                    }
                }
            }
        };
    }
    
    $: selectedDraft = drafts.find(d => d.draft_id == selectedDraftId) || null;
    $: selectedSection = sections.find(s => s.section_id == selectedSectionId) || null;
    $: displayData = (selectedSectionId === 'all' || !selectedSection) ? selectedDraft : selectedSection;
    $: displayTitle = (selectedSectionId === 'all' || !selectedSection) 
        ? `Overall Draft: ${selectedDraft?.title || ''}` 
        : selectedSection?.section_title || '';
    $: displaySummary = (selectedSectionId === 'all' || !selectedSection) 
        ? selectedDraft?.draft_ai_summary 
        : selectedSection?.section_ai_summary;
        
    const API_BASE_URL = 'http://127.0.0.1:5000';

    onMount(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/drafts`);
            drafts = await res.json();
        } catch (error) {
            console.error('Error fetching drafts:', error);
        }
    });
    
    $: if (selectedDraftId) handleDraftChange();

    async function handleDraftChange() {
        if (!selectedDraftId) { 
            sections = []; 
            allComments = []; 
            return; 
        }
        selectedSectionId = 'all';
        
        try {
            const [commentsRes, sectionsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/comments/${selectedDraftId}`),
                fetch(`${API_BASE_URL}/api/sections/${selectedDraftId}`)
            ]);
            allComments = await commentsRes.json();
            sections = await sectionsRes.json();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }
    
    function getSentimentColor(score) {
        if (score < -5) return '#dc3545'; // Red
        if (score <= 5) return '#6c757d'; // Neutral Grey
        return '#28a745'; // Green
    }
    
    function getSentimentText(score) {
        if (score < -5) return 'Negative';
        if (score <= 5) return 'Neutral';
        return 'Positive';
    }
</script>

<svelte:head>
    <title>AI Summary & Analysis</title>
</svelte:head>

<div class="container">
    <div class="header">
        <h1>Public Consultation Analysis Dashboard</h1>
    </div>

    <div class="controls">
        <div class="control-group">
            <label for="draft-select">Select Draft:</label>
            <select id="draft-select" bind:value={selectedDraftId}>
                <option value="">-- Select a Draft --</option>
                {#each drafts as draft}
                    <option value={draft.draft_id}>{draft.title}</option>
                {/each}
            </select>
        </div>

        {#if selectedDraftId}
            <div class="control-group">
                <label for="section-select">Select Section:</label>
                <select id="section-select" bind:value={selectedSectionId}>
                    <option value="all">All Sections</option>
                    {#each sections as section}
                        <option value={section.section_id}>{section.section_title}</option>
                    {/each}
                </select>
            </div>
        {/if}
    </div>

    {#if selectedDraft}
        <div class="main-grid">
            <!-- Gauge Chart Card -->
            <div class="card gauge-card">
                <h3>Overall Sentiment Score</h3>
                <div class="gauge-wrapper">
                    <div class="gauge-canvas-container">
                        <canvas use:chart={gaugeChartConfig}></canvas>
                    </div>
                    <div class="gauge-labels">
                        <span class="gauge-label min-label">-100.00</span>
                        <span class="gauge-label max-label">100.00</span>
                    </div>
                    <div class="gauge-center">
                        <div class="gauge-text" style:color={getSentimentColor(sentimentScore)}>
                            {getSentimentText(sentimentScore)}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bar Chart Card -->
            <div class="card bar-chart-card">
                <h3>Sentiment Distribution</h3>
                <div class="bar-chart-wrapper">
                    <canvas use:chart={barChartConfig}></canvas>
                </div>
            </div>

            <!-- Summary Card -->
            <div class="card summary-card">
                <h2>Summary for: {displayTitle}</h2>
                <div class="summary-content">
                    <p>{displaySummary || 'No summary available.'}</p>
                </div>
            </div>

            <!-- Word Cloud Card -->
            <div class="card wordcloud-card">
                <h2>Top Keywords</h2>
                <div class="wordcloud-content">
                    {#if displayData?.word_cloud_image_path}
                        <img src="{API_BASE_URL}/{displayData.word_cloud_image_path}" alt="Word Cloud">
                    {:else}
                        <p class="no-data">No word cloud available.</p>
                    {/if}
                </div>
            </div>

            <!-- Comments Card -->
            <div class="card comments-card">
                <h2>Individual Comments ({commentsForDisplay.length})</h2>
                <div class="comments-container">
                    {#if commentsForDisplay.length === 0}
                        <p class="no-data">No comments available.</p>
                    {:else}
                        {#each commentsForDisplay as comment}
                            <details class="comment-item">
                                <summary>
                                    <span 
                                        class="sentiment-badge" 
                                        style:background-color={comment.sentiment_label === 'Positive' ? '#28a745' : comment.sentiment_label === 'Negative' ? '#dc3545' : '#6c757d'}
                                    >
                                        {comment.sentiment_label}
                                    </span>
                                    <span class="comment-preview">
                                        {comment.ai_summary?.substring(0, 100) || 'No summary'}...
                                    </span>
                                </summary>
                                <div class="comment-details">
                                    <div class="detail-section">
                                        <strong>Original Comment:</strong>
                                        <p>{comment.comment_text}</p>
                                    </div>
                                    {#if comment.section_title}
                                        <div class="detail-section">
                                            <strong>Section:</strong>
                                            <p>{comment.section_title}</p>
                                        </div>
                                    {/if}
                                </div>
                            </details>
                        {/each}
                    {/if}
                </div>
            </div>
        </div>
    {:else}
        <div class="placeholder">
            <p>Please select a draft to view analysis</p>
        </div>
    {/if}
</div>

<style>
    :global(body) {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: #f8f9fa;
    }

    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .header h1 {
        color: #212529;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
    }

    .controls {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .control-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .control-group label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #495057;
    }

    select {
        font-size: 1rem;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        border: 2px solid #dee2e6;
        background: white;
        cursor: pointer;
        min-width: 250px;
        transition: border-color 0.2s;
    }

    select:hover {
        border-color: #adb5bd;
    }

    select:focus {
        outline: none;
        border-color: #0d6efd;
    }

    .main-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        grid-template-rows: auto auto;
        gap: 1.5rem;
    }

    .card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .card h2,
    .card h3 {
        margin: 0;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #f1f3f5;
        background: #f8f9fa;
    }

    .gauge-card {
        grid-row: 1 / 2;
        grid-column: 1 / 2;
    }

    .bar-chart-card {
        grid-row: 1 / 2;
        grid-column: 2 / 3;
    }

    .summary-card {
        grid-row: 1 / 2;
        grid-column: 3 / 4;
    }

    .wordcloud-card {
        grid-row: 2 / 3;
        grid-column: 1 / 2;
    }

    .comments-card {
        grid-row: 2 / 3;
        grid-column: 2 / 4;
    }

    /* Gauge Chart Styles */
    .gauge-wrapper {
        padding: 2rem 1.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .gauge-canvas-container {
        position: relative;
        width: 100%;
        max-width: 280px;
        height: 140px;
    }

    .gauge-labels {
        position: relative;
        width: 100%;
        max-width: 280px;
        margin-top: 0.5rem;
    }

    .gauge-label {
        position: absolute;
        font-size: 0.75rem;
        color: #6c757d;
        font-weight: 500;
    }

    .min-label {
        left: 0;
    }

    .max-label {
        right: 0;
    }

    .gauge-center {
        text-align: center;
        margin-top: 1rem;
    }

    .gauge-score {
        font-size: 1.8rem;
        font-weight: 700;
        color: #212529;
        margin-bottom: 0.25rem;
    }

    .gauge-text {
        font-size: 1.5rem;
        font-weight: 600;
    }

    /* Bar Chart Styles */
    .bar-chart-wrapper {
        padding: 1.5rem;
        height: 280px;
    }

    /* Summary Card */
    .summary-content {
        padding: 1.5rem;
        line-height: 1.7;
        color: #495057;
        flex-grow: 1;
        overflow-y: auto;
        max-height: 250px;
    }

    /* Word Cloud Card */
    .wordcloud-content {
        padding: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-grow: 1;
    }

    .wordcloud-content img {
        max-width: 100%;
        max-height: 300px;
        object-fit: contain;
    }

    /* Comments Card */
    .comments-container {
        padding: 1rem 1.5rem 1.5rem;
        max-height: 500px;
        overflow-y: auto;
    }

    .comment-item {
        border-bottom: 1px solid #e9ecef;
        padding: 1rem 0;
    }

    .comment-item:last-child {
        border-bottom: none;
    }

    summary {
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        list-style: none;
    }

    summary::-webkit-details-marker {
        display: none;
    }

    .sentiment-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.3rem 0.6rem;
        border-radius: 12px;
        color: white;
        flex-shrink: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .comment-preview {
        flex-grow: 1;
        color: #495057;
    }

    .comment-details {
        margin-top: 1rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
    }

    .detail-section {
        margin-bottom: 1rem;
    }

    .detail-section:last-child {
        margin-bottom: 0;
    }

    .detail-section strong {
        display: block;
        color: #212529;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .detail-section p {
        margin: 0;
        color: #495057;
        line-height: 1.6;
    }

    .no-data {
        text-align: center;
        color: #6c757d;
        padding: 2rem;
        font-style: italic;
    }

    .placeholder {
        text-align: center;
        padding: 4rem 2rem;
        color: #6c757d;
        font-size: 1.2rem;
    }

    /* Scrollbar Styling */
    .comments-container::-webkit-scrollbar,
    .summary-content::-webkit-scrollbar {
        width: 8px;
    }

    .comments-container::-webkit-scrollbar-track,
    .summary-content::-webkit-scrollbar-track {
        background: #f1f3f5;
        border-radius: 4px;
    }

    .comments-container::-webkit-scrollbar-thumb,
    .summary-content::-webkit-scrollbar-thumb {
        background: #ced4da;
        border-radius: 4px;
    }

    .comments-container::-webkit-scrollbar-thumb:hover,
    .summary-content::-webkit-scrollbar-thumb:hover {
        background: #adb5bd;
    }

    /* Responsive Design */
    @media (max-width: 1200px) {
        .main-grid {
            grid-template-columns: 1fr 1fr;
        }

        .gauge-card {
            grid-column: 1 / 2;
        }

        .bar-chart-card {
            grid-column: 2 / 3;
        }

        .summary-card {
            grid-row: 2 / 3;
            grid-column: 1 / 3;
        }

        .wordcloud-card {
            grid-row: 3 / 4;
            grid-column: 1 / 2;
        }

        .comments-card {
            grid-row: 3 / 4;
            grid-column: 2 / 3;
        }
    }

    @media (max-width: 768px) {
        .main-grid {
            grid-template-columns: 1fr;
        }

        .gauge-card,
        .bar-chart-card,
        .summary-card,
        .wordcloud-card,
        .comments-card {
            grid-column: 1 / 2;
        }
    }
</style>