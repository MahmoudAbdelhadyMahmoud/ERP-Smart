window.appWarehouse = {
    async addProduct() {
        if (!this.newProduct.name) return;
        try {
            if (this.isEditingProduct) {
                await axios.put(`/products/${this.editingProductId}`, this.newProduct);
            } else {
                await axios.post('/products', this.newProduct);
            }
            this.resetProduct();
            this.fetchWarehouseData();
            this.showToast('تم حفظ الصنف بنجاح');
        } catch (e) { 
            this.showToast(e.response?.data?.detail || 'خطأ في الحفظ', 'error');
        }
    },

    editProduct(p) {
        this.isEditingProduct = true;
        this.editingProductId = p.id;
        this.newProduct = { 
            name: p.name, name_chinese: p.name_chinese || '', unit: p.unit, code: p.code, 
            average_cost: p.average_cost, purchase_price: p.purchase_price, 
            reorder_level: p.reorder_level || 0, notes: p.notes || '' 
        };
    },

    async deleteProduct(id) {
        if (!confirm('هل أنت متأكد من حذف هذا الصنف نهائياً؟')) return;
        try {
            await axios.delete(`/products/${id}`);
            this.fetchWarehouseData();
            this.showToast('تم حذف الصنف بنجاح');
        } catch (e) { 
            this.showToast(e.response?.data?.detail || 'خطأ في الحذف', 'error');
        }
    },

    resetProduct() {
        this.isEditingProduct = false;
        this.editingProductId = null;
        this.newProduct = { name: '', name_chinese: '', unit: '', code: '', average_cost: 0, purchase_price: 0, reorder_level: 0, notes: '' };
    },

    async showPriceHistory(p) {
        try {
            const res = await axios.get(`/products/${p.id}/price-history`);
            this.currentProductPriceHistory = res.data;
            this.priceHistoryOpen = true;
        } catch (e) { 
            this.showToast('خطأ في جلب سجل الأسعار', 'error');
        }
    },

    async addMovement() {
        if (!this.newMovement.product_id || !this.newMovement.quantity || !this.newMovement.location_id) {
            alert('يرجى اختيار المنتج والكمية والمخزن');
            return;
        }
        try {
            if (this.isEditingMovement) {
                await axios.put(`/movements/${this.editingMovementId}`, this.newMovement);
            } else {
                await axios.post('/movements', this.newMovement);
            }
            this.resetMovementForm();
            this.fetchWarehouseData();
            this.showToast('تم تسجيل الحركة بنجاح');
        } catch (e) { 
            this.showToast(e.response?.data?.detail || 'خطأ في العملية', 'error');
        }
    },

    editMovement(m) {
        this.isEditingMovement = true;
        this.editingMovementId = m.id;
        this.newMovement = {
            product_id: m.product_id,
            location_id: m.location_id || '',
            type: m.type,
            quantity: m.quantity,
            unit_price: m.unit_price || 0,
            date: m.date,
            notes: m.notes || ''
        };
    },

    async deleteMovement(id) {
        if (!confirm('هل أنت متأكد من حذف هذه الحركة؟')) return;
        try {
            await axios.delete(`/movements/${id}`);
            this.fetchWarehouseData();
            this.showToast('تم حذف الحركة بنجاح');
        } catch (e) { 
            this.showToast(e.response?.data?.detail || 'خطأ في الحذف', 'error');
        }
    },

    resetMovementForm() {
        this.isEditingMovement = false;
        this.editingMovementId = null;
        this.newMovement = { 
            product_id: '', 
            location_id: '',
            type: 'Addition', 
            quantity: 0, 
            unit_price: 0, 
            date: new Date().toISOString().split('T')[0], 
            notes: '' 
        };
    },

    async addLocation() {
        if(!this.newLocation.name) return;
        try {
            await axios.post('/locations', this.newLocation);
            this.newLocation = { name: '', description: '' };
            this.fetchWarehouseData();
            this.showToast('تم إضافة الموقع بنجاح');
        } catch(e) { 
            this.showToast('خطأ في إضافة الموقع', 'error');
        }
    },

    async deleteLocation(id) {
        if(!confirm('هل أنت متأكد من حذف هذا المخزن؟')) return;
        try {
            await axios.delete(`/locations/${id}`);
            this.fetchWarehouseData();
            this.showToast('تم حذف الموقع بنجاح');
        } catch(e) { 
            this.showToast(e.response?.data?.detail || 'خطأ في الحذف', 'error');
        }
    },

    async createTransfer() {
        if(!this.transferData.product_id || !this.transferData.from_location_id || !this.transferData.to_location_id) {
            alert('يرجى اختيار المنتج والمخازن المراد التحويل بينها');
            return;
        }
        try {
            await axios.post('/transfers', this.transferData);
            this.transferData = { product_id: '', from_location_id: '', to_location_id: '', quantity: 0, date: new Date().toISOString().split('T')[0], notes: '' };
            this.showToast('تم التحويل بنجاح');
            this.fetchWarehouseData();
        } catch(e) { this.showToast('خطأ في عملية التحويل', 'error'); }
    },

    async showMovementHistory(m) {
        try {
            const res = await axios.get(`/audit_logs?t=${Date.now()}`);
            this.activeMovementHistory = res.data.filter(log => log.table_name === 'warehouse_movements' && log.record_id === m.id);
            this.showMovementHistoryModal = true;
        } catch (e) { alert('خطأ في تحميل سجل التعديلات'); }
    },

    async recalculateStock() {
        if (!confirm('سيقوم هذا الإجراء بإعادة حساب أرصدة كافة الأصناف بناءً على سجل الحركات. هل تريد الاستمرار؟')) return;
        try {
            await axios.post('/products/recalculate-stock');
            this.showToast('تم إعادة حساب الأرصدة بنجاح');
            this.fetchWarehouseData();
        } catch (e) { 
            this.showToast('خطأ في العملية', 'error');
        }
    },

    async saveOpeningBalances() {
        const items = this.openingBalances.filter(b => b.qty > 0).map(b => ({
            product_id: b.id,
            quantity: parseFloat(b.qty),
            unit_price: parseFloat(b.price) || 0
        }));
        if (items.length === 0) {
            this.showToast('يرجى إدخال كمية لمنتج واحد على الأقل', 'error');
            return;
        }
        try {
            await axios.post('/inventory/opening-balances', { items });
            this.showToast('تم حفظ الأرصدة بنجاح');
            this.fetchOpeningBalancesData();
        } catch (e) { this.showToast(e.response?.data?.detail || 'خطأ في الحفظ', 'error'); }
    },

    async approveCurrentBalances() {
        if (!confirm('هل تريد اعتماد الأرصدة الحالية كأرصدة افتتاحية؟')) return;
        try {
            await axios.post('/inventory/approve-balances');
            this.showToast('تم اعتماد الأرصدة بنجاح');
            this.fetchOpeningBalancesData();
        } catch (e) { this.showToast(e.response?.data?.detail || 'خطأ في الاعتماد', 'error'); }
    },

    addBulkItem() {
        this.bulkMovements.items.push({ product_id: '', quantity: 1, unit_price: 0, notes: '' });
    },

    removeBulkItem(index) {
        if (this.bulkMovements.items.length > 1) {
            this.bulkMovements.items.splice(index, 1);
        }
    },

    async submitBulkMovements() {
        const isTransfer = this.bulkMovements.type === 'Transfer';

        // Validate based on type
        if (isTransfer) {
            if (!this.bulkMovements.from_location_id || !this.bulkMovements.to_location_id) {
                this.showToast('يرجى اختيار مخزن المصدر ومخزن الوجهة', 'error');
                return;
            }
            if (this.bulkMovements.from_location_id == this.bulkMovements.to_location_id) {
                this.showToast('مخزن المصدر والوجهة لا يمكن أن يكونا نفس المخزن', 'error');
                return;
            }
        } else {
            if (!this.bulkMovements.location_id) {
                this.showToast('يرجى اختيار المخزن', 'error');
                return;
            }
        }

        const validItems = this.bulkMovements.items.filter(item => item.product_id && item.quantity > 0);
        if (validItems.length === 0) {
            this.showToast('يرجى إضافة صنف واحد على الأقل بكمية صحيحة', 'error');
            return;
        }

        try {
            if (isTransfer) {
                await axios.post('/transfers/bulk', {
                    date: this.bulkMovements.date,
                    from_location_id: this.bulkMovements.from_location_id,
                    to_location_id: this.bulkMovements.to_location_id,
                    notes: this.bulkMovements.notes,
                    items: validItems.map(i => ({ product_id: i.product_id, quantity: i.quantity, notes: i.notes }))
                });
            } else {
                await axios.post('/movements/bulk', {
                    date: this.bulkMovements.date,
                    location_id: this.bulkMovements.location_id,
                    type: this.bulkMovements.type,
                    notes: this.bulkMovements.notes,
                    items: validItems
                });
            }

            this.showToast(isTransfer ? 'تم تنفيذ التحويل بنجاح ✅' : 'تم تسجيل الحركات بنجاح ✅');
            this.fetchWarehouseData();
            // Reset items only, keep header settings for convenience
            this.bulkMovements.items = [{ product_id: '', quantity: 1, unit_price: 0, notes: '' }];
        } catch (e) {
            this.showToast(e.response?.data?.detail || 'خطأ في تسجيل الحركات', 'error');
        }
    },

    async importProducts(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        this.showToast('جاري استيراد الأصناف من ملف Excel...', 'info');
        try {
            const res = await axios.post('/products/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            this.showToast(res.data.message || 'تم الاستيراد بنجاح ✅');
            this.fetchWarehouseData();
        } catch (e) {
            this.showToast(e.response?.data?.detail || 'فشل عملية الاستيراد ❌', 'error');
        } finally {
            event.target.value = ''; // Reset for next use
        }
    },

    toggleLowStockFilter() {
        this.showOnlyLowStock = !this.showOnlyLowStock;
        if (this.showOnlyLowStock) {
            this.warehouseView = 'movements'; // Switch to movements tab where the table is
            this.$nextTick(() => {
                const el = document.getElementById('products-inventory-table');
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    this.flashTable = true;
                    setTimeout(() => this.flashTable = false, 2000);
                }
            });
        }
    }
};
