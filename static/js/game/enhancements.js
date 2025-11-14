/**
 * enhancements.js - Sistema completo de melhorias visuais para RPG Fighting Fantasy
 *
 * Features:
 * - Sistema de partículas (ouro/XP)
 * - Combo counter em combates
 * - Gráfico de dano acumulado
 * - Achievement popup animado
 * - Sons de dados configuráveis
 * - Botões de consumíveis contextuais
 */

// ===== CONFIGURAÇÃO DE ÁUDIO =====
class AudioSettings {
    constructor() {
        this.diceSound = localStorage.getItem('dice_sound_enabled') !== 'false'; // Default true
        this.loadSounds();
    }

    loadSounds() {
        this.sounds = {
            diceRoll: new Audio('/static/audio/dice_roll.mp3'),
            diceHit: new Audio('/static/audio/dice_hit.mp3'),
            goldCoin: new Audio('/static/audio/coin.mp3'),
            levelUp: new Audio('/static/audio/level_up.mp3'),
            achievement: new Audio('/static/audio/achievement.mp3'),
            potion: new Audio('/static/audio/potion.mp3'),
            eat: new Audio('/static/audio/eat.mp3'),
            comboHit: new Audio('/static/audio/hit.mp3'),
        };

        // Configurar volume padrão
        Object.values(this.sounds).forEach(sound => {
            sound.volume = 0.5;
            // Configurar para não falhar se arquivo não existir
            sound.addEventListener('error', () => {
                console.warn(`Audio file not found: ${sound.src}`);
            });
        });
    }

    toggle() {
        this.diceSound = !this.diceSound;
        localStorage.setItem('dice_sound_enabled', this.diceSound);
        return this.diceSound;
    }

    play(soundName) {
        if (this.diceSound && this.sounds[soundName]) {
            this.sounds[soundName].currentTime = 0;
            this.sounds[soundName].play().catch(e => console.warn('Audio play failed:', e));
        }
    }
}

const audioSettings = new AudioSettings();

// ===== SISTEMA DE PARTÍCULAS =====
class ParticleSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationId = null;
        this.init();
    }

    init() {
        // Criar canvas se não existir
        this.canvas = document.getElementById('particle-canvas');
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.canvas.id = 'particle-canvas';
            this.canvas.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 9999;
            `;
            document.body.appendChild(this.canvas);
        }

        this.ctx = this.canvas.getContext('2d');
        this.resize();

        window.addEventListener('resize', () => this.resize());
        this.startAnimation();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    emit(x, y, type = 'gold', count = 10) {
        const colors = {
            gold: ['#F59E0B', '#FCD34D', '#FFA500'],
            xp: ['#8B5CF6', '#A78BFA', '#C4B5FD'],
        };

        const emojis = {
            gold: ['💰', '🪙', '✨'],
            xp: ['⭐', '✨', '🌟'],
        };

        for (let i = 0; i < count; i++) {
            this.particles.push({
                x,
                y,
                vx: (Math.random() - 0.5) * 8,
                vy: -Math.random() * 8 - 2,
                life: 1,
                decay: Math.random() * 0.01 + 0.015,
                size: Math.random() * 20 + 15,
                color: colors[type][Math.floor(Math.random() * colors[type].length)],
                emoji: emojis[type][Math.floor(Math.random() * emojis[type].length)],
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.2,
            });
        }
    }

    startAnimation() {
        const animate = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            this.particles = this.particles.filter(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.vy += 0.3; // Gravidade
                p.vx *= 0.98; // Arrasto
                p.life -= p.decay;
                p.rotation += p.rotationSpeed;

                if (p.life <= 0) return false;

                // Desenhar partícula
                this.ctx.save();
                this.ctx.globalAlpha = p.life;
                this.ctx.translate(p.x, p.y);
                this.ctx.rotate(p.rotation);
                this.ctx.font = `${p.size}px Arial`;
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(p.emoji, 0, 0);
                this.ctx.restore();

                return true;
            });

            this.animationId = requestAnimationFrame(animate);
        };

        animate();
    }

    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

const particleSystem = new ParticleSystem();

// ===== COMBO COUNTER =====
class ComboCounter {
    constructor() {
        this.combo = 0;
        this.element = null;
        this.timeout = null;
        this.init();
    }

    init() {
        this.element = document.createElement('div');
        this.element.id = 'combo-counter';
        this.element.style.cssText = `
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            background: linear-gradient(135deg, #F59E0B, #EF4444);
            color: white;
            padding: 20px;
            border-radius: 15px;
            font-size: 2em;
            font-weight: bold;
            box-shadow: 0 10px 30px rgba(239, 68, 68, 0.5);
            display: none;
            text-align: center;
            z-index: 1000;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(this.element);
    }

    increment() {
        this.combo++;
        this.show();
        audioSettings.play('comboHit');

        // Reset timeout
        if (this.timeout) clearTimeout(this.timeout);
        this.timeout = setTimeout(() => this.reset(), 5000);
    }

    reset() {
        this.combo = 0;
        this.hide();
    }

    show() {
        const messages = [
            'HIT!',
            'DOUBLE HIT!',
            'TRIPLE HIT!',
            'COMBO!',
            'MEGA COMBO!',
            'ULTRA COMBO!',
            'GODLIKE!',
        ];

        const message = messages[Math.min(this.combo - 1, messages.length - 1)];

        this.element.innerHTML = `
            <div style="font-size: 3em; margin-bottom: 10px;">${this.combo}x</div>
            <div style="font-size: 0.6em; letter-spacing: 2px;">${message}</div>
        `;

        this.element.style.display = 'block';

        // Animação de shake e scale
        this.element.style.transform = `translateY(-50%) scale(${1 + this.combo * 0.05})`;
        setTimeout(() => {
            this.element.style.transform = 'translateY(-50%) scale(1)';
        }, 200);
    }

    hide() {
        this.element.style.display = 'none';
    }
}

const comboCounter = new ComboCounter();

// ===== GRÁFICO DE DANO =====
class DamageChart {
    constructor() {
        this.playerDamage = 0;
        this.enemyDamage = 0;
        this.element = null;
        this.init();
    }

    init() {
        this.element = document.createElement('div');
        this.element.id = 'damage-chart';
        this.element.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 15, 15, 0.95);
            border: 2px solid #27272A;
            border-radius: 12px;
            padding: 15px;
            display: none;
            width: 90%;
            max-width: 400px;
            z-index: 1000;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        `;
        document.body.appendChild(this.element);
    }

    update(playerDmg, enemyDmg) {
        this.playerDamage += playerDmg;
        this.enemyDamage += enemyDmg;
        this.render();
    }

    render() {
        const total = this.playerDamage + this.enemyDamage || 1;
        const playerPercent = (this.playerDamage / total) * 100;
        const enemyPercent = (this.enemyDamage / total) * 100;

        this.element.innerHTML = `
            <div style="color: #A1A1AA; font-size: 0.75em; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; text-align: center;">
                📊 Dano Acumulado
            </div>
            <div style="display: flex; gap: 10px; margin-bottom: 8px;">
                <div style="flex: 1;">
                    <div style="color: #10B981; font-size: 0.85em; margin-bottom: 5px;">
                        🗡️ Você: ${this.playerDamage}
                    </div>
                    <div style="background: #1A1A1A; border-radius: 8px; overflow: hidden; height: 12px;">
                        <div style="background: linear-gradient(90deg, #10B981, #6366F1); height: 100%; width: ${playerPercent}%; transition: width 0.5s ease;"></div>
                    </div>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <div style="flex: 1;">
                    <div style="color: #EF4444; font-size: 0.85em; margin-bottom: 5px;">
                        👹 Inimigo: ${this.enemyDamage}
                    </div>
                    <div style="background: #1A1A1A; border-radius: 8px; overflow: hidden; height: 12px;">
                        <div style="background: linear-gradient(90deg, #EF4444, #F59E0B); height: 100%; width: ${enemyPercent}%; transition: width 0.5s ease;"></div>
                    </div>
                </div>
            </div>
        `;

        this.element.style.display = 'block';
    }

    reset() {
        this.playerDamage = 0;
        this.enemyDamage = 0;
        this.element.style.display = 'none';
    }

    show() {
        if (this.playerDamage > 0 || this.enemyDamage > 0) {
            this.element.style.display = 'block';
        }
    }

    hide() {
        this.element.style.display = 'none';
    }
}

const damageChart = new DamageChart();

// ===== ACHIEVEMENT POPUP =====
class AchievementPopup {
    constructor() {
        this.queue = [];
        this.isShowing = false;
        this.element = null;
        this.init();
    }

    init() {
        this.element = document.createElement('div');
        this.element.id = 'achievement-popup';
        this.element.style.cssText = `
            position: fixed;
            top: 20px;
            right: -400px;
            width: 350px;
            background: linear-gradient(135deg, #1F2937, #111827);
            border: 2px solid #F59E0B;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 20px 50px rgba(245, 158, 11, 0.3);
            z-index: 10000;
            transition: right 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        document.body.appendChild(this.element);
    }

    show(achievement) {
        this.queue.push(achievement);
        if (!this.isShowing) {
            this.showNext();
        }
    }

    showNext() {
        if (this.queue.length === 0) {
            this.isShowing = false;
            return;
        }

        this.isShowing = true;
        const ach = this.queue.shift();

        this.element.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 3em;">${ach.icon}</div>
                <div style="flex: 1;">
                    <div style="color: #F59E0B; font-size: 0.7em; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; margin-bottom: 5px;">
                        🏆 Conquista Desbloqueada!
                    </div>
                    <div style="color: white; font-weight: bold; font-size: 1.1em; margin-bottom: 5px;">
                        ${ach.name}
                    </div>
                    <div style="color: #A1A1AA; font-size: 0.85em;">
                        ${ach.description}
                    </div>
                    <div style="color: #6366F1; font-size: 0.75em; margin-top: 8px; font-weight: 600;">
                        +${ach.points} XP
                    </div>
                </div>
            </div>
        `;

        // Som de achievement
        audioSettings.play('achievement');

        // Slide in
        setTimeout(() => {
            this.element.style.right = '20px';
        }, 100);

        // Slide out
        setTimeout(() => {
            this.element.style.right = '-400px';
            setTimeout(() => this.showNext(), 500);
        }, 5000);
    }
}

const achievementPopup = new AchievementPopup();

// ===== SISTEMA DE CONSUMÍVEIS =====
class ConsumableButtons {
    constructor() {
        this.container = null;
        this.inCombat = false;
        this.isDead = false;
        this.init();
    }

    init() {
        // Container será injetado no template
        this.container = document.getElementById('consumables-container');
    }

    update(character, flags) {
        if (!this.container) return;

        this.inCombat = flags.in_combat || false;
        this.isDead = character.stamina <= 0;

        const buttons = [];

        // Botão de Rações
        if (character.provisions > 0) {
            const disabled = this.inCombat || this.isDead || character.stamina >= character.initial_stamina;
            buttons.push(this.createButton(
                '🥖',
                `Ração (${character.provisions})`,
                'eat_provision',
                disabled,
                disabled ? 'Só pode usar fora de combate e se ferido' : 'Restaura 4 de ENERGIA'
            ));
        }

        // Botões de Poções
        const potions = [
            { key: 'potion1', type: character.potion1 },
            { key: 'potion2', type: character.potion2 }
        ];

        potions.forEach(({ key, type }) => {
            if (type) {
                const config = this.getPotionConfig(type);
                const disabled = this.inCombat || this.isDead;
                buttons.push(this.createButton(
                    config.icon,
                    config.name,
                    `use_${key}`,
                    disabled,
                    disabled ? 'Só pode usar fora de combate' : config.description
                ));
            }
        });

        this.container.innerHTML = buttons.join('');
        this.attachHandlers();
    }

    getPotionConfig(type) {
        const configs = {
            luck: { icon: '🍀', name: 'Poção de Sorte', description: '+1 SORTE (max inicial)' },
            skill: { icon: '⚔️', name: 'Poção de Habilidade', description: '+1 HABILIDADE (max inicial)' },
            stamina: { icon: '❤️', name: 'Poção de Energia', description: '+4 ENERGIA (max inicial)' },
        };
        return configs[type] || configs.stamina;
    }

    createButton(icon, label, action, disabled, tooltip) {
        const disabledClass = disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 hover:shadow-lg';
        const disabledAttr = disabled ? 'disabled' : '';

        return `
            <button
                class="consumable-btn flex items-center gap-2 px-4 py-3 rounded-lg font-semibold text-sm transition-all ${disabledClass}"
                style="background: ${disabled ? '#27272A' : 'linear-gradient(135deg, #6366F1, #8B5CF6)'}; color: white; border: 2px solid ${disabled ? '#3F3F46' : '#6366F1'};"
                data-action="${action}"
                ${disabledAttr}
                title="${tooltip}"
            >
                <span style="font-size: 1.5em;">${icon}</span>
                <span>${label}</span>
            </button>
        `;
    }

    attachHandlers() {
        const buttons = this.container.querySelectorAll('.consumable-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                if (!btn.disabled) {
                    const action = btn.getAttribute('data-action');
                    this.handleConsumable(action);
                }
            });
        });
    }

    async handleConsumable(action) {
        console.log('Consumable action:', action);

        // Tocar som apropriado
        if (action === 'eat_provision') {
            audioSettings.play('eat');
        } else {
            audioSettings.play('potion');
        }

        // Enviar ação ao servidor
        if (window.sendAction) {
            await window.sendAction(action);
        }
    }
}

const consumableButtons = new ConsumableButtons();

// ===== TOGGLE DE ÁUDIO =====
function createAudioToggle() {
    const toggle = document.createElement('button');
    toggle.id = 'audio-toggle';
    toggle.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border: 2px solid #6366F1;
        color: white;
        font-size: 1.5em;
        cursor: pointer;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;

    toggle.innerHTML = audioSettings.diceSound ? '🔊' : '🔇';

    toggle.addEventListener('click', () => {
        const enabled = audioSettings.toggle();
        toggle.innerHTML = enabled ? '🔊' : '🔇';
        toggle.style.transform = 'scale(1.2)';
        setTimeout(() => {
            toggle.style.transform = 'scale(1)';
        }, 200);
    });

    document.body.appendChild(toggle);
}

// ===== INTEGRAÇÃO COM EVENTOS DO JOGO =====
window.gameEnhancements = {
    // Atualizar stats com partículas
    updateStatsWithParticles(stats, oldStats) {
        const statElements = {
            gold: document.getElementById('stat-gold'),
            stamina: document.getElementById('stat-stamina'),
        };

        // Ouro
        if (stats.gold > oldStats.gold && statElements.gold) {
            const rect = statElements.gold.getBoundingClientRect();
            particleSystem.emit(rect.left + rect.width / 2, rect.top + rect.height / 2, 'gold', 15);
            audioSettings.play('goldCoin');
        }

        // XP (achievement)
        // Será chamado quando achievement for desbloqueado
    },

    // Atualizar combate
    updateCombat(combatData) {
        if (!combatData) {
            damageChart.hide();
            comboCounter.reset();
            return;
        }

        // Atualizar gráfico de dano
        if (combatData.player_damage) {
            damageChart.update(combatData.player_damage, 0);
            comboCounter.increment();
        }

        if (combatData.enemy_damage) {
            damageChart.update(0, combatData.enemy_damage);
            comboCounter.reset();
        }

        damageChart.show();
    },

    // Notificar achievement
    notifyAchievement(achievement) {
        achievementPopup.show(achievement);

        // Partículas no centro da tela
        particleSystem.emit(window.innerWidth / 2, window.innerHeight / 2, 'xp', 30);
    },

    // Atualizar consumíveis
    updateConsumables(character, flags) {
        consumableButtons.update(character, flags);
    },

    // Inicializar
    init() {
        createAudioToggle();
        console.log('🎮 Game Enhancements carregado com sucesso!');
    }
};

// Inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.gameEnhancements.init();
    });
} else {
    window.gameEnhancements.init();
}
