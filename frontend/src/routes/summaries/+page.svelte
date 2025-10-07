<script>
import { onMount } from 'svelte';
import { filterStore, activeFilterCount } from '$lib/stores/filterStore.js';

// --- State Management ---
let drafts = [];
let allComments = [];
let sections = [];
let selectedDraftId = '';

// INDEPENDENT STATE: Draft-level sentiment filter
let draftSentimentView = 'all'; // 'all', 'positive', 'neutral', 'negative'

// INDEPENDENT STATE: Section selection (for viewing specific section)
let selectedSectionId = 'all';

// INDEPENDENT STATE: Section-level sentiment filter
let sectionSentimentView = 'all'; // 'all', 'positive', 'neutral', 'negative'

// Filter states for INDIVIDUAL COMMENTS ONLY
let filterState = 'All';
let filterAction = 'All';
let filterSentiment = 'All';

// UI State
let showComments = false;

// Subscribe to filter store (only affects individual comments)
let currentFilters = {};
filterStore.subscribe(value => {
  currentFilters = value;
});

// --- Derived State ---
$: selectedDraft = drafts.find(d => d.draft_id == selectedDraftId) || null;
$: selectedSection = sections.find(s => s.section_id == selectedSectionId) || null;

// Available filter options for individual comments
$: availableStates = ['All', ...new Set(allComments.map(c => c.state).filter(c => c))];
$: availableActions = ['All', ...new Set(allComments.map(c => c.action_type).filter(c => c))];
$: availableSentiments = ['All', ...new Set(allComments.map(c => c.sentiment_label).filter(c => c))];

// Filtered comments - ONLY affects individual comments section
$: filteredComments = (() => {
  if (!selectedDraftId) return [];
  let filtered = allComments;
  
  // Cross-filter store filters (only for individual comments)
  if (currentFilters.section) {
    const section = sections.find(s => s.section_title === currentFilters.section);
    if (section) {
      filtered = filtered.filter(c => c.section_id == section.section_id);
    }
  }
  if (currentFilters.state) {
    filtered = filtered.filter(c => c.state == currentFilters.state);
  }
  if (currentFilters.action) {
    filtered = filtered.filter(c => c.action_type == currentFilters.action);
  }
  if (currentFilters.sentiment) {
    filtered = filtered.filter(c => c.sentiment_label == currentFilters.sentiment);
  }
  if (currentFilters.industry) {
    filtered = filtered.filter(c => {
      const ind = c.industry || 'Individual';
      return ind === currentFilters.industry;
    });
  }
  
  // Dropdown filters (only for individual comments)
  if (filterState !== 'All' && !currentFilters.state) {
    filtered = filtered.filter(c => c.state == filterState);
  }
  if (filterAction !== 'All' && !currentFilters.action) {
    filtered = filtered.filter(c => c.action_type == filterAction);
  }
  if (filterSentiment !== 'All' && !currentFilters.sentiment) {
    filtered = filtered.filter(c => c.sentiment_label == filterSentiment);
  }
  
  return filtered;
})();

// Reset filters when draft changes
$: if (selectedDraftId) {
  resetAllFilters();
}

function resetAllFilters() {
  // Reset individual comment filters
  filterState = 'All';
  filterAction = 'All';
  filterSentiment = 'All';
  filterStore.reset();
  
  // Reset draft sentiment view
  draftSentimentView = 'all';
  
  // Reset section selection and sentiment view
  selectedSectionId = 'all';
  sectionSentimentView = 'all';
}

function resetCommentFilters() {
  filterState = 'All';
  filterAction = 'All';
  filterSentiment = 'All';
  filterStore.reset();
}

const API_BASE_URL = 'http://127.0.0.1:5000';

onMount(async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/drafts`);
    drafts = await res.json();
  } catch (error) {
    console.error('Error fetching drafts:', error);
  }
});

// Handle draft change
$: if (selectedDraftId) handleDraftChange();

async function handleDraftChange() {
  if (!selectedDraftId) {
    sections = [];
    allComments = [];
    showComments = true;
    return;
  }

  showComments = true;

  try {
    const [sectionsRes, commentsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/sections/${selectedDraftId}`),
      fetch(`${API_BASE_URL}/api/comments/${selectedDraftId}`)
    ]);
    sections = await sectionsRes.json();
    allComments = await commentsRes.json();
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

function getSentimentColor(label) {
  if (label === 'Positive') return '#28a745';
  if (label === 'Negative') return '#dc3545';
  return '#6c757d';
}
</script>

<div class="container">
  <!-- Step 1: Draft Selection -->
  <section class="section draft-selection">
    <div class="draft-selector">
      <select bind:value={selectedDraftId} class="primary-select">
        <option value="">-- Draft Selection --</option>
        {#each drafts as draft}
          <option value={draft.draft_id}>{draft.title}</option>
        {/each}
      </select>
    </div>
  </section>

  {#if selectedDraft}
    <!-- Step 2: DRAFT Overview Section with INDEPENDENT Sentiment Tabs -->
    <section class="section overview-section">
      <div class="section-header">
        <h2>Draft Overview & Sentiment Analysis</h2>
      </div>

      <!-- DRAFT Sentiment View Tabs - INDEPENDENT -->
      <div class="sentiment-tabs">
        <button 
          class="tab-btn" 
          class:active={draftSentimentView === 'all'}
          on:click={() => draftSentimentView = 'all'}
        >
          All Comments
        </button>
        <button 
          class="tab-btn positive-tab" 
          class:active={draftSentimentView === 'positive'}
          on:click={() => draftSentimentView = 'positive'}
        >
          Positive
        </button>
        <button 
          class="tab-btn neutral-tab" 
          class:active={draftSentimentView === 'neutral'}
          on:click={() => draftSentimentView = 'neutral'}
        >
          Neutral
        </button>
        <button 
          class="tab-btn negative-tab" 
          class:active={draftSentimentView === 'negative'}
          on:click={() => draftSentimentView = 'negative'}
        >
          Negative
        </button>
      </div>

      <div class="overview-grid">
        <!-- DRAFT Word Cloud - Controlled by draftSentimentView ONLY -->
        <div class="card wordcloud-card">
          <div class="card-header">
            <h3>
              {#if draftSentimentView === 'all'}
                Draft Word Cloud (All Comments)
              {:else if draftSentimentView === 'positive'}
                Positive Sentiment Word Cloud
              {:else if draftSentimentView === 'neutral'}
                Neutral Sentiment Word Cloud
              {:else}
                Negative Sentiment Word Cloud
              {/if}
            </h3>
            <p class="card-subtitle">Most frequently mentioned terms</p>
          </div>
          <div class="card-body">
            {#if draftSentimentView === 'all' && selectedDraft.word_cloud_image_path}
              <img src="{API_BASE_URL}/{selectedDraft.word_cloud_image_path}" alt="All Comments Word Cloud">
            {:else if draftSentimentView === 'positive' && selectedDraft.wordcloud_positive_path}
              <img src="{API_BASE_URL}/{selectedDraft.wordcloud_positive_path}" alt="Positive Word Cloud">
            {:else if draftSentimentView === 'neutral' && selectedDraft.wordcloud_neutral_path}
              <img src="{API_BASE_URL}/{selectedDraft.wordcloud_neutral_path}" alt="Neutral Word Cloud">
            {:else if draftSentimentView === 'negative' && selectedDraft.wordcloud_negative_path}
              <img src="{API_BASE_URL}/{selectedDraft.wordcloud_negative_path}" alt="Negative Word Cloud">
            {:else}
              <p class="empty-state">No word cloud available for this sentiment category</p>
            {/if}
          </div>
        </div>

        <!-- DRAFT Summary - Controlled by draftSentimentView ONLY -->
        <div class="card summary-card">
          <div class="card-header">
            <h3>
              {#if draftSentimentView === 'all'}
                Summary of All Comments
              {:else if draftSentimentView === 'positive'}
                Positive Comments Summary
              {:else if draftSentimentView === 'neutral'}
                Neutral Comments Summary
              {:else}
                Negative Comments Summary
              {/if}
            </h3>
            <p class="card-subtitle">AI-generated overview of feedback</p>
          </div>
          <div class="card-body">
            <div class="summary-text">
              {#if draftSentimentView === 'all'}
                {selectedDraft.draft_ai_summary || 'No summary available for this draft.'}
              {:else if draftSentimentView === 'positive'}
                {selectedDraft.summary_positive || 'No positive sentiment summary available.'}
              {:else if draftSentimentView === 'neutral'}
                {selectedDraft.summary_neutral || 'No neutral sentiment summary available.'}
              {:else}
                {selectedDraft.summary_negative || 'No negative sentiment summary available.'}
              {/if}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Step 3: SECTION Summaries with INDEPENDENT Controls -->
    {#if sections.length > 0}
      <section class="section sections-section">
        <div class="section-header">
          <h2>Section Analysis</h2>
          <div class="section-controls">
            <label>
              <span class="label-text">Select Section:</span>
              <select bind:value={selectedSectionId} class="inline-select">
                <option value="all">All Sections (Overview)</option>
                {#each sections as section}
                  <option value={section.section_id}>{section.section_title}</option>
                {/each}
              </select>
            </label>
          </div>
        </div>

        {#if selectedSectionId !== 'all'}
          <!-- SECTION Sentiment Tabs - INDEPENDENT from Draft tabs -->
          <div class="sentiment-tabs">
            <button 
              class="tab-btn" 
              class:active={sectionSentimentView === 'all'}
              on:click={() => sectionSentimentView = 'all'}
            >
              All Comments
            </button>
            <button 
              class="tab-btn positive-tab" 
              class:active={sectionSentimentView === 'positive'}
              on:click={() => sectionSentimentView = 'positive'}
            >
              Positive
            </button>
            <button 
              class="tab-btn neutral-tab" 
              class:active={sectionSentimentView === 'neutral'}
              on:click={() => sectionSentimentView = 'neutral'}
            >
              Neutral
            </button>
            <button 
              class="tab-btn negative-tab" 
              class:active={sectionSentimentView === 'negative'}
              on:click={() => sectionSentimentView = 'negative'}
            >
              Negative
            </button>
          </div>

          <!-- Side-by-side layout for SELECTED section -->
          <div class="section-detail-grid">
            <!-- SECTION Word Cloud - Controlled by sectionSentimentView ONLY -->
            <div class="card section-wordcloud-card">
              <div class="card-header">
                <h3>
                  {#if sectionSentimentView === 'all'}
                    Section Word Cloud (All)
                  {:else if sectionSentimentView === 'positive'}
                    Positive Sentiment
                  {:else if sectionSentimentView === 'neutral'}
                    Neutral Sentiment
                  {:else}
                    Negative Sentiment
                  {/if}
                </h3>
                <p class="card-subtitle">Key terms in this section</p>
              </div>
              <div class="card-body wordcloud-body">
                {#if sectionSentimentView === 'all' && selectedSection?.word_cloud_image_path}
                  <img src="{API_BASE_URL}/{selectedSection.word_cloud_image_path}" alt="Section Word Cloud">
                {:else if sectionSentimentView === 'positive' && selectedSection?.wordcloud_positive_path}
                  <img src="{API_BASE_URL}/{selectedSection.wordcloud_positive_path}" alt="Positive Word Cloud">
                {:else if sectionSentimentView === 'neutral' && selectedSection?.wordcloud_neutral_path}
                  <img src="{API_BASE_URL}/{selectedSection.wordcloud_neutral_path}" alt="Neutral Word Cloud">
                {:else if sectionSentimentView === 'negative' && selectedSection?.wordcloud_negative_path}
                  <img src="{API_BASE_URL}/{selectedSection.wordcloud_negative_path}" alt="Negative Word Cloud">
                {:else}
                  <p class="empty-state">No word cloud available for this sentiment</p>
                {/if}
              </div>
            </div>

            <!-- SECTION Summary - Controlled by sectionSentimentView ONLY -->
            <div class="card section-card">
              <div class="card-header">
                <h3>{selectedSection?.section_title}</h3>
              </div>
              <div class="card-body">
                <div class="section-content">
                  <div class="summary-block">
                    <strong>
                      {#if sectionSentimentView === 'all'}
                        Summary (All Comments)
                      {:else if sectionSentimentView === 'positive'}
                        Positive Sentiment Summary
                      {:else if sectionSentimentView === 'neutral'}
                        Neutral Sentiment Summary
                      {:else}
                        Negative Sentiment Summary
                      {/if}
                    </strong>
                    <p>
                      {#if sectionSentimentView === 'all'}
                        {selectedSection?.section_ai_summary || 'No summary available.'}
                      {:else if sectionSentimentView === 'positive'}
                        {selectedSection?.summary_positive || 'No positive sentiment summary available.'}
                      {:else if sectionSentimentView === 'neutral'}
                        {selectedSection?.summary_neutral || 'No neutral sentiment summary available.'}
                      {:else}
                        {selectedSection?.summary_negative || 'No negative sentiment summary available.'}
                      {/if}
                    </p>
                  </div>
                  {#if sectionSentimentView === 'all' && selectedSection?.section_ai_key_points}
                    <div class="keypoints-block">
                      <strong>Key Points:</strong>
                      <p>{selectedSection.section_ai_key_points}</p>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        {:else}
          <!-- Grid layout for ALL sections overview -->
          <div class="sections-grid">
            {#each sections as section}
              <div class="card section-card">
                <div class="card-header">
                  <h3>{section.section_title}</h3>
                </div>
                <div class="card-body">
                  <div class="section-content">
                    <div class="summary-block">
                      <strong>Summary:</strong>
                      <p>{section.section_ai_summary || 'No summary available.'}</p>
                    </div>
                    {#if section.section_ai_key_points}
                      <div class="keypoints-block">
                        <strong>Key Points:</strong>
                        <p>{section.section_ai_key_points}</p>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </section>
    {/if}

    <!-- Step 4: INDIVIDUAL COMMENTS Section - INDEPENDENT Filtering -->
    <section class="section comments-section">
      <div class="section-header">
        <h2>Individual Comments</h2>
      </div>

      <!-- Active Filters Display - ONLY for individual comments -->
      {#if $activeFilterCount > 0}
        <div class="filter-badges">
          <span class="badge-label">Active Comment Filters ({$activeFilterCount}):</span>
          {#if currentFilters.section}
            <button class="filter-badge" on:click={() => filterStore.clearFilter('section')}>
              Section: {currentFilters.section} ✕
            </button>
          {/if}
          {#if currentFilters.state}
            <button class="filter-badge" on:click={() => filterStore.clearFilter('state')}>
              State: {currentFilters.state} ✕
            </button>
          {/if}
          {#if currentFilters.action}
            <button class="filter-badge" on:click={() => filterStore.clearFilter('action')}>
              Action: {currentFilters.action} ✕
            </button>
          {/if}
          {#if currentFilters.sentiment}
            <button class="filter-badge" on:click={() => filterStore.clearFilter('sentiment')}>
              Sentiment: {currentFilters.sentiment} ✕
            </button>
          {/if}
          {#if currentFilters.industry}
            <button class="filter-badge" on:click={() => filterStore.clearFilter('industry')}>
              Industry: {currentFilters.industry} ✕
            </button>
          {/if}
          <button class="clear-all-btn" on:click={resetCommentFilters}>
            Clear All
          </button>
        </div>
      {/if}

      {#if showComments}
        <div class="filters-panel">
          <div class="filters-header">
            <span class="filters-label">Filter Individual Comments:</span>
          </div>
          <div class="filters-grid">
            <label class="filter-group">
              <span>State</span>
              <select bind:value={filterState}>
                {#each availableStates as state}
                  <option value={state}>{state}</option>
                {/each}
              </select>
            </label>
            <label class="filter-group">
              <span>Action Type</span>
              <select bind:value={filterAction}>
                {#each availableActions as action}
                  <option value={action}>{action}</option>
                {/each}
              </select>
            </label>
            <label class="filter-group">
              <span>Sentiment</span>
              <select bind:value={filterSentiment}>
                {#each availableSentiments as sentiment}
                  <option value={sentiment}>{sentiment}</option>
                {/each}
              </select>
            </label>
          </div>
        </div>

        <div class="card comments-card">
          <div class="comments-list">
            {#if filteredComments.length === 0}
              <div class="empty-state">
                <p>No comments match the selected filters.</p>
                <button class="link-btn" on:click={resetCommentFilters}>Clear all filters</button>
              </div>
            {:else}
              {#each filteredComments as comment, i}
                <div class="comment-item">
                  <div class="comment-header">
                    <span class="comment-number">#{i + 1}</span>
                    <div class="comment-badges">
                      <span
                        class="badge sentiment-badge"
                        style:background-color={getSentimentColor(comment.sentiment_label)}
                      >
                        {comment.sentiment_label || 'N/A'}
                      </span>
                      <span class="badge action-badge">
                        {comment.action_type}
                      </span>
                    </div>
                  </div>

                  <div class="comment-content-grid">
                    <!-- Original Comment -->
                    <div class="comment-block original-comment">
                      <div class="block-header">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M2.5 3A1.5 1.5 0 0 0 1 4.5v.793c.026.009.051.02.076.032L7.674 8.51c.206.1.446.1.652 0l6.598-3.185A.755.755 0 0 1 15 5.293V4.5A1.5 1.5 0 0 0 13.5 3h-11Z"/>
                          <path d="M15 6.954 8.978 9.86a2.25 2.25 0 0 1-1.956 0L1 6.954V11.5A1.5 1.5 0 0 0 2.5 13h11a1.5 1.5 0 0 0 1.5-1.5V6.954Z"/>
                        </svg>
                        Original Comment
                      </div>
                      <p class="comment-text">{comment.comment_text || 'No comment text available'}</p>
                    </div>

                    <!-- AI Summary -->
                    <div class="comment-block ai-summary">
                      <div class="block-header">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm.93 4.588l-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 4.588zM9 3.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                        </svg>
                        AI Summary
                      </div>
                      <p class="comment-text">{comment.ai_summary || 'No AI summary available'}</p>
                    </div>
                  </div>

                  <!-- Metadata -->
                  <div class="comment-metadata">
                    {#if comment.section_title}
                      <span class="meta-item">
                        <span class="meta-label">Section:</span>
                        <span class="meta-value">{comment.section_title}</span>
                      </span>
                    {/if}
                    {#if comment.state}
                      <span class="meta-item">
                        <span class="meta-label">State:</span>
                        <span class="meta-value">{comment.state}</span>
                      </span>
                    {/if}
                    {#if comment.industry}
                      <span class="meta-item">
                        <span class="meta-label">Industry:</span>
                        <span class="meta-value">{comment.industry}</span>
                      </span>
                    {/if}
                  </div>
                </div>
              {/each}
            {/if}
          </div>
        </div>
      {/if}
    </section>
  {:else}
    <div class="empty-state-large">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
      <h3>No Draft Selected</h3>
      <p>Select a draft from the dropdown above to view its analysis and feedback</p>
    </div>
  {/if}
</div>

<style>
:global(body) {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #1a202c;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

/* Filter Badges */
.filter-badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
  padding: 0.75rem;
  background: #fff3cd;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.badge-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #856404;
}

.filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  background: #ffc107;
  color: #000;
  border: none;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-badge:hover {
  background: #e0a800;
  transform: scale(1.05);
}

.clear-all-btn {
  padding: 0.4rem 0.9rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: auto;
}

.clear-all-btn:hover {
  background: #bb2d3b;
  transform: scale(1.05);
}

/* Sentiment Tabs */
.sentiment-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: 2px solid transparent;
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.tab-btn:hover {
  background: #e9ecef;
}

.tab-btn.active {
  background: #0d6efd;
  color: white;
  border-color: #0d6efd;
}

.positive-tab.active {
  background: #28a745;
  border-color: #28a745;
}

.neutral-tab.active {
  background: #6c757d;
  border-color: #6c757d;
}

.negative-tab.active {
  background: #dc3545;
  border-color: #dc3545;
}

/* Sections */
.section {
  margin-bottom: 2.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
  gap: 10px;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2d3748;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.label-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4a5568;
  margin-right: 0.5rem;
}

/* Draft Selection */
.draft-selector {
  display: flex;
  justify-content: center;
}

.primary-select {
  font-size: 1.1rem;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  border: 2px solid #cbd5e0;
  background: white;
  cursor: pointer;
  min-width: 500px;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.primary-select:hover {
  border-color: #4299e1;
}

.primary-select:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.inline-select {
  font-size: 0.95rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #cbd5e0;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.inline-select:hover {
  border-color: #a0aec0;
}

.inline-select:focus {
  outline: none;
  border-color: #3182ce;
}

/* Cards */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2d3748;
}

.card-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: #718096;
}

.card-body {
  padding: 1.5rem;
}

/* Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1.5rem;
}

.wordcloud-card .card-body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.wordcloud-card img {
  max-width: 100%;
  max-height: 350px;
  object-fit: contain;
}

.summary-text {
  line-height: 1.8;
  color: #4a5568;
  font-size: 1rem;
}

/* Sections Grid */
.sections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

/* Section Detail Grid */
.section-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.section-wordcloud-card .card-body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.section-wordcloud-card img {
  max-width: 100%;
  max-height: 450px;
  object-fit: contain;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.summary-block,
.keypoints-block {
  padding: 0;
}

.summary-block strong,
.keypoints-block strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #2d3748;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-block p,
.keypoints-block p {
  margin: 0;
  color: #4a5568;
  line-height: 1.6;
}

.keypoints-block {
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

/* Filters Panel */
.filters-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.filters-header {
  margin-bottom: 1rem;
}

.filters-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2d3748;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group span {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4a5568;
}

.filter-group select {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5e0;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-group select:hover {
  border-color: #a0aec0;
}

.filter-group select:focus {
  outline: none;
  border-color: #3182ce;
}

/* Comments */
.comments-list {
  padding: 1rem;
}

.comment-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  background: white;
}

.comment-item:last-child {
  margin-bottom: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

.comment-number {
  font-weight: 700;
  color: #2d3748;
  font-size: 1.1rem;
}

.comment-badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sentiment-badge {
  color: white;
}

.action-badge {
  background: #edf2f7;
  color: #4a5568;
}

.comment-content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.comment-block {
  padding: 1rem;
  border-radius: 6px;
  background: #f7fafc;
}

.original-comment {
  border-left: 3px solid #718096;
}

.ai-summary {
  border-left: 3px solid #4299e1;
}

.block-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #2d3748;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.block-header svg {
  flex-shrink: 0;
}

.original-comment .block-header svg {
  color: #718096;
}

.ai-summary .block-header svg {
  color: #4299e1;
}

.comment-text {
  margin: 0;
  color: #4a5568;
  line-height: 1.7;
  font-size: 0.95rem;
}

.comment-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.meta-value {
  font-size: 0.875rem;
  color: #2d3748;
  font-weight: 600;
}

.link-btn {
  background: none;
  border: none;
  color: #3182ce;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  font-size: 0.95rem;
}

.link-btn:hover {
  color: #2c5aa0;
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #718096;
}

.empty-state-large {
  text-align: center;
  padding: 5rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.empty-state-large svg {
  color: #cbd5e0;
  margin-bottom: 1.5rem;
}

.empty-state-large h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
}

.empty-state-large p {
  margin: 0;
  color: #718096;
  font-size: 1rem;
}

/* Responsive */
@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
  
  .section-detail-grid {
    grid-template-columns: 1fr;
  }
  
  .sections-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 968px) {
  .comment-content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }
  
  .primary-select {
    min-width: 100%;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
  }
  
  .sentiment-tabs {
    flex-direction: column;
  }
}
</style>