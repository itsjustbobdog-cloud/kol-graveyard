// 🪦 KOL GRAVEYARD JavaScript 🪦
// Built by Archon while Russ slept

document.addEventListener('DOMContentLoaded', () => {
    // Initialize handle input
    const handleInput = document.getElementById('handle-input');
    if (handleInput) {
        handleInput.addEventListener('input', (e) => {
            // Remove @ if user types it
            e.target.value = e.target.value.replace(/^@/, '');
        });
        
        handleInput.focus();
    }
});

// Load recent burials from API
async function loadRecentBurials() {
    const container = document.getElementById('recent-tombstones');
    if (!container) return;
    
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // For now, show a message since we don't have a recent burials endpoint
        if (data.total_buried === 0) {
            container.innerHTML = `
                <div class="empty-graveyard" style="grid-column: 1 / -1;">
                    <p>No fresh graves yet. Be the first to bury a shill.</p>
                </div>
            `;
        } else {
            // Load actual burials
            const gravesResponse = await fetch('/api/graveyard');
            const graves = await gravesResponse.json();
            
            if (graves.length === 0) {
                container.innerHTML = `
                    <div class="empty-graveyard" style="grid-column: 1 / -1;">
                        <p>Fresh burial coming soon...</p>
                    </div>
                `;
            } else {
                // Render up to 6 recent burials
                const recent = graves.slice(0, 6);
                container.innerHTML = recent.map(roast => `
                    <a href="/r/${roast.handle}" class="tombstone-link">
                        <div class="tombstone-card mini">
                            <div class="tombstone-shape">
                                <div class="tombstone-header">
                                    <span class="cross">✝</span>
                                </div>
                                <div class="tombstone-body">
                                    <h3 class="deceased-name">${roast.display_name || roast.handle}</h3>
                                    <p class="deceased-handle">@${roast.handle}</p>
                                    <div class="mini-stats">
                                        <span class="mini-stat" title="Paid promos">📢 ${roast.promo_count}</span>
                                        <span class="mini-stat dead" title="Dead projects">💀 ${roast.dead_count}</span>
                                    </div>
                                    <div class="death-info small">
                                        <span>${roast.death_date}</span>
                                    </div>
                                </div>
                                <div class="tombstone-footer">
                                    <span class="view-roast">View Roast →</span>
                                </div>
                            </div>
                            <div class="grass-stripe">🌿 🍂 🌱</div>
                        </div>
                    </a>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading recent burials:', error);
        container.innerHTML = `
            <div class="loading-tomb" style="grid-column: 1 / -1;">
                The spirits are restless. Try refreshing.
            </div>
        `;
    }
}

// Load stats from API
async function loadStats() {
    const buriedEl = document.getElementById('buried-count');
    const shillsEl = document.getElementById('shill-count');
    const casualtiesEl = document.getElementById('casualty-count');
    
    if (!buriedEl) return;
    
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Animate numbers
        animateNumber(buriedEl, data.total_buried);
        animateNumber(shillsEl, data.total_shills);
        animateNumber(casualtiesEl, data.total_casualties);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Animate number counting
function animateNumber(element, target) {
    const duration = 1000;
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease out
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(ease * target);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = target.toLocaleString();
        }
    }
    
    requestAnimationFrame(update);
}

// Form submission handler with loading state
document.addEventListener('submit', (e) => {
    if (e.target.matches('.search-form')) {
        const btn = e.target.querySelector('.bury-btn');
        const originalText = btn.innerHTML;
        
        btn.innerHTML = '<span>⚰️ Digging...</span>';
        btn.disabled = true;
        
        // Visual feedback
        btn.style.opacity = '0.7';
    }
});
