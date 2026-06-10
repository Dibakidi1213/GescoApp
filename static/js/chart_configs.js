/**
 * Configuration globale des graphiques Chart.js pour la plateforme scolaire.
 */

const chartColors = {
    primary: 'rgba(54, 162, 235, 0.8)',
    secondary: 'rgba(255, 99, 132, 0.8)',
    success: 'rgba(75, 192, 192, 0.8)',
    warning: 'rgba(255, 206, 86, 0.8)',
    danger: 'rgba(255, 99, 132, 0.8)',
    info: 'rgba(153, 102, 255, 0.8)',
    grey: 'rgba(201, 203, 207, 0.8)'
};

function createLineChart(ctx, labels, data, title) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                borderColor: chartColors.primary,
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function createBarChart(ctx, labels, data, title, color = chartColors.primary) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: color,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true } }
        }
    });
}

function createPieChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: Object.values(chartColors)
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// Fonction pour rafraîchir les données via API
async function refreshDashboardData(apiEndpoint, updateCallback) {
    try {
        const response = await fetch(apiEndpoint);
        const data = await response.json();
        updateCallback(data);
    } catch (error) {
        console.error('Erreur lors du rafraîchissement du dashboard:', error);
    }
}

// Exportation globale
window.DashboardManager = {
    createLineChart,
    createBarChart,
    createPieChart,
    refreshDashboardData,
    colors: chartColors
};
