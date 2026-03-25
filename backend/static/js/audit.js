window.appAudit = {
    async openAudit() {
        this.view = 'audit';
        this.fetchCurrentAudit();
    },

    async fetchCurrentAudit() {
        try {
            const res = await axios.get('/inventory-audits/current');
            this.currentAudit = res.data;
        } catch (e) { console.error(e); }
    },

    async startAuditManual() {
        try {
            await axios.post('/inventory-audits/start');
            this.fetchCurrentAudit();
            this.checkSystemStatus();
        } catch (e) { alert('خطأ في بدء الجرد'); }
    },

    async skipAuditManual() {
        if (!confirm('هل أنت متأكد من تخطي الجرد لهذا الشهر؟ سيتم فتح النظام فوراً.')) return;
        try {
            await axios.post('/inventory-audits/skip');
            this.systemLocked = false;
            this.fetchCurrentAudit();
            this.checkSystemStatus();
            alert('تم تخطي الجرد وفتح النظام بنجاح');
        } catch (e) { alert('خطأ في تخطي الجرد'); }
    },

    async submitAudit() {
        try {
            const payload = {
                items: this.currentAudit.items.map(i => ({
                    product_id: i.product_id,
                    actual_quantity: parseFloat(i.actual_quantity) || 0
                }))
            };
            await axios.post('/inventory-audits/submit', payload);
            alert('تم اعتماد الجرد بنجاح وفتح النظام');
            this.systemLocked = false;
            this.view = 'warehouse';
            this.fetchWarehouseData();
        } catch (e) { alert(e.response?.data?.detail || 'خطأ في اعتماد الجرد'); }
    }
};
