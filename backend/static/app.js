function expenseApp() {
    return {
        ...window.appState(),
        ...window.appUtils,
        ...window.appRouting,
        ...window.appAPI,
        ...window.appExpenses,
        ...window.appWarehouse,
        ...window.appAudit,
        ...window.appCharts,
        ...window.appSettings,
        ...window.appForms,
        ...window.appCosting,
        ...window.appI18n,

        get filteredExpenses() {
            return (this.expenses || []).filter(exp => {
                const d = new Date(exp.date);
                const from = this.filters.from_date ? new Date(this.filters.from_date) : null;
                const to = this.filters.to_date ? new Date(this.filters.to_date) : null;
                const matchDate = (!from || d >= from) && (!to || d <= to);
                const matchType = !this.filters.type_id || exp.items.some(i => i.expense_type_id == this.filters.type_id);
                const matchCC = !this.filters.cc_id || exp.cost_center_id == this.filters.cc_id;
                const matchInv = !this.filters.invoice_number || 
                                (exp.invoice_number?.toLowerCase().includes(this.filters.invoice_number.toLowerCase())) ||
                                (('EXP-'+exp.id).toLowerCase().includes(this.filters.invoice_number.toLowerCase()));
                return matchDate && matchType && matchCC && matchInv;
            });
        },

        get filteredMovements() {
            if (!this.movementFilterProductId) return this.movements || [];
            return (this.movements || []).filter(m => m.product_id == this.movementFilterProductId);
        },

        async openWarehouse() {
            this.view = 'warehouse';
            this.fetchWarehouseData();
        },

        async openAnalytics() {
            this.view = 'analytics';
            this.fetchAnalyticsData();
        },

        async init() {
            this.t = this.t.bind(this);
            this.locName = this.locName.bind(this);
            this.locDesc = this.locDesc.bind(this);
            this.initRouting();
            
            this.$watch('lang', (v) => { 
                window.appLang = v; 
                localStorage.setItem('app_lang', v);
            });
            
            await this.fetchData();
            this.checkSystemStatus();
            this.$watch('filters', () => this.calculateTotal());
            this.$watch('expenses', () => this.calculateTotal());
            this.$watch('view', (v) => {
                this.updateBackendUrl(v);
                if (v === 'warehouse' && this.warehouseView === 'items') {
                    this.$nextTick(() => this.initStockChart());
                }
                if (v === 'analytics') {
                    this.$nextTick(() => this.renderChart());
                }
            });
            this.$watch('warehouseView', (v) => {
                this.updateBackendUrl(this.view, v);
                if (this.view === 'warehouse' && v === 'items') {
                    // Slight delay to ensure Alpine has finished displaying the canvas container
                    setTimeout(() => {
                        this.initStockChart();
                    }, 50);
                }
            });
            window.addEventListener('hashchange', () => this.initRouting());
            setInterval(() => {
                this.fetchData(true);
                if (this.view === 'warehouse') this.fetchWarehouseData(true);
            }, 30000);
        }
    };
}