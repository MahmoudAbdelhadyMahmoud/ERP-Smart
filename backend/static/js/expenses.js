window.appExpenses = {
    showDetails(exp) {
        this.activeExpense = exp;
        this.showDetailsModal = true;
    },

    async addExpense() {
        if (this.formData.items.length === 0) {
            alert('يرجى إضافة بند واحد على الأقل للمصروف');
            return;
        }
        try {
            const cleanedData = {
                ...this.formData,
                items: this.formData.items.map(i => ({
                    expense_type_id: parseInt(i.expense_type_id),
                    product_id: i.product_id ? parseInt(i.product_id) : null,
                    description: i.description || "",
                    description_chinese: i.description_chinese || "",
                    quantity: parseFloat(i.quantity) || 0,
                    unit_price: parseFloat(i.unit_price) || 0,
                    tax: parseFloat(i.tax) || 0,
                    discount: parseFloat(i.discount) || 0,
                    amount: parseFloat(i.amount) || 0
                }))
            };

            if (this.isEditing) {
                await axios.put(`/expenses/${this.editingId}`, cleanedData);
            } else {
                await axios.post('/expenses', cleanedData);
            }
            this.view = 'dashboard';
            this.resetForm();
            this.fetchData();
            this.showToast('تم حفظ المصروف بنجاح');
        } catch (e) { 
            this.showToast('خطأ في الحفظ: ' + (e.response?.data?.detail || ''), 'error');
        }
    },

    editExpense(exp) {
        this.isEditing = true;
        this.view = 'register_expense';
        this.editingId = exp.id;
        this.formData = {
            date: exp.date,
            amount_egp: exp.amount_egp,
            taxes: exp.taxes,
            discount_pct: exp.discount_pct,
            total: exp.total,
            notes: exp.notes,
            cost_center_id: exp.cost_center_id,
            invoice_number: exp.invoice_number || '',
            items: exp.items.map(i => {
                const base = (i.quantity || 1) * (i.unit_price || 0);
                return {
                    expense_type_id: i.expense_type_id,
                    product_id: i.product_id || '',
                    description: i.description,
                    description_chinese: i.description_chinese || '',
                    quantity: i.quantity || 1,
                    unit_price: i.unit_price || 0,
                    tax: i.tax || 0,
                    tax_pct: base > 0 ? ((i.tax || 0) / base * 100).toFixed(1) : 0,
                    discount: i.discount || 0,
                    discount_pct: base > 0 ? ((i.discount || 0) / base * 100).toFixed(1) : 0,
                    amount: i.amount
                };
            })
        };
    },

    async deleteExpense(id) {
        if (!confirm('هل أنت متأكد من حذف هذا المصروف؟')) return;
        try {
            await axios.delete(`/expenses/${id}`);
            this.fetchData();
            this.showToast('تم حذف المصروف بنجاح');
        } catch (e) { alert('خطأ في الحذف'); }
    },

    async getRecommendation() {
        if (!this.formData.notes) {
            alert('يرجى كتابة ملاحظات أولاً للحصول على اقتراح');
            return;
        }
        try {
            const res = await axios.post('/recommend', {
                notes: this.formData.notes,
                amount: parseFloat(this.formData.amount_egp)
            });
            if (res.data.recommended_type && res.data.recommended_type !== 'Other') {
                const found = this.expenseTypes.find(et => res.data.recommended_type.includes(et.name));
                if (found) {
                    this.formData.expense_type_id = found.id;
                } else {
                    alert('النوع المقترح غير مسجل حالياً: ' + res.data.recommended_type);
                }
            } else { alert('لا توجد بيانات كافية للاقتراح بعد'); }
        } catch (e) { console.error(e); }
    },

    resetForm() {
        this.isEditing = false;
        this.editingId = null;
        this.default_expense_type_id = '';
        this.tax_pct = 0;
        this.discount_amount = 0;
        this.formData = {
            date: new Date().toISOString().split('T')[0],
            amount_egp: 0,
            taxes: 0,
            discount_pct: 0,
            total: 0,
            notes: '',
            cost_center_id: '',
            invoice_number: '',
            items: []
        };
        this.addItemRow();
        this.updateSubtotal();
    },

    async importExpenses(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        this.showToast('جاري استيراد الفواتير من ملف Excel...', 'info');
        try {
            const res = await axios.post('/expenses/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            this.showToast(res.data.message || 'تم الاستيراد بنجاح ✅');
            this.fetchData();
            this.view = 'dashboard';
        } catch (e) {
            this.showToast(e.response?.data?.detail || 'فشل عملية الاستيراد ❌', 'error');
        } finally {
            event.target.value = ''; // Reset for next use
        }
    }
};
