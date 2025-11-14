/**
 * gameplay.js - Lógica principal do jogo RPG Fighting Fantasy
 *
 * Gerencia:
 * - Envio de ações via AJAX
 * - Atualização da UI (narrativa, stats, inventário)
 * - Comunicação com o servidor
 * - Integração com animação de dados
 */

class GameplayManager {
    constructor(sessionId, csrfToken) {
        this.sessionId = sessionId;
        this.csrfToken = csrfToken;
        this.isProcessing = false;

        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Form e inputs
        this.form = document.getElementById('action-form');
        this.input = document.getElementById('action-input');
        this.submitBtn = document.getElementById('action-btn');

        // Áreas de conteúdo
        this.narrativeArea = document.getElementById('narrative-area');
        this.loadingIndicator = document.getElementById('loading-indicator');

        // Stats
        this.skillValue = document.getElementById('skill-value');
        this.staminaValue = document.getElementById('stamina-value');
        this.luckValue = document.getElementById('luck-value');
        this.goldValue = document.getElementById('gold-value');
        this.provisionsValue = document.getElementById('provisions-value');

        // Barras de progresso
        this.staminaBar = document.getElementById('stamina-bar');
        this.luckBar = document.getElementById('luck-bar');

        // Inventário
        this.inventoryList = document.getElementById('inventory-list');

        // Seção atual
        this.currentSection = document.getElementById('current-section');
    }

    attachEventListeners() {
        // Submit do formulário
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAction();
        });

        // Enter no input
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleAction();
            }
        });

        // Auto-save a cada 5 minutos
        setInterval(() => this.autoSave(), 5 * 60 * 1000);
    }

    async handleAction() {
        if (this.isProcessing) return;

        const action = this.input.value.trim();

        if (!action) {
            this.showError('Por favor, insira uma ação.');
            return;
        }

        // Adicionar ação do jogador à narrativa imediatamente
        this.addPlayerMessage(action);

        // Limpar input
        this.input.value = '';

        // Mostrar loading
        this.setProcessing(true);

        try {
            const result = await this.sendAction(action);
            await this.handleResponse(result);
        } catch (error) {
            console.error('Erro ao processar ação:', error);
            this.showError('Erro ao processar ação. Tente novamente.');
        } finally {
            this.setProcessing(false);
        }
    }

    async sendAction(action) {
        const response = await fetch(`/game/play/${this.sessionId}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.csrfToken,
            },
            body: `action=${encodeURIComponent(action)}`,
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        return await response.json();
    }

    async handleResponse(result) {
        if (!result.success) {
            this.showError(result.error || 'Erro desconhecido');
            return;
        }

        // Verificar se precisa rolar dados (detecção heurística)
        const needsDiceRoll = this.checkIfNeedsDiceRoll(result.narrative);

        if (needsDiceRoll && window.DiceAnimator) {
            // Mostrar animação de dados
            await this.showDiceAnimation();
        }

        // Adicionar resposta do narrador
        this.addNarratorMessage(result.narrative);

        // Atualizar stats
        this.updateStats(result.stats);

        // Atualizar inventário
        if (result.inventory) {
            this.updateInventory(result.inventory);
        }

        // Atualizar seção
        if (result.current_section) {
            this.updateSection(result.current_section);
        }

        // Verificar game over
        if (result.game_over || result.victory) {
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }

        // Auto-scroll
        this.scrollToBottom();
    }

    checkIfNeedsDiceRoll(narrative) {
        const diceKeywords = [
            'rolar',
            'rolou',
            'dados',
            '2d6',
            'd6',
            'teste',
            'sorte',
            'habilidade',
            'combate'
        ];

        const lowerNarrative = narrative.toLowerCase();
        return diceKeywords.some(keyword => lowerNarrative.includes(keyword));
    }

    async showDiceAnimation() {
        // Integração com dice.js
        if (window.DiceAnimator) {
            return new Promise((resolve) => {
                const diceAnimator = new DiceAnimator();
                diceAnimator.roll(2, 6, (result) => {
                    resolve(result);
                });
            });
        }
    }

    addPlayerMessage(text) {
        const entry = document.createElement('div');
        entry.className = 'narrative-entry player';
        entry.innerHTML = `
            <div class="narrative-label">Você</div>
            <div class="narrative-text">${this.escapeHtml(text)}</div>
        `;
        this.narrativeArea.appendChild(entry);
        this.scrollToBottom();
    }

    addNarratorMessage(text) {
        const entry = document.createElement('div');
        entry.className = 'narrative-entry narrator';
        entry.innerHTML = `
            <div class="narrative-label">Narrador</div>
            <div class="narrative-text">${this.escapeHtml(text)}</div>
        `;
        this.narrativeArea.appendChild(entry);
        this.scrollToBottom();
    }

    showError(message) {
        const entry = document.createElement('div');
        entry.className = 'narrative-entry';
        entry.style.background = 'rgba(239, 68, 68, 0.1)';
        entry.style.borderLeft = '4px solid #ef4444';
        entry.innerHTML = `
            <div class="narrative-label" style="color: #ef4444;">Erro</div>
            <div class="narrative-text">${this.escapeHtml(message)}</div>
        `;
        this.narrativeArea.appendChild(entry);
        this.scrollToBottom();
    }

    updateStats(stats) {
        if (!stats) return;

        // Skill
        if (stats.skill !== undefined) {
            this.animateNumber(this.skillValue, stats.skill);
        }

        // Stamina
        if (stats.stamina !== undefined) {
            this.animateNumber(this.staminaValue, stats.stamina);

            // Atualizar barra
            const maxStamina = parseInt(this.staminaBar.parentElement.nextElementSibling.textContent.split(': ')[1]);
            const percentage = (stats.stamina / maxStamina) * 100;
            this.staminaBar.style.width = `${percentage}%`;

            // Mudar cor se crítico
            if (stats.stamina < 5) {
                this.staminaBar.classList.add('low');
            } else {
                this.staminaBar.classList.remove('low');
            }
        }

        // Luck
        if (stats.luck !== undefined) {
            this.animateNumber(this.luckValue, stats.luck);

            // Atualizar barra (assumindo max luck similar)
            const maxLuck = parseInt(this.luckBar.parentElement.nextElementSibling.textContent.split(': ')[1]);
            const percentage = (stats.luck / maxLuck) * 100;
            this.luckBar.style.width = `${percentage}%`;
        }

        // Gold
        if (stats.gold !== undefined) {
            this.animateNumber(this.goldValue, stats.gold);
        }

        // Provisions
        if (stats.provisions !== undefined) {
            this.animateNumber(this.provisionsValue, stats.provisions);
        }
    }

    updateInventory(items) {
        this.inventoryList.innerHTML = '';

        if (items.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'inventory-item';
            emptyItem.style.opacity = '0.5';
            emptyItem.textContent = 'Vazio';
            this.inventoryList.appendChild(emptyItem);
        } else {
            items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'inventory-item';
                itemDiv.textContent = item;
                this.inventoryList.appendChild(itemDiv);
            });
        }
    }

    updateSection(section) {
        this.currentSection.textContent = section;
    }

    animateNumber(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const step = (targetValue - currentValue) / 20;
        let current = currentValue;

        const animate = () => {
            current += step;

            if ((step > 0 && current >= targetValue) || (step < 0 && current <= targetValue)) {
                element.textContent = targetValue;
                return;
            }

            element.textContent = Math.round(current);
            requestAnimationFrame(animate);
        };

        animate();
    }

    setProcessing(isProcessing) {
        this.isProcessing = isProcessing;
        this.submitBtn.disabled = isProcessing;
        this.input.disabled = isProcessing;

        if (isProcessing) {
            this.loadingIndicator.classList.add('active');
        } else {
            this.loadingIndicator.classList.remove('active');
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.narrativeArea.scrollTop = this.narrativeArea.scrollHeight;
        }, 100);
    }

    async autoSave() {
        try {
            const response = await fetch(`/game/play/${this.sessionId}/save/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                },
            });

            const data = await response.json();

            if (data.success) {
                console.log('Auto-save realizado com sucesso');
            }
        } catch (error) {
            console.error('Erro no auto-save:', error);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Função global para quick actions
window.setAction = function(text) {
    const input = document.getElementById('action-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    if (typeof sessionId !== 'undefined' && typeof csrfToken !== 'undefined') {
        window.gameplayManager = new GameplayManager(sessionId, csrfToken);
        console.log('GameplayManager inicializado');
    }
});
