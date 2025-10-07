<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import ChartDataLabels from 'chartjs-plugin-datalabels';
  import { filterStore } from '$lib/stores/filterStore.js';

  export let commentsForDisplay = [];

  let chartCanvas;
  let chartInstance;

  $: if (commentsForDisplay && commentsForDisplay.length > 0) {
    updateChart();
  }

  function updateChart() {
    const total = commentsForDisplay.length;
    const pos = commentsForDisplay.filter(c => c.sentiment_label === 'Positive').length;
    const neu = commentsForDisplay.filter(c => c.sentiment_label === 'Neutral').length;
    const neg = commentsForDisplay.filter(c => c.sentiment_label === 'Negative').length;

    const posPercent = ((pos / total) * 100).toFixed(1);
    const neuPercent = ((neu / total) * 100).toFixed(1);
    const negPercent = ((neg / total) * 100).toFixed(1);

    const data = [posPercent, neuPercent, negPercent];

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(chartCanvas, {
      type: 'bar',
      data: {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
          label: '% of Comments',
          data,
          backgroundColor: ['#28a745', '#007bff', '#dc3545'],
          borderRadius: 8,
          barThickness: 25
        }]
      },
      options: {
        indexAxis: 'y', // horizontal layout
        responsive: true,
        maintainAspectRatio: false,
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const index = elements[0].index;
            const sentiments = ['Positive', 'Neutral', 'Negative'];
            filterStore.setFilter('sentiment', sentiments[index]);
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: (value) => `${value}%`,
              color: '#666',
              font: { size: 11 }
            },
            grid: { color: '#e9ecef' }
          },
          y: {
            ticks: {
              color: '#333',
              font: { size: 12, weight: '600' }
            },
            grid: { display: false }
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
            padding: 10,
            callbacks: {
              label: (context) => `${context.parsed.x}%`
            }
          },
          datalabels: {
            color: '#333',
            anchor: 'end',
            align: 'right',
            formatter: (value) => `${value}%`,
            font: { weight: 'bold', size: 13 }
          }
        }
      },
      plugins: [ChartDataLabels]
    });
  }
</script>

<div class="chart-wrapper">
  <canvas bind:this={chartCanvas}></canvas>
</div>

<style>
  .chart-wrapper {
    width: 100%;
    height: 200px;
    padding: 1rem;
  }
</style>
