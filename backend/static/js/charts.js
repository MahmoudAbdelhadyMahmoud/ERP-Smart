window.appCharts = {
    renderChart() {
        if (this.view !== 'analytics') return;
        
        const container = document.getElementById('expenseChartContainer');
        if (!container || container.offsetParent === null) {
            // Container currently hidden by Alpine, will retry shortly.
            setTimeout(() => this.renderChart(), 100);
            return;
        }

        // Clean injection to prevent any Chart.js internal rendering bugs
        container.innerHTML = '<canvas id="expenseChart"></canvas>';
        const ctx = document.getElementById('expenseChart').getContext('2d');

        const labels = Object.keys(this.analyticsSummary || {});
        const data = Object.values(this.analyticsSummary || {});

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    },

    initStockChart(data = null) {
        if (!data) data = this.stockChartData;
        if (!data || this.view !== 'warehouse' || this.warehouseView !== 'items') return;
        
        const container = document.getElementById('stockChartContainer');
        if (!container || container.offsetParent === null) {
            // Container currently hidden by Alpine, will retry shortly.
            setTimeout(() => this.initStockChart(data), 100);
            return;
        }

        // Clean injection to prevent any Chart.js internal rendering bugs
        container.innerHTML = '<canvas id="stockChart"></canvas>';
        const ctx = document.getElementById('stockChart').getContext('2d');

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'الكمية المتوفرة',
                    data: data.data,
                    backgroundColor: 'rgba(79, 70, 229, 0.6)',
                    borderColor: 'rgba(79, 70, 229, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 500 },
                scales: { 
                    y: { 
                        beginAtZero: true,
                        ticks: { font: { family: 'Cairo' } }
                    },
                    x: {
                        ticks: { font: { family: 'Cairo' } }
                    }
                },
                plugins: {
                    legend: {
                        labels: { font: { family: 'Cairo' } }
                    }
                }
            }
        });
    }
};
