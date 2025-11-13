/**
 * Utils.js - Utilitários gerais
 */

// Format numbers
function formatNumber(num) {
    return new Intl.NumberFormat('pt-BR').format(num);
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Format date
function formatDate(date) {
    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast notification
class Toast {
    static show(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 fade-in px-6 py-4 rounded-lg shadow-lg ${this.getTypeClass(type)}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    static getTypeClass(type) {
        const classes = {
            success: 'bg-[#16A34A] text-white',
            error: 'bg-[#DC2626] text-white',
            warning: 'bg-[#F59E0B] text-white',
            info: 'bg-[#2563EB] text-white'
        };
        return classes[type] || classes.info;
    }
}

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.show('Copiado para área de transferência!', 'success');
    } catch (err) {
        Toast.show('Erro ao copiar', 'error');
    }
}

// Export
window.utils = {
    formatNumber,
    formatCurrency,
    formatDate,
    debounce,
    Toast,
    confirmAction,
    copyToClipboard
};