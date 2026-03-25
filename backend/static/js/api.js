window.appAPI = {
    async checkSystemStatus() {
        try {
            const res = await axios.get(`/system-status?t=${Date.now()}`);
            this.systemLocked = res.data.locked;
        } catch (e) { console.error(e); }
    },

    async fetchData(silent = false) {
        try {
            const t = Date.now();
            const [expRes, ccRes, etRes, pRes] = await Promise.all([
                axios.get(`/expenses?t=${t}`),
                axios.get(`/cost_centers?t=${t}`),
                axios.get(`/expense_types?t=${t}`),
                axios.get(`/products?t=${t}`)
            ]);
            this.expenses = expRes.data;
            this.costCenters = ccRes.data;
            this.expenseTypes = etRes.data;
            this.products = pRes.data;
            this.calculateTotal();
        } catch (e) { 
            if (!silent) console.error('Error fetching data:', e);
        }
    },

    async fetchWarehouseData(silent = false) {
        try {
            const t = Date.now();
            const [pRes, mRes, tRes, sRes, lRes, splRes, statsRes] = await Promise.all([
                axios.get(`/products?t=${t}`),
                axios.get(`/movements?t=${t}`),
                axios.get(`/reports/warehouse/top-items?t=${t}`),
                axios.get(`/analytics/stock-summary?t=${t}`),
                axios.get(`/locations?t=${t}`),
                axios.get(`/reports/stock-per-location?t=${t}`),
                axios.get(`/dashboard/stats?t=${t}`)
            ]);
            this.products = pRes.data;
            this.movements = mRes.data;
            this.topItems = tRes.data;
            this.locations = lRes.data;
            this.stockPerLocation = splRes.data;
            this.stockChartData = sRes.data;
            this.warehouseStats = statsRes.data;
            
            this.$nextTick(() => {
                this.initStockChart(this.stockChartData);
            });
        } catch (e) { if (!silent) console.error(e); }
    },

    async fetchAnalyticsData() {
        try {
            const t = Date.now();
            const res = await axios.get(`/analytics/summary?t=${t}`);
            this.analyticsSummary = res.data.summary;
            this.recommendations = res.data.recommendations;
            this.$nextTick(() => this.renderChart());
        } catch (e) { console.error('Error fetching analytics:', e); }
    },

    async fetchOpeningBalancesData() {
        this.isLoadingOpening = true;
        try {
            const t = Date.now();
            const res = await axios.get(`/products?t=${t}`);
            this.openingBalances = res.data.map(p => ({
                id: p.id,
                code: p.code,
                name: p.name,
                unit: p.unit,
                current_stock: p.current_stock,
                qty: 0,
                price: 0
            }));
        } catch (e) { console.error(e); }
        finally { this.isLoadingOpening = false; }
    }
};
