    // Frontend/src/lib/chartAction.js
    import Chart from 'chart.js/auto';
    import ChartDataLabels from 'chartjs-plugin-datalabels';
    import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';

    // Register plugins and controllers
    Chart.register(ChartDataLabels);
    Chart.register(MatrixController, MatrixElement);

    /**
     * A Svelte Action for integrating Chart.js in a robust, lifecycle-aware way.
     * @param {HTMLCanvasElement} canvas The canvas element the action is applied to.
     * @param {import('chart.js').ChartConfiguration} config The Chart.js configuration object.
     */
    export function chart(canvas, config) {
        let chartInstance = new Chart(canvas, config);

        return {
            // This function is called whenever the 'config' parameter changes.
            update(newConfig) {
                // Destroy the existing chart instance to prevent memory leaks and ensure proper updates
                chartInstance.destroy();
                // Create a new chart instance with the updated configuration
                chartInstance = new Chart(canvas, newConfig);
            },

            // This function is called when the component is unmounted, preventing memory leaks.
            destroy() {
                chartInstance.destroy();
            }
        };
    }