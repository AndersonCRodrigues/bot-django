/**
 * Charts.js - Gráficos do Dashboard Admin
 */

class DashboardCharts {
    constructor() {
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                    labels: { color: '#A1A1AA' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#71717A' },
                    grid: { color: '#27272A' }
                },
                x: {
                    ticks: { color: '#71717A' },
                    grid: { display: false }
                }
            }
        };
    }

    createTokensChart(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;

        const labels = data.map(d => d.date);
        const values = data.map(d => d.tokens);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tokens',
                    data: values,
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
                }]
            },
            options: this.defaultOptions
        });
    }

    createCostChart(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;

        const labels = data.map(d => d.date);
        const values = data.map(d => d.cost);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Custo (USD)',
                    data: values,
                    backgroundColor: '#F59E0B',
                    borderRadius: 4
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        ticks: {
                            color: '#71717A',
                            callback: value => '$' + value.toFixed(2)
                        }
                    }
                }
            }
        });
    }

    createOperationsChart(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;

        const labels = data.map(d => d.operation_type);
        const values = data.map(d => d.count);

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#6366F1',
                        '#8B5CF6',
                        '#EC4899',
                        '#F59E0B',
                        '#10B981'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: '#A1A1AA' }
                    }
                }
            }
        });
    }
}

// Export para uso global
window.DashboardCharts = DashboardCharts;