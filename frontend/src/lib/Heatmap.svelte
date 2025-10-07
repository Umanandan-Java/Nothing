<script>
    import { createEventDispatcher } from 'svelte';
    
    const dispatch = createEventDispatcher();
    
    export let commentsForDisplay = [];
    
    let heatmapData = [];
    let industries = [];
    let sections = [];
    let maxSectionLength = 30;
    
    $: {
        const dataMap = {};
        
        commentsForDisplay.forEach(c => {
            if (!c.section_title) return;
            
            const industry = c.industry || 'Individual';
            const section = c.section_title.length > maxSectionLength 
                ? c.section_title.substring(0, maxSectionLength) + '...' 
                : c.section_title;
            
            if (!dataMap[industry]) {
                dataMap[industry] = {};
            }
            if (!dataMap[industry][section]) {
                dataMap[industry][section] = { sum: 0, count: 0 };
            }
            
            let score = 0;
            if (c.sentiment_label === 'Positive') score = 1;
            if (c.sentiment_label === 'Neutral') score = 0;
            if (c.sentiment_label === 'Negative') score = -1;
            
            dataMap[industry][section].sum += score;
            dataMap[industry][section].count++;
        });
        
        industries = Object.keys(dataMap).sort((a, b) => {
            if (a === 'Individual') return -1;
            if (b === 'Individual') return 1;
            return a.localeCompare(b);
        });
        
        sections = [...new Set(
            industries.flatMap(ind => Object.keys(dataMap[ind]))
        )].sort();
        
        heatmapData = industries.map(ind => 
            sections.map(sec => {
                const data = dataMap[ind]?.[sec];
                if (data) {
                    return data.sum / data.count;
                }
                return null;
            })
        );
    }
    
    function getColor(value) {
        if (value === null) return '#e9ecef';
        if (value > 0.5) return '#28a745';
        if (value > 0.1) return '#90ee90';
        if (value >= -0.1) return '#007bff';
        if (value > -0.5) return '#ffb3b3';
        return '#dc3545';
    }
    
    function getSentimentText(value) {
        if (value === null) return 'No data';
        if (value > 0.3) return 'Positive';
        if (value < -0.3) return 'Negative';
        return 'Neutral';
    }
    
    function handleCellClick(industry, section) {
        dispatch('cellClick', { industry, section });
    }
</script>

<div class="heatmap-container">
    {#if industries.length === 0}
        <p class="no-data">No data available for heatmap</p>
    {:else}
        <div class="heatmap-wrapper">
            <div class="heatmap-scroll">
                <table class="heatmap-table">
                    <thead>
                        <tr>
                            <th class="corner-cell">Industry / Section</th>
                            {#each sections as section}
                                <th class="section-header" title={section}>
                                    <div class="header-text">{section}</div>
                                </th>
                            {/each}
                        </tr>
                    </thead>
                    <tbody>
                        {#each industries as industry, i}
                            <tr>
                                <th class="industry-header">{industry}</th>
                                {#each heatmapData[i] as value, j}
                                    <td 
                                        class="heatmap-cell"
                                        class:clickable={value !== null}
                                        style:background-color={getColor(value)}
                                        title="{industry} × {sections[j]}&#10;{getSentimentText(value)}&#10;Score: {value !== null ? value.toFixed(2) : 'N/A'}&#10;{value !== null ? 'Click to filter' : ''}"
                                        on:click={() => value !== null && handleCellClick(industry, sections[j])}
                                    >
                                        {#if value !== null}
                                            <span class="cell-value">{value.toFixed(2)}</span>
                                        {:else}
                                            <span class="cell-empty">—</span>
                                        {/if}
                                    </td>
                                {/each}
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="legend">
            <span class="legend-title">Sentiment Scale:</span>
            <div class="legend-item">
                <div class="legend-color" style="background: #28a745;"></div>
                <span>Strong Positive (&gt;0.5)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #90ee90;"></div>
                <span>Positive (0.1 to 0.5)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #007bff;"></div>
                <span>Neutral (-0.1 to 0.1)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffb3b3;"></div>
                <span>Negative (-0.5 to -0.1)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #dc3545;"></div>
                <span>Strong Negative (&lt;-0.5)</span>
            </div>
            <div class="legend-note">
                <em>💡 Click on any cell to filter by industry and section</em>
            </div>
        </div>
    {/if}
</div>

<style>
    .heatmap-container {
        height: 100%;
        display: flex;
        flex-direction: column;
        padding: 1rem;
        width: 100%;
    }
    
    .heatmap-wrapper {
        flex: 1;
        overflow: auto;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        background: white;
        width: 100%;
    }
    
    .heatmap-scroll {
        overflow: auto;
        max-height: 100%;
        width:100%;
    }
    
    .heatmap-table {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        font-size: 0.85rem;
    }
    
    .corner-cell {
        background: #f8f9fa;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #dee2e6;
        border-right: 2px solid #dee2e6;
        position: sticky;
        left: 0;
        top: 0;
        z-index: 3;
        min-width: 120px;
    }
    
    .section-header {
        background: #f8f9fa;
        padding: 0.5rem 0.5rem;
        text-align: center;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #dee2e6;
        border-right: 1px solid #e9ecef;
        position: sticky;
        top: 0;
        z-index: 2;
        min-width: 60px;
        width: fit-content;
        height: auto;
    }
    
    .header-text {
        writing-mode: horizontal;
        font-size: 0.75rem;
    }
    
    .industry-header {
        background: #f8f9fa;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        color: #495057;
        white-space: nowrap;
        position: sticky;
        left: 0;
        z-index: 1;
        border-right: 2px solid #dee2e6;
        border-bottom: 1px solid #e9ecef;
        min-width: 120px;
    }
    
    .heatmap-cell {
        min-width: 60px;
        max-width: 60px;
        height: 50px;
        text-align: center;
        vertical-align: middle;
        border-right: 1px solid #e9ecef;
        border-bottom: 1px solid #e9ecef;
        transition: all 0.2s;
    }
    
    .heatmap-cell.clickable {
        cursor: pointer;
    }
    
    .heatmap-cell.clickable:hover {
        box-shadow: inset 0 0 0 3px #0d6efd;
        z-index: 1;
        transform: scale(1.05);
    }
    
    .cell-value {
        font-size: 0.75rem;
        font-weight: 600;
        color: #000;
        text-shadow: 0 0 3px rgba(255,255,255,0.8);
    }
    
    .cell-empty {
        color: #adb5bd;
        font-size: 1rem;
    }
    
    .legend {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        margin-top: 1rem;
        border-top: 2px solid #e9ecef;
        flex-wrap: wrap;
        background: #f8f9fa;
        border-radius: 6px;
    }
    
    .legend-title {
        font-weight: 600;
        color: #495057;
        margin-right: 0.5rem;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.75rem;
        color: #495057;
    }
    
    .legend-color {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 1px solid #dee2e6;
    }
    
    .legend-note {
        width: 100%;
        text-align: center;
        color: #0d6efd;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .no-data {
        text-align: center;
        padding: 3rem;
        color: #6c757d;
        font-style: italic;
    }
    
    .heatmap-scroll::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    .heatmap-scroll::-webkit-scrollbar-track {
        background: #f1f3f5;
        border-radius: 5px;
    }
    
    .heatmap-scroll::-webkit-scrollbar-thumb {
        background: #ced4da;
        border-radius: 5px;
    }
    
    .heatmap-scroll::-webkit-scrollbar-thumb:hover {
        background: #adb5bd;
    }
</style>