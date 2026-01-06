/**
 * Aadhaar Analysis Dashboard - Application JavaScript
 * Premium "Royal Tech" Implementation
 */

// ============================================
// CONFIGURATION
// ============================================

const DATA_URL = 'data/analysis_results.json';

// Universal Chart Styling
const THEME = {
    gold: '#fbbf24',
    sky: '#0ea5e9',
    emerald: '#10b981',
    rose: '#f43f5e',
    slate: '#94a3b8',
    midnight: '#1e293b',
    grid: 'rgba(255, 255, 255, 0.05)',
    font: 'Plus Jakarta Sans'
};

Chart.defaults.color = THEME.slate;
Chart.defaults.font.family = THEME.font;
Chart.defaults.plugins.legend.display = false;

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatNumber(num) {
    if (!num && num !== 0) return '--';
    if (num >= 10000000) {
        return (num / 10000000).toFixed(2) + ' Cr';
    } else if (num >= 100000) {
        return (num / 100000).toFixed(2) + ' L';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return Math.round(num).toLocaleString('en-IN');
}

function formatCurrency(num) {
    return '₹' + formatNumber(num);
}

function getStatusBadge(score) {
    if (score >= 0.7) return '<span class="badge status-critical">Critical Risk</span>';
    if (score >= 0.4) return '<span class="badge status-high">Heightened</span>';
    return '<span class="badge status-medium">Stable</span>';
}

function getInfrastructureBadge(rec) {
    const clean = rec.replace('Aadhaar ', '');
    if (rec.includes('ASK')) return `<span class="badge status-high">${clean}</span>`;
    return `<span class="badge status-medium">${clean}</span>`;
}

function updateTimestamp() {
    const now = new Date();
    const options = {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    const ts = document.getElementById('timestamp');
    if (ts) ts.textContent = now.toLocaleDateString('en-IN', options);
}

// ============================================
// DATA LOADING
// ============================================

async function loadData() {
    try {
        const response = await fetch(DATA_URL + '?t=' + new Date().getTime());
        if (!response.ok) throw new Error('Data source offline');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Core Intelligence Failure:', error);
        return null;
    }
}

// ============================================
// RENDER FUNCTIONS
// ============================================

function renderSummaryMetrics(summary) {
    document.getElementById('total-records').textContent = formatNumber(summary.total_records);
    document.getElementById('maintenance-deserts').textContent = summary.maintenance_deserts_count;
    document.getElementById('migration-hotspots').textContent = summary.migration_hotspots_count;
    document.getElementById('projected-surge').textContent = formatNumber(summary.total_projected_surge);
    document.getElementById('fiscal-risk').textContent = (summary.total_fiscal_risk / 10000000).toFixed(2);
    document.getElementById('total-states').textContent = summary.total_states;
}

function renderSurgeChart(data) {
    const ctx = document.getElementById('surgeChart').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(14, 165, 233, 0.5)');
    gradient.addColorStop(1, 'rgba(14, 165, 233, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.state),
            datasets: [{
                data: data.map(d => d.projected_surge),
                borderColor: THEME.sky,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 0,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: THEME.grid }, ticks: { callback: v => formatNumber(v) } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderFiscalChart(data) {
    const ctx = document.getElementById('fiscalChart').getContext('2d');
    const sorted = [...data].sort((a, b) => b.total_fiscal_risk - a.total_fiscal_risk).slice(0, 5);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sorted.map(d => d.state),
            datasets: [{
                data: sorted.map(d => d.total_fiscal_risk),
                backgroundColor: [THEME.gold, THEME.sky, THEME.emerald, THEME.rose, THEME.midnight],
                borderWidth: 0,
                hoverOffset: 20
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: { color: THEME.slate, usePointStyle: true, padding: 20 }
                }
            }
        }
    });
}

function renderPriorityChart(data) {
    const ctx = document.getElementById('priorityChart').getContext('2d');
    const sorted = [...data].sort((a, b) => b.priority_score - a.priority_score).slice(0, 10);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(d => d.state),
            datasets: [{
                data: sorted.map(d => d.priority_score),
                backgroundColor: THEME.gold,
                borderRadius: 4,
                barThickness: 12
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { max: 1, grid: { color: THEME.grid } },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderPriorityTable(data) {
    const tbody = document.querySelector('#priority-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    data.slice(0, 10).forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span style="color: var(--text-primary); font-weight: 600;">${item.pincode}</span></td>
            <td>${Math.abs(item.maintenance_risk).toFixed(1)}% Lag</td>
            <td>${formatNumber(item.migration_impact)}</td>
            <td>${formatNumber(item.age_0_5)}</td>
            <td><span style="color: var(--brand-gold); font-weight: 800;">${item.priority_score.toFixed(3)}</span></td>
        `;
        tbody.appendChild(row);
    });
}

function renderWelfareTable(data) {
    const tbody = document.querySelector('#welfare-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const maxScore = Math.max(...data.map(d => d.welfare_risk_score));

    data.slice(0, 10).forEach(item => {
        const normalized = item.welfare_risk_score / maxScore;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span style="color: var(--text-primary); font-weight: 600;">${item.district}</span></td>
            <td>${formatNumber(item.welfare_risk_score)}</td>
            <td>${getStatusBadge(normalized)}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderRecommendationsTable(data) {
    const tbody = document.querySelector('#recommendations-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    data.slice(0, 10).forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span style="color: var(--text-primary); font-weight: 600;">${item.pincode}</span></td>
            <td>${item.priority_score.toFixed(3)}</td>
            <td>${formatNumber(item.total_activity)}</td>
            <td>${getInfrastructureBadge(item.recommendation)}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderActionPlan(data) {
    const container = document.getElementById('action-cards');
    if (!container) return;
    container.innerHTML = '';

    if (!data) return; // Guard clause if action_plan is missing

    data.forEach(action => {
        const card = document.createElement('div');
        card.className = 'action-card glass';
        card.innerHTML = `
            <span class="action-priority">${action.priority} PRIORITY</span>
            <h4>${action.title}</h4>
            <p>${action.description}</p>
            <span class="action-target">Unit Target: ${action.target}</span>
        `;
        container.appendChild(card);
    });
}

function renderDesertsList(data) {
    const list = document.getElementById('deserts-list');
    if (!list) return;
    list.innerHTML = '';

    // Filter out dummy data
    const valid = data.filter(d => !d.district.match(/^[0-9?*]+$/)).slice(0, 8);

    valid.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.district}</span>
            <span class="insight-value">${(item.update_ratio * 100).toFixed(1)}% Update Rate</span>
        `;
        list.appendChild(li);
    });
}

function renderHotspotsList(data) {
    const list = document.getElementById('hotspots-list');
    if (!list) return;
    list.innerHTML = '';

    data.slice(0, 8).forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.district}, ${item.state}</span>
            <span class="insight-value">${formatNumber(item.migration_ratio)}</span>
        `;
        list.appendChild(li);
    });
}

// ============================================
// MAP VISUALIZATION
// ============================================

async function renderMap(mapData) {
    const mapContainer = document.getElementById('india-map');
    if (!mapContainer) return;

    // Initialize Map
    // Center of India roughly
    const map = L.map('india-map', {
        zoomControl: false,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: false
    }).setView([22.5937, 78.9629], 5);

    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Fetch GeoJSON
    try {
        const response = await fetch('data/india.geojson');
        if (!response.ok) throw new Error('Map geometry fetch failed');
        const geoJson = await response.json();

        // Calculate Data Range for Dynamic Scaling
        const scores = Object.values(mapData).map(s => s.priority_score).filter(s => s > 0);
        const minScore = Math.min(...scores) || 0.3;
        const maxScore = Math.max(...scores) || 0.4;
        const range = maxScore - minScore;

        // Helper to get color based on Relative Priority
        function getColor(score) {
            if (score === 0) return '#1e293b'; // No data

            // Calculate normalized position (0 to 1) within the state range
            const normalized = (score - minScore) / (range || 1);

            if (normalized > 0.75) return '#f43f5e'; // Top 25% (Critical)
            if (normalized > 0.50) return '#fbbf24'; // Top 50% (Elevated)
            if (normalized > 0.25) return '#0ea5e9'; // Above average (Moderate)
            return '#10b981'; // Bottom 25% (Stable)
        }

        // Helper to resolve state stats with fuzzy matching
        function getStatForState(name, data) {
            if (!name) return null;

            const aliases = {
                'Andaman and Nicobar': 'Andaman And Nicobar Islands',
                'Andaman & Nicobar': 'Andaman And Nicobar Islands',
                'Chhatisgarh': 'Chhattisgarh',
                'Orissa': 'Odisha',
                'Tamilnadu': 'Tamil Nadu',
                'West Bangal': 'West Bengal',
                'West Bengli': 'West Bengal',
                'Westbengal': 'West Bengal',
                'Uttaranchal': 'Uttarakhand',
                'Jammu & Kashmir': 'Jammu And Kashmir',
                'Jammu and Kashmir': 'Jammu And Kashmir',
                'Delhi': 'NCT of Delhi',
                'Pondicherry': 'Puducherry'
            };

            const normalize = n => n.toLowerCase()
                .replace(/ & /g, ' and ')
                .replace(/ islands/g, '')
                .replace(/ state/g, '')
                .replace(/ ut/g, '')
                .replace(/ territory/g, '')
                .replace(/ /g, '')
                .trim();

            const nName = normalize(name);
            const aName = aliases[name] ? normalize(aliases[name]) : null;

            // 1. Exact Name Match
            if (data[name]) return data[name];

            // 2. Exact Alias Match
            if (aliases[name] && data[aliases[name]]) return data[aliases[name]];

            // 3. Normalized Fuzzy Match
            const keys = Object.keys(data);
            const match = keys.find(k => {
                const nk = normalize(k);
                return nk === nName || nk === aName || nk.includes(nName) || nName.includes(nk);
            });

            return match ? data[match] : null;
        }

        // Initialize Layer
        const geoJsonLayer = L.geoJson(geoJson, {
            style: function (feature) {
                const name = feature.properties.NAME_1 || feature.properties.name || feature.properties.NAME;
                const stats = getStatForState(name, mapData);
                const score = stats ? stats.priority_score : 0;

                return {
                    fillColor: getColor(score),
                    weight: 1,
                    opacity: 1,
                    color: 'rgba(255, 255, 255, 0.44)',
                    fillOpacity: 0.8
                };
            },
            onEachFeature: function (feature, layer) {
                const name = feature.properties.NAME_1 || feature.properties.name || feature.properties.NAME;
                const stats = getStatForState(name, mapData);

                if (stats) {
                    layer.bindPopup(`
                        <div class="map-popup">
                            <h3>${name}</h3>
                            <div class="popup-grid">
                                <div class="popup-item full">
                                    <span class="label">Integrated Risk Index</span>
                                    <span class="value">${stats.priority_score.toFixed(3)}</span>
                                </div>
                                <div class="popup-item">
                                    <span class="label">Fiscal Risk</span>
                                    <span class="value">₹${(stats.fiscal_risk / 10000000).toFixed(2)} Cr</span>
                                </div>
                                <div class="popup-item">
                                    <span class="label">Future Surge</span>
                                    <span class="value">${formatNumber(stats.projected_surge)}</span>
                                </div>
                                <div class="popup-item">
                                    <span class="label">Maint. Gap</span>
                                    <span class="value">${(stats.maintenance_gap * 100).toFixed(1)}%</span>
                                </div>
                                <div class="popup-item">
                                    <span class="label">Migrant Churn</span>
                                    <span class="value">${(stats.migration_churn * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                    `);

                    layer.on({
                        mouseover: function (e) {
                            const l = e.target;
                            l.setStyle({
                                weight: 2,
                                color: '#ffffffff',
                                fillOpacity: 1
                            });
                            l.bringToFront();
                        },
                        mouseout: function (e) {
                            geoJsonLayer.resetStyle(e.target);
                        }
                    });
                }
            }
        }).addTo(map);

        // Zoom to fit India
        map.fitBounds(geoJsonLayer.getBounds());


        // Add Legend
        const legendContainer = document.getElementById('map-legend');
        const labels = ['Stable', 'Moderate Risk', 'Elevated Risk', 'Critical Priority'];

        // Percentile representative values
        const legendGrades = [
            minScore,                   // 0th (Stable)
            minScore + range * 0.3,     // ~30th (Moderate)
            minScore + range * 0.6,     // ~60th (Elevated)
            maxScore                    // 100th (Critical)
        ];

        legendGrades.forEach((grade, i) => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `
                <div class="legend-color" style="background:${getColor(grade)}"></div>
                <span>${labels[i]}</span>
            `;
            legendContainer.appendChild(item);
        });

    } catch (e) {
        console.error("Map Error", e);
        document.getElementById('india-map').innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--text-muted);">Geospatial Data Unavailable</p>`;
    }
}

// ============================================
// INITIALIZATION
// ============================================

async function init() {
    updateTimestamp();

    const data = await loadData();
    if (!data) return;

    // Safe Render Utility
    const safeRender = (fn, arg) => {
        try {
            fn(arg);
        } catch (e) {
            console.error(`Rendering failed for ${fn.name}:`, e);
        }
    };

    // Orchestrate Rendering safely
    safeRender(renderSummaryMetrics, data.summary);

    // Render Map (Priority)
    if (data.map_data) {
        // Run map rendering without blocking
        safeRender(renderMap, data.map_data);
    }

    safeRender(renderSurgeChart, data.update_surge);
    safeRender(renderFiscalChart, data.state_fiscal_risk);
    safeRender(renderPriorityChart, data.state_priority);
    safeRender(renderPriorityTable, data.top_priority_pincodes);
    safeRender(renderWelfareTable, data.welfare_risk_districts);
    safeRender(renderRecommendationsTable, data.recommendations);
    safeRender(renderActionPlan, data.action_plan);
    safeRender(renderDesertsList, data.maintenance_deserts);
    safeRender(renderHotspotsList, data.migration_hotspots);
}

document.addEventListener('DOMContentLoaded', init);
setInterval(updateTimestamp, 60000);