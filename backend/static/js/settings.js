window.appSettings = {
    async addCostCenter() {
        if (!this.newCC.name || this.isLoadingCC) return;
        this.isLoadingCC = true;
        try {
            if (this.isEditingCC) { await axios.put(`/cost_centers/${this.editingCCId}`, this.newCC); }
            else { await axios.post('/cost_centers', this.newCC); }
            this.resetCC();
            this.fetchData();
            this.showToast('تم حفظ المركز بنجاح');
        } catch (e) { alert(e.response?.data?.detail || 'خطأ في العملية'); }
        finally { this.isLoadingCC = false; }
    },

    editCC(cc) {
        this.isEditingCC = true;
        this.editingCCId = cc.id;
        this.newCC = { name: cc.name, description: cc.description || '' };
    },

    async deleteCC(id) {
        if (!confirm('هل أنت متأكد من حذف هذا المركز؟')) return;
        try {
            await axios.delete(`/cost_centers/${id}`);
            this.fetchData();
            this.showToast('تم حذف المركز بنجاح');
        } catch (e) { alert(e.response?.data?.detail || 'خطأ في الحذف'); }
    },

    resetCC() {
        this.isEditingCC = false;
        this.editingCCId = null;
        this.newCC = { name: '', description: '' };
    },

    async addExpenseType() {
        if (!this.newET.name) return;
        try {
            if (this.isEditingET) { await axios.put(`/expense_types/${this.editingETId}`, this.newET); }
            else { await axios.post('/expense_types', this.newET); }
            this.resetET();
            this.fetchData();
            this.showToast('تم حفظ النوع بنجاح');
        } catch (e) { alert(e.response?.data?.detail || 'خطأ في العملية'); }
    },

    editET(et) {
        this.isEditingET = true;
        this.editingETId = et.id;
        this.newET = { name: et.name, name_chinese: et.name_chinese || '' };
    },

    async deleteET(id) {
        if (!confirm('هل أنت متأكد من حذف هذا النوع؟')) return;
        try {
            await axios.delete(`/expense_types/${id}`);
            this.fetchData();
            this.showToast('تم حذف النوع بنجاح');
        } catch (e) { alert(e.response?.data?.detail || 'خطأ في الحذف'); }
    },

    resetET() {
        this.isEditingET = false;
        this.editingETId = null;
        this.newET = { name: '', name_chinese: '' };
    }
};
