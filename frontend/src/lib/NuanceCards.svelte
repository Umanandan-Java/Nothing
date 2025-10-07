<script>
    export let commentsForDisplay = [];

    $: sarcasticAgreements = commentsForDisplay.filter(
        c => c.action_type === 'In Agreement' && c.sentiment_label === 'Negative'
    ).length;

    $: positiveModifications = commentsForDisplay.filter(
        c => c.action_type === 'Suggest modification' && c.sentiment_label === 'Positive'
    ).length;

    $: negativeRemovals = commentsForDisplay.filter(
        c => c.action_type === 'Suggest removal' && c.sentiment_label === 'Negative'
    ).length;
</script>

<div class="nuance-cards">
    <div class="nuance-card sarcastic">
        <h4>Sarcastic Agreements Detected</h4>
        <div class="card-value">{sarcasticAgreements}</div>
        <p class="card-description">AI detected hidden negativity</p>
    </div>

    <div class="nuance-card positive-mod">
        <h4>Positive Modifications</h4>
        <div class="card-value">{positiveModifications}</div>
        <p class="card-description">Constructive suggestions</p>
    </div>

    <div class="nuance-card negative-removal">
        <h4>Strongly Opposed</h4>
        <div class="card-value">{negativeRemovals}</div>
        <p class="card-description">Critical removal requests</p>
    </div>
</div>

<style>
    .nuance-cards {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .nuance-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
        padding: 0.5rem;
        text-align: center;
        transition: transform 0.2s;
    }

    .nuance-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    }

    .card-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .nuance-card h4 {
        font-size: 0.85rem;
        font-weight: 600;
        color: #495057;
        margin: 0.5rem 0;
    }

    .card-value {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }

    .card-description {
        font-size: 0.75rem;
        color: #6c757d;
        margin: 0;
    }

    .sarcastic {
        border-bottom: 3px solid #ff9800;
    }

    .sarcastic .card-value {
        color: #ff9800;
    }

    .positive-mod {
        border-bottom: 3px solid #28a745;
    }

    .positive-mod .card-value {
        color: #28a745;
    }

    .negative-removal {
        border-bottom: 3px solid #dc3545;
    }

    .negative-removal .card-value {
        color: #dc3545;
    }
</style>