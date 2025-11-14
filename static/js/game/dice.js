/**
 * dice.js - Animação 3D de rolagem de dados
 *
 * Implementa animação realista de dados usando CSS 3D transforms
 * Inspirado em livros-jogo Fighting Fantasy (2d6)
 */

class DiceAnimator {
    constructor() {
        this.overlay = null;
        this.container = null;
        this.isRolling = false;
    }

    /**
     * Rola N dados de D faces
     * @param {number} count - Número de dados
     * @param {number} faces - Número de faces (6 padrão)
     * @param {function} callback - Callback com resultado
     */
    roll(count = 2, faces = 6, callback = null) {
        if (this.isRolling) return;

        this.isRolling = true;

        // Criar overlay se não existir
        if (!this.overlay) {
            this.createOverlay();
        }

        // Mostrar overlay
        this.overlay.classList.add('active');

        // Rolar dados
        const results = [];
        for (let i = 0; i < count; i++) {
            const result = Math.floor(Math.random() * faces) + 1;
            results.push(result);
        }

        const total = results.reduce((a, b) => a + b, 0);

        // Renderizar dados
        this.renderDice(count, results);

        // Após animação, mostrar resultado
        setTimeout(() => {
            this.showResult(total, results);

            // Fechar após delay
            setTimeout(() => {
                this.close();
                this.isRolling = false;

                if (callback) {
                    callback({ total, rolls: results });
                }
            }, 2000);
        }, 2000);
    }

    createOverlay() {
        this.overlay = document.getElementById('dice-overlay');

        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = 'dice-overlay';
            document.body.appendChild(this.overlay);
        }

        this.container = document.createElement('div');
        this.container.id = 'dice-container';
        this.overlay.appendChild(this.container);

        this.resultDiv = document.createElement('div');
        this.resultDiv.className = 'dice-result';
        this.overlay.appendChild(this.resultDiv);
    }

    renderDice(count, results) {
        this.container.innerHTML = '';
        this.resultDiv.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.style.display = 'flex';
        wrapper.style.gap = '30px';
        wrapper.style.justifyContent = 'center';

        for (let i = 0; i < count; i++) {
            const dice = this.createDice(results[i]);
            wrapper.appendChild(dice);
        }

        this.container.appendChild(wrapper);
    }

    createDice(result) {
        const dice = document.createElement('div');
        dice.className = 'dice';

        // Calcular rotação final baseada no resultado
        const rotations = this.getRotationForFace(result);
        dice.style.setProperty('--final-x', `${rotations.x}deg`);
        dice.style.setProperty('--final-y', `${rotations.y}deg`);

        // Criar faces do dado (cubo 3D)
        const faces = [
            { value: 1, transform: 'rotateY(0deg) translateZ(50px)' },
            { value: 6, transform: 'rotateY(180deg) translateZ(50px)' },
            { value: 2, transform: 'rotateY(90deg) translateZ(50px)' },
            { value: 5, transform: 'rotateY(-90deg) translateZ(50px)' },
            { value: 3, transform: 'rotateX(90deg) translateZ(50px)' },
            { value: 4, transform: 'rotateX(-90deg) translateZ(50px)' },
        ];

        faces.forEach(face => {
            const faceDiv = document.createElement('div');
            faceDiv.className = 'dice-face';
            faceDiv.style.transform = face.transform;
            faceDiv.appendChild(this.createDots(face.value));
            dice.appendChild(faceDiv);
        });

        return dice;
    }

    createDots(value) {
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'dice-dots';

        // Configuração de pontos para cada face
        const dotPatterns = {
            1: ['g'],
            2: ['a', 'b'],
            3: ['a', 'g', 'b'],
            4: ['a', 'c', 'd', 'b'],
            5: ['a', 'c', 'g', 'd', 'b'],
            6: ['a', 'c', 'e', 'f', 'd', 'b'],
        };

        const positions = dotPatterns[value] || [];

        // Criar grid 3x3
        for (let i = 0; i < 9; i++) {
            const cell = document.createElement('div');
            const posName = ['a', 'e', 'c', 'e', 'g', 'e', 'd', 'f', 'b'][i];

            if (positions.includes(posName)) {
                const dot = document.createElement('div');
                dot.className = 'dot';
                cell.appendChild(dot);
            }

            dotsContainer.appendChild(cell);
        }

        return dotsContainer;
    }

    getRotationForFace(face) {
        // Rotações para mostrar cada face
        const rotations = {
            1: { x: 0, y: 0 },
            2: { x: 0, y: 90 },
            3: { x: 90, y: 0 },
            4: { x: -90, y: 0 },
            5: { x: 0, y: -90 },
            6: { x: 0, y: 180 },
        };

        return rotations[face] || { x: 0, y: 0 };
    }

    showResult(total, rolls) {
        const rollsText = rolls.map((r, i) => `Dado ${i + 1}: ${r}`).join(' | ');

        this.resultDiv.innerHTML = `
            <div style="font-size: 3em; color: #f59e0b; font-weight: bold; margin-bottom: 15px;">
                ${total}
            </div>
            <div style="font-size: 1.2em; color: #cbd5e1;">
                ${rollsText}
            </div>
        `;
    }

    close() {
        if (this.overlay) {
            this.overlay.classList.remove('active');
        }
    }
}

// Criar instância global
window.DiceAnimator = DiceAnimator;

// Função helper para rolar dados simples
window.rollDice = function(count = 2, faces = 6, callback = null) {
    const animator = new DiceAnimator();
    animator.roll(count, faces, callback);
};

// Exemplo de uso no console:
// rollDice(2, 6, (result) => console.log('Resultado:', result.total));
