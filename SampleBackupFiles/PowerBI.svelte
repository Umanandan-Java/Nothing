<svelte:head>
    <title>Sentiment Analysis Dashboard</title>
</svelte:head>

<div class="page-header">
    <h1>Interactive Sentiment Dashboard</h1>
    <p>This dashboard is a fully interactive Power BI report embedded within our application.</p>
</div>

<div class="iframe-container">
    <!-- Your provided iFrame goes here -->
    <iframe title="Econsultation" width="1140" height="641" src="https://app.powerbi.com/reportEmbed?reportId=43111e45-8660-4f6f-877b-7941f3fb6a86&autoAuth=true&ctid=c58bf622-52be-4f23-a188-a30040a9896f" frameborder="0" allowFullScreen="true"></iframe>
</div>

<style>
    .page-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .iframe-container {
        display: flex;
        justify-content: center;
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 6px 15px rgba(36, 37, 38, 0.08);
    }
    iframe {
        max-width: 100%;
    }
</style>