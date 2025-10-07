<script>
import { onMount } from 'svelte';
import { chart } from '$lib/chartAction.js';
import Map from '$lib/Map.svelte';
import Heatmap from '$lib/Heatmap.svelte';
import SentimentChart from '$lib/components/SentimentChart.svelte';
import NuanceCards from '$lib/NuanceCards.svelte';
import { filterStore, activeFilterCount } from '$lib/stores/filterStore.js';

// --- State Management ---
let drafts = [];
let allComments = [];
let sections = [];
let selectedDraftId = '';
let selectedSectionId = 'all';
let selectedState = 'All';
let selectedAction = 'All';
let selectedSentiment = 'All';
let isLoading = true;

// Metrics
let totalComments = 0;
let positiveCount = 0;
let neutralCount = 0;
let negativeCount = 0;
let sentimentScore = 0;

// Chart configs
let gaugeChartConfig = {};
let sentimentBarChartConfig = {};
let actionPieChartConfig = {};
let sectionPieChartConfig = {};

// --- API Configuration ---
const API_BASE_URL = 'http://127.0.0.1:5000';

// Subscribe to filter store
let currentFilters = {};
filterStore.subscribe(value => {
  currentFilters = value;
});

// --- Derived State with Cross-Filtering ---
$: commentsForDisplay = (() => {
  if (!selectedDraftId) return [];
  let filtered = allComments;
  
  // Apply cross-filter store filters
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
  
  // Apply dropdown filters (if not using cross-filter)
  if (selectedSectionId !== 'all' && !currentFilters.section) {
    filtered = filtered.filter(c => c.section_id == selectedSectionId);
  }
  if (selectedState !== 'All' && !currentFilters.state) {
    filtered = filtered.filter(c => c.state == selectedState);
  }
  if (selectedAction !== 'All' && !currentFilters.action) {
    filtered = filtered.filter(c => c.action_type == selectedAction);
  }
  if (selectedSentiment !== 'All' && !currentFilters.sentiment) {
    filtered = filtered.filter(c => c.sentiment_label == selectedSentiment);
  }
  
  return filtered;
})();

$: selectedDraft = drafts.find(d => d.draft_id == selectedDraftId) || null;
$: availableStates = ['All', ...new Set(allComments.map(c => c.state).filter(c => c))];

$: stateMapData = (() => {
  const data = {};
  commentsForDisplay.forEach(c => {
    if (!c.state) return;
    if (!data[c.state]) {
      data[c.state] = { positive: 0, neutral: 0, negative: 0, total: 0 };
    }
    data[c.state].total++;
    if (c.sentiment_label === 'Positive') data[c.state].positive++;
    if (c.sentiment_label === 'Neutral') data[c.state].neutral++;
    if (c.sentiment_label === 'Negative') data[c.state].negative++;
  });
  return data;
})();

// Calculate metrics and update charts
$: {
  if (!commentsForDisplay || commentsForDisplay.length === 0) {
    sentimentScore = 0;
    totalComments = 0;
    positiveCount = 0;
    negativeCount = 0;
    neutralCount = 0;
  } else {
    totalComments = commentsForDisplay.length;
    positiveCount = commentsForDisplay.filter(c => c.sentiment_label === 'Positive').length;
    neutralCount = commentsForDisplay.filter(c => c.sentiment_label === 'Neutral').length;
    negativeCount = commentsForDisplay.filter(c => c.sentiment_label === 'Negative').length;
    sentimentScore = (positiveCount / totalComments) * 100;
  }

  // Action type counts
  const actionCounts = {
    'Suggest removal': 0,
    'In Agreement': 0,
    'Suggest modification': 0
  };
  commentsForDisplay.forEach(c => {
    if (actionCounts.hasOwnProperty(c.action_type)) {
      actionCounts[c.action_type]++;
    }
  });

  // Section-wise comment counts
  const sectionCounts = {};
  commentsForDisplay.forEach(c => {
    if (!c.section_title) return;
    const shortTitle = c.section_title.length > 30
      ? c.section_title.substring(0, 30) + '...'
      : c.section_title;
    sectionCounts[shortTitle] = (sectionCounts[shortTitle] || 0) + 1;
  });

  const normalizedScore = sentimentScore + 100;
  const sentimentColor = getSentimentColor(sentimentScore);

  // Gauge Chart
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
    }
  };

  // Sentiment Bar Chart
  sentimentBarChartConfig = {
    type: 'bar',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [positiveCount, neutralCount, negativeCount],
        backgroundColor: ['#28a745', '#007bff', '#dc3545'],
        borderRadius: 6,
        barThickness: 50
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: (event, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          const sentiments = ['Positive', 'Neutral', 'Negative'];
          filterStore.setFilter('sentiment', sentiments[index]);
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#333',
          bodyColor: '#666',
          borderColor: '#ddd',
          borderWidth: 1,
          padding: 10
        },
        datalabels: {
          anchor: 'end',
          align: 'top',
          color: '#333',
          font: { weight: 'bold', size: 13 }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, color: '#666', font: { size: 11 } },
          grid: { color: '#e9ecef', drawBorder: false }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#333', font: { size: 12, weight: '600' } }
        }
      }
    }
  };

  // Action Type Pie Chart
  actionPieChartConfig = {
    type: 'pie',
    data: {
      labels: ['Suggest removal', 'In Agreement', 'Suggest modification'],
      datasets: [{
        data: [actionCounts['Suggest removal'], actionCounts['In Agreement'], actionCounts['Suggest modification']],
        backgroundColor: ['#dc3545', '#28a745', '#007bff']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: (event, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          const actions = ['Suggest removal', 'In Agreement', 'Suggest modification'];
          filterStore.setFilter('action', actions[index]);
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'right',
          labels: { usePointStyle: true, padding: 12, font: { size: 11 } }
        },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#333',
          bodyColor: '#666',
          borderColor: '#ddd',
          borderWidth: 1,
          padding: 10
        },
        datalabels: {
          color: '#fff',
          formatter: (value, context) => {
            let sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
            return sum > 0 ? ((value * 100 / sum).toFixed(1) + "%") : '';
          },
          font: { weight: 'bold', size: 13 }
        }
      }
    }
  };

  // Section Pie Chart
  const sectionLabels = Object.keys(sectionCounts);
  const sectionData = Object.values(sectionCounts);
  sectionPieChartConfig = {
    type: 'pie',
    data: {
      labels: sectionLabels,
      datasets: [{
        data: sectionData,
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
          '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: (event, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          const fullTitle = sections.find(s => 
            s.section_title.startsWith(sectionLabels[index].replace('...', ''))
          )?.section_title || sectionLabels[index];
          filterStore.setFilter('section', fullTitle);
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'right',
          labels: { usePointStyle: true, padding: 8, font: { size: 10 } }
        },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#333',
          bodyColor: '#666',
          borderColor: '#ddd',
          borderWidth: 1,
          padding: 10
        },
        datalabels: {
          color: '#fff',
          formatter: (value, context) => {
            let sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
            return sum > 0 ? ((value * 100 / sum).toFixed(1) + "%") : '';
          },
          font: { weight: 'bold', size: 11 }
        }
      }
    }
  };
}

onMount(async () => {
    isLoading = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/drafts`);
    drafts = await res.json();
  } catch (error) {
    console.error('Error fetching drafts:', error);
  }
  finally {
    isLoading = false; // End loading
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
  selectedState = 'All';
  selectedAction = 'All';
  selectedSentiment = 'All';
  filterStore.reset();
  
  try {
    const [commentsRes, sectionsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/comments/${selectedDraftId}`),
      fetch(`${API_BASE_URL}/api/sections/${selectedDraftId}`)
    ]);
    allComments = await commentsRes.json();
    sections = await sectionsRes.json();
    allComments = allComments.filter(comment => 
        sections.some(section => section.section_id === comment.section_id));
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

function getSentimentColor(score) {
  if (score < 40) return '#dc3545';
  if (score < 60) return '#ffc107';
  return '#28a745';
}

function getSentimentText(score) {
  if (score < 40) return 'Negative';
  if (score < 60) return 'Neutral';
  return 'Positive';
}
</script>

<svelte:head>
  <title>Overall Analysis Dashboard</title>
</svelte:head>

<div class="container">
  <!-- Filters Section -->
  <div class="controls">
    <div class="control-group">
      <label for="draft-select">Draft Selection</label>
      <select id="draft-select" bind:value={selectedDraftId}>
        <option value="">-- Select a Draft --</option>
        {#each drafts as draft}
          <option value={draft.draft_id}>{draft.title}</option>
        {/each}
      </select>
    </div>

    {#if selectedDraftId}
      <div class="control-group">
        <label for="section-select">Section</label>
        <select id="section-select" bind:value={selectedSectionId}>
          <option value="all">All Sections</option>
          {#each sections as section}
            <option value={section.section_id}>{section.section_title}</option>
          {/each}
        </select>
      </div>

      <div class="control-group">
        <label for="state-select">State</label>
        <select id="state-select" bind:value={selectedState}>
          {#each availableStates as state}
            <option value={state}>{state}</option>
          {/each}
        </select>
      </div>

      <div class="control-group">
        <label for="action-select">Action Type</label>
        <select id="action-select" bind:value={selectedAction}>
          <option value="All">All</option>
          <option value="Suggest removal">Suggest removal</option>
          <option value="In Agreement">In Agreement</option>
          <option value="Suggest modification">Suggest modification</option>
        </select>
      </div>

      <div class="control-group">
        <label for="sentiment-select">Sentiment</label>
        <select id="sentiment-select" bind:value={selectedSentiment}>
          <option value="All">All</option>
          <option value="Positive">Positive</option>
          <option value="Neutral">Neutral</option>
          <option value="Negative">Negative</option>
        </select>
      </div>
    {/if}
  </div>

  <!-- Active Filters Display -->
  {#if selectedDraftId && $activeFilterCount > 0}
    <div class="filter-badges">
      <span class="badge-label">Active Filters ({$activeFilterCount}):</span>
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
      <button class="clear-all-btn" on:click={() => filterStore.clearAllFilters()}>
        Clear All
      </button>
    </div>
  {/if}

  {#if selectedDraftId}
    <!-- Summary Cards -->
    <div class="comment-summary">
      <div class="comment-box total">
        <h3>Total Comments</h3>
        <p>{totalComments}</p>
      </div>
      <div class="comment-box positive">
        <h3>Positive Comments</h3>
        <p>{positiveCount}</p>
      </div>
      <div class="comment-box neutral">
        <h3>Neutral Comments</h3>
        <p>{neutralCount}</p>
      </div>
      <div class="comment-box negative">
        <h3>Negative Comments</h3>
        <p>{negativeCount}</p>
      </div>
      {#if selectedDraftId}
        <NuanceCards {commentsForDisplay} />
      {/if}
    </div>

    <!-- Dashboard Grid -->
    <div class="dashboard-grid">
      <!-- Gauge Chart -->
      <div class="card gauge-card clickable-chart">
        <h3>Overall Sentiment Distribution <span class="click-hint">Click to filter</span></h3>
        <SentimentChart {commentsForDisplay} />
      </div>

      <!-- Action Type Pie Chart -->
      <div class="card action-card clickable-chart">
        <h3>Comments by Action Type <span class="click-hint">Click to filter</span></h3>
        <div class="chart-wrapper">
          <canvas use:chart={actionPieChartConfig}></canvas>
        </div>
      </div>

      <!-- Sentiment Bar Chart -->
      <div class="card sentiment-card clickable-chart">
        <h3>Comments by Sentiment Label <span class="click-hint">Click to filter</span></h3>
        <div class="chart-wrapper">
          <canvas use:chart={sentimentBarChartConfig}></canvas>
        </div>
      </div>

      <!-- Section Heat Map -->
      <div class="card heatmap-card">
        <h3>Industry × Section Sentiment Heatmap</h3>
        <div class="heatmap-wrapper">
          <Heatmap {commentsForDisplay} on:cellClick={(e) => {
            filterStore.setFilter('industry', e.detail.industry);
            filterStore.setFilter('section', e.detail.section);
          }} />
        </div>
      </div>

      <!-- Geographic Map -->
      <div class="card map-card">
        <h3>Geographic Distribution</h3>
        <div class="map-container">
          <Map {stateMapData} {selectedDraftId} fetchFromApi={false} on:stateClick={(e) =>
            filterStore.setFilter('state', e.detail)} />
          <div class="map-legend">
            <div class="legend-item">
              <div class="legend-color" style="background: #28a745;"></div>
              <span>Positive</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #007bff;"></div>
              <span>Neutral</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #dc3545;"></div>
              <span>Negative</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pie Chart -->
      <div class="card section-card clickable-chart">
        <h3>Comments received per Section <span class="click-hint">Click to filter</span></h3>
        <div class="chart-wrapper">
          <canvas use:chart={sectionPieChartConfig}></canvas>
        </div>
      </div>
    </div>

    <!-- Draft Summary Section -->
    {#if selectedDraft}
      <div class="summary-section">
        <div class="card summary-card">
          <h3>Draft Summary</h3>
          <div class="summary-content">
            <div class="summary-text">
              <h4>{selectedDraft.title}</h4>
              <p>{selectedDraft.draft_ai_summary || 'No summary available for this draft.'}</p>
            </div>
            {#if selectedDraft.word_cloud_image_path}
              <div class="wordcloud-container">
                <img src="{API_BASE_URL}/{selectedDraft.word_cloud_image_path}" alt="Draft Word Cloud">
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    <!-- Section Summary (when specific section selected) -->
    {#if selectedSectionId !== 'all'}
      {@const selectedSection = sections.find(s => s.section_id == selectedSectionId)}
      {#if selectedSection}
        <div class="summary-content">
          <div class="summary-text">
            <h4>{selectedSection.section_title}</h4>
            <p><strong>Summary:</strong> {selectedSection.section_ai_summary || 'No summary available.'}</p>
            {#if selectedSection.section_ai_key_points}
              <p><strong>Key Points:</strong> {selectedSection.section_ai_key_points}</p>
            {/if}
          </div>
          {#if selectedSection.word_cloud_image_path}
            <div class="wordcloud-container">
              <img src="{API_BASE_URL}/{selectedSection.word_cloud_image_path}" alt="Section Word Cloud">
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  {:else}
    <div class="placeholder">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <h3>No Draft Selected</h3>
      <p>Please select a draft to view the overall analysis</p>
    </div>
  {/if}
</div>

<style>
:global(body) {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
}

.container {
  max-width: 1600px;
  margin: 0 auto;
  
}

.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
  flex: 1;
}

.control-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #495057;
}

select {
  font-size: 0.9rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  border: 2px solid #dee2e6;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

select:hover {
  border-color: #adb5bd;
}

select:focus {
  outline: none;
  border-color: #0d6efd;
}

.filter-badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
  padding: 0.75rem;
  background: #e7f3ff;
  border-radius: 8px;
  border-left: 4px solid #0d6efd;
}

.badge-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0d6efd;
}

.filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  background: #0d6efd;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-badge:hover {
  background: #0b5ed7;
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

.comment-summary {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.comment-box {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  text-align: center;
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  max-height: 85px;
}

.comment-box h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #495057;
  margin: 0;
}

.comment-box p {
  font-size: 1.2rem;
  font-weight: bold;
  color: #343a40;
  margin: 0;
}

.comment-box.total {
  border-bottom: 2px solid #6c757d;
}

.comment-box.positive {
  border-bottom: 2px solid #28a745;
}

.comment-box.neutral {
  border-bottom: 2px solid #007bff;
}

.comment-box.negative {
  border-bottom: 2px solid #dc3545;
}

.summary-section {
  margin-bottom: 2rem;
}

.summary-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 2rem;
}

.summary-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0.75rem;
}

.summary-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.summary-text {
  flex: 1;
  max-width: 700px;
}

.summary-text h4 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #2d3748;
}

.summary-text p {
  margin: 0 0 1rem 0;
  line-height: 1.7;
  color: #4a5568;
}

.wordcloud-container {
  flex-shrink: 0;
  width: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wordcloud-container img {
  max-width: 100%;
  max-height: 300px;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.clickable-chart {
  cursor: pointer;
}

.clickable-chart:hover {
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.2);
}

.card h3 {
  margin: 0;
  padding: 1.25rem;
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #f1f3f5;
  background: #fafafa;
  text-align: center;
}

.click-hint {
  font-size: 0.7rem;
  color: #0d6efd;
  font-weight: 500;
  font-style: italic;
}

.gauge-card {
  grid-column: span 1;
}

.action-card {
  grid-column: span 1;
}

.sentiment-card {
  grid-column: span 1;
}

.section-card {
  grid-column: span 2;
}

.map-card {
  grid-column: span 1;
  grid-row: span 2;
}

.heatmap-card {
  grid-column: span 2;
}

.chart-wrapper {
  padding: 1.5rem;
  height: 280px;
}

.map-container {
  padding: 1rem;
  height: 800px;
  display: flex;
  flex-direction: column;
}

.map-legend {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.legend-item span {
  font-size: 0.875rem;
  color: #495057;
  font-weight: 500;
}

.heatmap-wrapper {
  padding: 1rem;
  max-height: 600px;
  overflow: auto;
}

.placeholder {
  text-align: center;
  padding: 5rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.placeholder svg {
  color: #cbd5e0;
  margin-bottom: 1.5rem;
}

.placeholder h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
}

.placeholder p {
  margin: 0;
  color: #718096;
  font-size: 1rem;
}

@media (max-width: 1400px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .section-card,
  .heatmap-card {
    grid-column: span 2;
  }
  
  .map-card {
    grid-column: span 2;
    grid-row: span 1;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .gauge-card,
  .action-card,
  .sentiment-card,
  .section-card,
  .map-card,
  .heatmap-card {
    grid-column: span 1;
    grid-row: span 1;
  }
}
</style>