<script>
  import { page } from '$app/stores';
</script>
<main class="app-shell">
  <nav class="main-nav">
  <a href="/" class:active={$page.url.pathname === '/'}>Overall Analysis</a>
  <a href="/sentimental-analysis" class:active={$page.url.pathname === '/sentimental-analysis'}>Sentiment Analysis Dashboard</a>
  <a href="/summaries" class:active={$page.url.pathname === '/summaries'}>Text Summary & Word Cloud</a>
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
    padding: 1rem 2rem;
    display: flex;
    gap: 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-bottom: 1px solid #dee2e6;
  }
  .main-nav a {
  color: black;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  padding: 1rem 1rem;
  border-bottom: 3px solid transparent;
  border-radius: 10px;
  background-color: transparent;
}

.main-nav a.active {
  background-color: #0D6EF0;
  color: white;
}

  .content {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }
</style>