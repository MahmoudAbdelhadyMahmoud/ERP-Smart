window.appForms = {
    removeItem(index) {
        this.formData.items.splice(index, 1);
        this.updateSubtotal();
    },

    addItemRow() {
        this.formData.items.push({
            expense_type_id: this.default_expense_type_id || '',
            product_id: '',
            description: '',
            description_chinese: '',
            quantity: 1,
            unit_price: 0,
            tax: 0,
            tax_pct: 0,
            discount: 0,
            discount_pct: 0,
            amount: 0
        });
    },

    applyDefaultType() {
        if (!this.default_expense_type_id) return;
        this.formData.items.forEach(item => {
            item.expense_type_id = this.default_expense_type_id;
        });
    },

    updateItemTotal(item) {
        const base = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
        const tax = parseFloat(item.tax) || 0;
        const discount = parseFloat(item.discount) || 0;
        item.amount = base + tax - discount;
        this.updateSubtotal();
    },

    updateItemTaxFromPct(item) {
        const base = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
        item.tax = (base * (parseFloat(item.tax_pct) || 0) / 100).toFixed(2);
        this.updateItemTotal(item);
    },

    updateItemTaxFromAmount(item) {
        const base = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
        if (base > 0) {
            item.tax_pct = ((parseFloat(item.tax) || 0) / base * 100).toFixed(1);
        }
        this.updateItemTotal(item);
    },

    updateItemDiscountFromPct(item) {
        const base = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
        item.discount = (base * (parseFloat(item.discount_pct) || 0) / 100).toFixed(2);
        this.updateItemTotal(item);
    },

    updateItemDiscountFromAmount(item) {
        const base = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
        if (base > 0) {
            item.discount_pct = ((parseFloat(item.discount) || 0) / base * 100).toFixed(1);
        }
        this.updateItemTotal(item);
    },

    updateSubtotal() {
        this.formData.amount_egp = this.formData.items.reduce((sum, item) => sum + (parseFloat(item.amount) || 0), 0);
        this.calculateGrandTotal();
    },

    updateTaxFromPct() {
        const subtotal = parseFloat(this.formData.amount_egp) || 0;
        this.formData.taxes = (subtotal * (parseFloat(this.tax_pct) || 0) / 100).toFixed(2);
        this.calculateGrandTotal();
    },

    updateTaxFromAmount() {
        const subtotal = parseFloat(this.formData.amount_egp) || 0;
        if (subtotal > 0) {
            this.tax_pct = ((parseFloat(this.formData.taxes) || 0) / subtotal * 100).toFixed(1);
        }
        this.calculateGrandTotal();
    },

    updateDiscountFromPct() {
        const subtotal = parseFloat(this.formData.amount_egp) || 0;
        this.discount_amount = (subtotal * (parseFloat(this.formData.discount_pct) || 0) / 100).toFixed(2);
        this.calculateGrandTotal();
    },

    updateDiscountFromAmount() {
        const subtotal = parseFloat(this.formData.amount_egp) || 0;
        if (subtotal > 0) {
            this.formData.discount_pct = ((parseFloat(this.discount_amount) || 0) / subtotal * 100).toFixed(1);
        }
        this.calculateGrandTotal();
    },

    calculateGrandTotal() {
        const subtotal = parseFloat(this.formData.amount_egp) || 0;
        const taxes = parseFloat(this.formData.taxes) || 0;
        const discount_val = (subtotal * (parseFloat(this.formData.discount_pct) || 0) / 100);
        this.formData.total = subtotal + taxes - discount_val;
    }
};
