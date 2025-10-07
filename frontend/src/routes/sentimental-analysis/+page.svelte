<script>
    import { onMount } from 'svelte';
    import { chart } from '$lib/chartAction.js';
    import { filterStore, activeFilterCount } from '$lib/stores/filterStore.js';
    import Map from '$lib/Map.svelte';
    import Heatmap from '$lib/Heatmap.svelte';
    import NuanceCards from '$lib/NuanceCards.svelte';
    import ImpactfulComments from '$lib/ImpactfulComments.svelte';
    import SentimentChart from '$lib/components/SentimentChart.svelte';
  import { forceCenter, randomWeibull } from 'd3';
  
    
    let drafts = [];
    let allComments = [];
    let sections = [];
    let selectedDraftId = '';
    let selectedSectionId = 'all';
    let selectedState = 'All';
    let selectedAction = 'All';
    let selectedSentiment = 'All';
    
    let totalComments = 0;
    let positiveCount = 0;
    let neutralCount = 0;
    let negativeCount = 0;
    let sentimentScore = 0;

    let gaugeChartConfig = {};
    let sentimentBarChartConfig = {};
    let actionBarChartConfig = {};
    let stateChartConfig = {};
    let industryChartConfig = {};
    let sectionChartConfig = {};

    const API_BASE_URL = 'http://127.0.0.1:5000';

    // Subscribe to filter store
    let currentFilters = {};
    filterStore.subscribe(value => {
        currentFilters = value;
    });

    // Apply filters from store to commentsForDisplay
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
     // compute average scores across currently filtered selection (so SentimentChart can use them)
 $: avg_score_positive = commentsForDisplay && commentsForDisplay.length
     ? commentsForDisplay.reduce((sum, c) => sum + (c.score_positive || 0), 0) / commentsForDisplay.length
     : 0;

 $: avg_score_negative = commentsForDisplay && commentsForDisplay.length
     ? commentsForDisplay.reduce((sum, c) => sum + (c.score_negative || 0), 0) / commentsForDisplay.length
     : 0;

 $: avg_score_neutral = commentsForDisplay && commentsForDisplay.length
     ? commentsForDisplay.reduce((sum, c) => sum + (c.score_neutral || 0), 0) / commentsForDisplay.length
     : 0;


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

        const stateData = {};
        commentsForDisplay.forEach(c => {
            if (!c.state) return;
            if (!stateData[c.state]) {
                stateData[c.state] = { Positive: 0, Neutral: 0, Negative: 0 };
            }
            if (c.sentiment_label) {
                stateData[c.state][c.sentiment_label]++;
            }
        });

        const industryData = {};
        commentsForDisplay.forEach(c => {
            const industry = c.industry || 'Individual';
            if (!industryData[industry]) {
                industryData[industry] = { Positive: 0, Neutral: 0, Negative: 0 };
            }
            if (c.sentiment_label) {
                industryData[industry][c.sentiment_label]++;
            }
        });

        const sectionData = {};
        commentsForDisplay.forEach(c => {
            if (!c.section_title) return;
            const shortTitle = c.section_title.length > 30
                ? c.section_title.substring(0, 30) + '...'
                : c.section_title;
            if (!sectionData[shortTitle]) {
                sectionData[shortTitle] = { Positive: 0, Neutral: 0, Negative: 0 };
            }
            if (c.sentiment_label) {
                sectionData[shortTitle][c.sentiment_label]++;
            }
        });

        const normalizedScore = sentimentScore + 100;
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
            }
        };

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

        actionBarChartConfig = {
            type: 'pie',
            data: {
                labels: ['Suggest\nremoval', 'In Agreement', 'Suggest\nmodification'],
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
                        labels: {
                            usePointStyle: true,
                            padding: 12,
                            font: { size: 11 }
                        }
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

        const stateLabels = Object.keys(stateData);
        stateChartConfig = {
            type: 'bar',
            data: {
                labels: stateLabels,
                datasets: [
                    {
                        label: 'Negative',
                        data: stateLabels.map(s => stateData[s].Negative),
                        backgroundColor: '#dc3545'
                    },
                    {
                        label: 'Neutral',
                        data: stateLabels.map(s => stateData[s].Neutral),
                        backgroundColor: '#007bff'
                    },
                    {
                        label: 'Positive',
                        data: stateLabels.map(s => stateData[s].Positive),
                        backgroundColor: '#28a745'
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        filterStore.setFilter('state', stateLabels[index]);
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { usePointStyle: true, padding: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: '#fff',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 10 },
                        formatter: (value) => value > 0 ? value : ''
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { color: '#666', font: { size: 10 } }
                    },
                    y: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { color: '#333', font: { size: 11 } }
                    }
                }
            }
        };

        const industryLabels = Object.keys(industryData);
        industryChartConfig = {
            type: 'bar',
            data: {
                labels: industryLabels,
                datasets: [
                    {
                        label: 'Negative',
                        data: industryLabels.map(i => industryData[i].Negative),
                        backgroundColor: '#dc3545'
                    },
                    {
                        label: 'Neutral',
                        data: industryLabels.map(i => industryData[i].Neutral),
                        backgroundColor: '#007bff'
                    },
                    {
                        label: 'Positive',
                        data: industryLabels.map(i => industryData[i].Positive),
                        backgroundColor: '#28a745'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        filterStore.setFilter('industry', industryLabels[index]);
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { usePointStyle: true, padding: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: '#fff',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        color: '#333',
                        font: { weight: 'bold', size: 10 },
                        formatter: (value) => value > 0 ? value : ''
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#666', font: { size: 10 } },
                        grid: { color: '#e9ecef' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#333', font: { size: 10 } }
                    }
                }
            }
        };

        const sectionLabels = Object.keys(sectionData);
        sectionChartConfig = {
            type: 'bar',
            data: {
                labels: sectionLabels,
                datasets: [
                    {
                        label: 'Negative',
                        data: sectionLabels.map(s => sectionData[s].Negative),
                        backgroundColor: '#dc3545'
                    },
                    {
                        label: 'Neutral',
                        data: sectionLabels.map(s => sectionData[s].Neutral),
                        backgroundColor: '#007bff'
                    },
                    {
                        label: 'Positive',
                        data: sectionLabels.map(s => sectionData[s].Positive),
                        backgroundColor: '#28a745'
                    }
                ]
            },
            options: {
                indexAxis: 'y',
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
                        position: 'top',
                        labels: { usePointStyle: true, padding: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: '#fff',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'left',
                        color: 'white',
                        font: { weight: 'bold', size: 12 },
                        formatter: (value) => value > 0 ? value : ''
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#666', font: { size: 10 } },
                        grid: { color: '#e9ecef' },
                        stacked: true
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#333',
                            font: { size: 9 },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        stacked: true
                    }
                }
            }
        };
    }

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
        sections.some(section => section.section_id === comment.section_id)
    );
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
    <title>Public Consultation Analysis Dashboard</title>
</svelte:head>


<style>
    :global(body) {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #f5f5f5;
    }

    .container {
        height: 100vh;
        width:100%;
        margin: 0 auto;
        padding:1rem;
    }
/* Update these existing styles in your <style> block */
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


    .controls {
        display: flex;
        
        margin-bottom: 0;
        flex-wrap: nowrap;
        align-items: center;
        overflow-x: auto;
        margin-bottom:1rem;
    }

    .control-group {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        width: 250px;
        flex-shrink: 0;
    }

    .control-group label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #495057;
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
        /* margin-bottom: 1.5rem; */
        flex-wrap: wrap;
    }

    .comment-box {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
        text-align: center;
        padding:0.5rem 1rem;
        display:flex;
        justify-content:center;
        align-items:center;
        flex-direction:column;
        max-height:85px;
    }

    .comment-box h3 {
        font-size: 0.9rem;
        font-weight: 600;
        color: #495057;
        margin: 0;
        /* margin-bottom: 0.5rem; */
    }

    .comment-box p {
        font-size: 1.2rem;
        font-weight: bold;
        color: #343a40;
        margin: 0;
    }

    .comment-box.total {
        border-bottom: 3px solid #6c757d;
    }

    .comment-box.positive {
        border-bottom: 3px solid #28a745;
    }

    .comment-box.neutral {
        border-bottom: 3px solid #007bff;
    }

    .comment-box.negative {
        border-bottom: 3px solid #dc3545;
    }

    select {
        font-size: 0.9rem;
        padding: 0.5rem 0.9rem;
        border-radius: 6px;
        border: 2px solid #dee2e6;
        background: white;
        cursor: pointer;
        width: 100%;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }

    select:hover {
        border-color: #adb5bd;
    }

    select:focus {
        outline: none;
        border-color: #0d6efd;
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        grid-template-rows: auto auto auto auto auto;
        gap: 1rem;
    }

    .gauge-card {
        grid-column: 1 / 2;
        grid-row: 1;
    }

    .action-bar-card {
        grid-column: 2 / 3;
        grid-row: 1;
    }

    .sentiment-bar-card {
        grid-column: 3 / 4;
        grid-row: 3;
    }

    .map-card {
        grid-column: 3 / 4;
        grid-row: 1 / 3;
    }

    .industry-card {
        grid-column: 1 / 3;
        grid-row: 3;
    }

    .section-card {
        grid-column: 1 / 3;
        grid-row: 2;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .heatmap-card {
        grid-column: 1/ 4;
        grid-row: 4;
    }

    .impactful-card {
        grid-column: 1 / 4;
        grid-row: 5;
    }

    .impactful-wrapper {
        padding: 1.2rem;
    }

    .card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transition: box-shadow 0.3s;
    }

    .clickable-chart {
        cursor: pointer;
    }

    .clickable-chart:hover {
        box-shadow: 0 4px 12px rgba(13, 110, 253, 0.2);
    }

    .card h3 {
        margin: 0;
        padding: 1rem;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #f1f3f5;
        background: #fafafa;
    }

    .click-hint {
        font-size: 0.7rem;
        color: #0d6efd;
        font-weight: 500;
        font-style: italic;
    }

    .gauge-wrapper {
        padding: 1.5rem 1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .gauge-canvas-container {
        position: relative;
        width: 100%;
        max-width: 250px;
        height: 125px;
    }

    .gauge-labels {
        position: relative;
        width: 100%;
        max-width: 250px;
        margin-top: 0.3rem;
    }

    .gauge-label {
        position: absolute;
        font-size: 0.7rem;
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
        margin-top: 0.8rem;
    }

    .gauge-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .gauge-text {
        font-size: 1.1rem;
        font-weight: 600;
    }

    .chart-wrapper {
        padding: 1.2rem;
        height: 250px;
        width:80%;
    }

    .map-container {
        padding: 1.2rem;
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    

    .map-legend {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: auto;
        padding-top: 0.8rem;
        border-top: 1px solid #e9ecef;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid #fff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    .legend-item span {
        font-size: 0.8rem;
        color: #495057;
        font-weight: 500;
    }

    .placeholder {
        text-align: center;
        padding: 3rem 2rem;
        color: #6c757d;
        font-size: 1rem;
        padding-top: 5rem;
    }
</style>
<div class="container">
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
     {/if}
    

    {#if selectedDraft}
        <div class="dashboard-grid">
            <div class="card gauge-card clickable-chart">
  <h3>Overall Sentiment Distribution <span class="click-hint">Click to filter</span></h3>
  <SentimentChart {commentsForDisplay} />
</div>



            <div class="card action-bar-card clickable-chart">
                <h3>No of Comments received in each Action <span class="click-hint">Click to filter</span></h3>
                <div class="chart-wrapper">
                    <canvas use:chart={actionBarChartConfig}></canvas>
                </div>
            </div>

            <div class="card sentiment-bar-card clickable-chart">
                <h3>No of Comments received in each Sentimental Label <span class="click-hint">Click to filter</span></h3>
                <div class="chart-wrapper">
                    <canvas use:chart={sentimentBarChartConfig}></canvas>
                </div>
            </div>

            <div class="card section-card clickable-chart">
                <h3>Section Wise Sentiment Analysis of Comments <span class="click-hint">Click to filter</span></h3>
                <div class="chart-wrapper">
                    <canvas use:chart={sectionChartConfig}></canvas>
                </div>
            </div>

            <div class="card map-card">
                <h3>Geographic Distribution of Sentiment</h3>
                <div class="map-container">
                    <Map {stateMapData} {selectedDraftId} fetchFromApi={false} on:stateClick={(e) => filterStore.setFilter('state', e.detail)} />
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

            <div class="card industry-card clickable-chart">
                <h3>No of comments Received from Stake Holders with Sentiment <span class="click-hint">Click to filter</span></h3>
                <div class="chart-wrapper">
                    <canvas use:chart={industryChartConfig}></canvas>
                </div>
            </div>
             <div class="card heatmap-card">
            <h3>Industry × Section Sentiment Heatmap</h3>
            <div class="chart-wrapper" style="height: auto;">
                <Heatmap {commentsForDisplay} on:cellClick={(e) => {
                    filterStore.setFilter('industry', e.detail.industry);
                    filterStore.setFilter('section', e.detail.section);
                }} />
            </div>
        </div>

        <div class="card impactful-card">
            <h3>Most Impactful Comments</h3>
            <div class="impactful-wrapper">
                <ImpactfulComments {commentsForDisplay} />
            </div>
        </div>
        </div>
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