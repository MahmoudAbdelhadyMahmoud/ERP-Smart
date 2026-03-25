window.appRouting = {
    initRouting() {
        const hash = window.location.hash.replace('#/', '');
        if (hash) {
            const [v, wv] = hash.split('/');
            this.view = v;
            if (wv) this.warehouseView = wv;
        } else {
            this.view = 'dashboard';
            this.updateBackendUrl(this.view, this.warehouseView);
        }

        // Load view-specific data on initial routing
        if (this.view === 'warehouse') this.fetchWarehouseData();
        if (this.view === 'analytics') this.fetchAnalyticsData();
        if (this.view === 'audit') this.fetchCurrentAudit();
        if (this.view === 'opening_balances') this.fetchOpeningBalancesData();
        if (this.view === 'costing') this.fetchRecipes();
        if (this.view === 'stock_control') this.fetchStockControlData();
        if (this.view === 'register_expense' && !this.isEditing) {
            if (this.formData.items.length === 0) this.addItemRow();
        }
    },

    navigate(path, subPath = null) {
        this.view = path;
        if (subPath) this.warehouseView = subPath;
        this.updateBackendUrl(path, subPath);

        if (path === 'warehouse') this.fetchWarehouseData();
        if (path === 'analytics') this.fetchAnalyticsData();
        if (path === 'audit') this.fetchCurrentAudit();
        if (path === 'opening_balances') this.fetchOpeningBalancesData();
        if (path === 'costing') this.fetchRecipes();
        if (path === 'stock_control') this.fetchStockControlData();
        if (path === 'register_expense' && !this.isEditing) {
            this.resetForm();
        }
    },

    updateBackendUrl(v, wv = null) {
        const path = wv ? `${v}/${wv}` : v;
        window.location.hash = `/${path}`;
        localStorage.setItem('last_view', path);
    }
};
