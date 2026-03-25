window.appCosting = {
    costingTab: 'recipes', // 'recipes' or 'produce'
    recipes: [],
    
    // UI states
    recipeModalOpen: false,
    recipeDetailsModalOpen: false,
    selectedRecipe: null,
    isProducing: false,
    isEditingRecipe: false,
    editingRecipeId: null,

    // Forms
    recipeForm: {
        name: '',
        name_chinese: '',
        product_id: '',
        base_quantity: 1,
        labor_cost: 0,
        overhead_cost: 0,
        gas_cost: 0,
        electricity_cost: 0,
        water_cost: 0,
        rent_cost: 0,
        marketing_cost: 0,
        ad_cost: 0,
        admin_cost: 0,
        taxes: 0,
        import_costs: 0,
        other_costs: 0,
        selling_price: 0,
        items: []
    },
    
    productionForm: {
        recipe_id: '',
        quantity: 1
    },

    async fetchRecipes() {
        try {
            const res = await axios.get(`/costing/recipes`);
            this.recipes = res.data;
        } catch (err) {
            console.error(err);
            this.showToast('خطأ في جلب بيانات التصنيع', 'error');
        }
    },

    openRecipeModal() {
        this.isEditingRecipe = false;
        this.editingRecipeId = null;
        this.recipeForm = {
            name: '',
            name_chinese: '',
            product_id: '',
            base_quantity: 1,
            labor_cost: 0,
            overhead_cost: 0,
            gas_cost: 0,
            electricity_cost: 0,
            water_cost: 0,
            rent_cost: 0,
            marketing_cost: 0,
            ad_cost: 0,
            admin_cost: 0,
            taxes: 0,
            import_costs: 0,
            other_costs: 0,
            selling_price: 0,
            items: []
        };
        this.addRecipeItem(); // Add one row by default
        this.recipeModalOpen = true;
    },

    editRecipe(recipe) {
        this.isEditingRecipe = true;
        this.editingRecipeId = recipe.id;
        this.recipeForm = {
            name: recipe.name,
            name_chinese: recipe.name_chinese || '',
            product_id: recipe.product_id,
            base_quantity: recipe.base_quantity,
            labor_cost: recipe.labor_cost,
            overhead_cost: recipe.overhead_cost,
            gas_cost: recipe.gas_cost || 0,
            electricity_cost: recipe.electricity_cost || 0,
            water_cost: recipe.water_cost || 0,
            rent_cost: recipe.rent_cost || 0,
            marketing_cost: recipe.marketing_cost || 0,
            ad_cost: recipe.ad_cost || 0,
            admin_cost: recipe.admin_cost || 0,
            taxes: recipe.taxes,
            import_costs: recipe.import_costs,
            other_costs: recipe.other_costs,
            selling_price: recipe.selling_price || 0,
            items: recipe.items.map(i => ({
                material_product_id: i.material_product_id,
                quantity: i.quantity,
                waste_pct: i.waste_pct
            }))
        };
        this.recipeModalOpen = true;
    },

    async deleteRecipe(recipeId) {
        if (!confirm('هل أنت متأكد من حذف هذه الوصفة نهائياً؟')) return;
        try {
            await axios.delete(`/costing/recipes/${recipeId}`);
            this.showToast('تم حذف الوصفة بنجاح');
            this.fetchRecipes();
        } catch (err) {
            this.showToast(err.response?.data?.detail || 'خطأ في الحذف', 'error');
        }
    },

    addRecipeItem() {
        this.recipeForm.items.push({
            material_product_id: '',
            quantity: 1,
            waste_pct: 0
        });
    },

    removeRecipeItem(index) {
        this.recipeForm.items.splice(index, 1);
    },

    async submitRecipe() {
        // Validation
        if (!this.recipeForm.product_id) {
            this.showToast('❌ يرجى اختيار المنتج النهائي المرتبط بهذه القاعدة', 'error');
            return;
        }
        if (!this.recipeForm.name || this.recipeForm.name.trim().length < 2) {
            this.showToast('❌ يرجى إدخال اسم صحيح لقاعدة التصنيع', 'error');
            return;
        }
        if (parseFloat(this.recipeForm.base_quantity || 0) <= 0) {
            this.showToast('❌ يجب أن تكون الكمية الناتجة في الطبخة أكبر من صفر', 'error');
            return;
        }
        if (this.recipeForm.items.length === 0) {
            this.showToast('❌ يجب إضافة مكون واحد (خامة) على الأقل للطبخة', 'error');
            return;
        }

        // Detailed Items Validation
        for (let i = 0; i < this.recipeForm.items.length; i++) {
            const item = this.recipeForm.items[i];
            if (!item.material_product_id) {
                this.showToast(`⚠️ السطر رقم ${i+1}: يرجى اختيار الخامة المطلوبة`, 'error');
                return;
            }
            if (parseFloat(item.quantity || 0) <= 0) {
                this.showToast(`⚠️ السطر رقم ${i+1}: يرجى تحديد كمية الخامة (يجب أن تكون أكبر من صفر)`, 'error');
                return;
            }
        }
        
        try {
            const payload = {
                ...this.recipeForm,
                product_id: parseInt(this.recipeForm.product_id),
                base_quantity: parseFloat(this.recipeForm.base_quantity),
                labor_cost: parseFloat(this.recipeForm.labor_cost || 0),
                overhead_cost: parseFloat(this.recipeForm.overhead_cost || 0),
                gas_cost: parseFloat(this.recipeForm.gas_cost || 0),
                electricity_cost: parseFloat(this.recipeForm.electricity_cost || 0),
                water_cost: parseFloat(this.recipeForm.water_cost || 0),
                rent_cost: parseFloat(this.recipeForm.rent_cost || 0),
                marketing_cost: parseFloat(this.recipeForm.marketing_cost || 0),
                ad_cost: parseFloat(this.recipeForm.ad_cost || 0),
                admin_cost: parseFloat(this.recipeForm.admin_cost || 0),
                taxes: parseFloat(this.recipeForm.taxes || 0),
                import_costs: parseFloat(this.recipeForm.import_costs || 0),
                other_costs: parseFloat(this.recipeForm.other_costs || 0),
                selling_price: parseFloat(this.recipeForm.selling_price || 0),
                items: this.recipeForm.items.map(i => ({
                    ...i,
                    material_product_id: parseInt(i.material_product_id),
                    quantity: parseFloat(i.quantity),
                    waste_pct: parseFloat(i.waste_pct || 0)
                }))
            };

            if (this.isEditingRecipe) {
                await axios.put(`/costing/recipes/${this.editingRecipeId}`, payload);
            } else {
                await axios.post(`/costing/recipes`, payload);
            }

            this.showToast(this.isEditingRecipe ? 'تم التحديث بنجاح' : 'تم حفظ القاعدة بنجاح!', 'success');
            this.recipeModalOpen = false;
            await this.fetchRecipes();
        } catch (err) {
            console.error(err);
            this.showToast('خطأ اثناء حفظ القاعدة', 'error');
        }
    },

    viewRecipeDetails(recipe) {
        this.selectedRecipe = recipe;
        this.recipeDetailsModalOpen = true;
    },

    async submitProduction() {
        if (!this.productionForm.recipe_id) {
            this.showToast('❌ يرجى اختيار قاعدة التصنيع (الريسيبي) أولاً', 'error');
            return;
        }
        if (parseFloat(this.productionForm.quantity || 0) <= 0) {
            this.showToast('❌ يرجى إدخال الكمية المطلوب إنتاجها (يجب أن تكون أكبر من صفر)', 'error');
            return;
        }

        if(!confirm(`هل أنت متأكد من تنفيذ أمر التصنيع؟ سيتم سحب المواد الخام وإدخال المنتج النهائي للمخزن!`)) return;

        this.isProducing = true;
        try {
            const url = `/costing/recipes/${this.productionForm.recipe_id}/produce?quantity=${this.productionForm.quantity}`;
            const res = await axios.post(url);
            
            this.showToast(`تم التصنيع بنجاح! التكلفة الاجمالية: ${this.formatMoney(res.data.total_cost)}`, 'success', 5000);
            this.productionForm = { recipe_id: '', quantity: 1 };
            
            // Refresh overall data (inventory balances)
            await this.fetchData();
        } catch (err) {
            console.error(err);
            this.showToast(err.response?.data?.detail || 'حدث خطأ غير متوقع اثناء التصنيع', 'error');
        } finally {
            this.isProducing = false;
        }
    },

    getRecipeSummary() {
        const f = this.recipeForm;
        
        // 1. Material Costs
        let matCost = 0;
        f.items.forEach(item => {
            const p = this.products.find(x => x.id == item.material_product_id);
            if (p) {
                const qty = parseFloat(item.quantity) || 0;
                const waste = 1 + (parseFloat(item.waste_pct) || 0) / 100;
                matCost += p.average_cost * qty * waste;
            }
        });

        // 2. Expense Costs
        const expFields = [
            'labor_cost', 'overhead_cost', 'gas_cost', 'electricity_cost', 
            'water_cost', 'rent_cost', 'marketing_cost', 'ad_cost', 
            'admin_cost', 'taxes', 'import_costs', 'other_costs'
        ];
        let expCost = 0;
        expFields.forEach(field => {
            expCost += parseFloat(f[field]) || 0;
        });

        const totalCost = matCost + expCost;
        const baseQty = parseFloat(f.base_quantity) || 1;
        const costPerUnit = totalCost / (baseQty || 1);
        const sellPrice = parseFloat(f.selling_price) || 0;
        const profit = sellPrice - costPerUnit;
        const margin = sellPrice > 0 ? (profit / sellPrice) * 100 : 0;

        return {
            matCost,
            expCost,
            totalCost,
            costPerUnit,
            profit,
            margin
        };
    }
};
