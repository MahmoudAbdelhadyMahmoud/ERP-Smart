window.appUtils = {
    locName(item, fallbackKey = null) {
        if (!item) return fallbackKey ? this.t(fallbackKey) : '';
        const lang = this.lang || window.appLang || 'ar';
        if (lang === 'zh' && item.name_chinese) return item.name_chinese;
        if (lang === 'en' && item.name_en) return item.name_en;
        return item.name || (fallbackKey ? this.t(fallbackKey) : '');
    },

    locDesc(item, fallbackKey = null) {
        if (!item) return fallbackKey ? this.t(fallbackKey) : '';
        const lang = this.lang || window.appLang || 'ar';
        if (lang === 'zh' && (item.description_chinese || item.name_chinese)) return item.description_chinese || item.name_chinese;
        if (lang === 'en' && item.description_en) return item.description_en;
        return item.description || (fallbackKey ? this.t(fallbackKey) : '');
    },

    showToast(message, type = 'success') {
        const id = Date.now();
        this.notifications.push({ id, message, type });
        setTimeout(() => {
            this.notifications = this.notifications.filter(n => n.id !== id);
        }, 3000);
    },

    formatMoney(val) {
        return new Intl.NumberFormat('ar-EG', { minimumFractionDigits: 2 }).format(val);
    },

    exportData(type, id = null) {
        this.showToast('جاري تحضير ملف ' + type.toUpperCase() + '...', 'info');
        if (id) {
            window.location.href = `/export/invoice/${id}/${type}`;
        } else {
            window.location.href = `/export/${type}`;
        }
    },

    calculateTotal() {
        this.totalSum = this.filteredExpenses.reduce((acc, curr) => acc + curr.total, 0);
    },

    async translateText(text, callback) {
        if (!text || text.length < 2) return;
        try {
            const res = await axios.post('/translate', { notes: text, amount: 0 }); // Reusing RecommendationRequest schema
            if (res.data) {
                callback(res.data);
            }
        } catch (e) {
            console.error('Translation error:', e);
        }
    }
};
