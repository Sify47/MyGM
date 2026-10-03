// Simple fetch wrapper for the JSON API
async function fetchState() {
    const res = await fetch('/api/state');
    if (!res.ok) return null;
    return res.json();
}

async function fetchWrestler(id) {
    const res = await fetch(`/api/wrestler/${id}`);
    if (!res.ok) return null;
    return res.json();
}

// Auto-refresh dashboard numbers every 30s (optional)
if (window.location.pathname.includes('dashboard')) {
    setInterval(async () => {
        const state = await fetchState();
        if (state) {
            // Hook for live updates later
            console.log('State refreshed', state.current_week);
        }
    }, 30000);
}