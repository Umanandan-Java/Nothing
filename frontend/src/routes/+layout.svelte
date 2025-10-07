<main class="app-shell">
  <nav class="main-nav">
    <a href="/overall-analysis">Overall Analysis</a>
    <a href="/">Sentiment Analysis Dashboard</a>
    <a href="/summaries">Text Summary & Word Cloud</a>
  </nav>
  <div class="content">
    <slot />
  </div>
</main>

<style>
  :global(body) {
    font-family: system-ui, -apple-system, sans-serif;
    margin: 0;
    background-color: #f8f9fa;
    color: #212529;
  }
  .main-nav {
    background-color: white;
    padding: 0 2rem;
    display: flex;
    gap: 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-bottom: 1px solid #dee2e6;
  }
  .main-nav a {
    color: #495057;
    text-decoration: none;
    font-size: 1rem;
    font-weight: 500;
    padding: 1.5rem 0;
    border-bottom: 3px solid transparent;
  }
  .content {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }
</style>