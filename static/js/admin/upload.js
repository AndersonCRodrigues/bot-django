/**
 * Upload.js - Drag & Drop para upload de arquivos
 */

class FileUploader {
    constructor(options = {}) {
        this.dropZone = options.dropZone;
        this.fileInput = options.fileInput;
        this.previewArea = options.previewArea;
        this.allowedTypes = options.allowedTypes || ['application/pdf'];
        this.maxSize = options.maxSize || 50 * 1024 * 1024; // 50MB

        this.init();
    }

    init() {
        if (!this.dropZone || !this.fileInput) return;

        // Drag & Drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.highlight(), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.unhighlight(), false);
        });

        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);

        // Click to upload
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight() {
        this.dropZone.classList.add('border-[#6366F1]', 'bg-[#6366F1]', 'bg-opacity-5');
    }

    unhighlight() {
        this.dropZone.classList.remove('border-[#6366F1]', 'bg-[#6366F1]', 'bg-opacity-5');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    handleFiles(files) {
        const file = files[0];

        if (!file) return;

        // Validações
        if (!this.allowedTypes.includes(file.type)) {
            this.showError('Tipo de arquivo não permitido. Apenas PDF.');
            return;
        }

        if (file.size > this.maxSize) {
            this.showError(`Arquivo muito grande. Máximo: ${this.maxSize / 1024 / 1024}MB`);
            return;
        }

        // Preview
        this.showPreview(file);
    }

    showPreview(file) {
        if (!this.previewArea) return;

        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);

        this.previewArea.innerHTML = `
            <div class="flex items-center justify-between p-4 bg-[#1A1A1A] rounded-lg border border-[#27272A]">
                <div class="flex items-center space-x-3">
                    <div class="w-12 h-12 bg-[#DC2626] bg-opacity-10 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">📄</span>
                    </div>
                    <div>
                        <p class="font-medium text-white">${file.name}</p>
                        <p class="text-sm text-[#71717A]">${sizeInMB} MB</p>
                    </div>
                </div>
                <button type="button" onclick="this.closest('.file-uploader').querySelector('input[type=file]').value=''; this.closest('div').remove();" class="text-[#DC2626] hover:text-[#EF4444]">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `;

        this.previewArea.classList.remove('hidden');
    }

    showError(message) {
        alert(message); // Pode ser melhorado com toast notification
    }
}

// Auto-init para classe .file-uploader
document.addEventListener('DOMContentLoaded', () => {
    const uploaders = document.querySelectorAll('.file-uploader');

    uploaders.forEach(uploader => {
        const dropZone = uploader.querySelector('[data-dropzone]');
        const fileInput = uploader.querySelector('input[type="file"]');
        const previewArea = uploader.querySelector('[data-preview]');

        if (dropZone && fileInput) {
            new FileUploader({
                dropZone,
                fileInput,
                previewArea
            });
        }
    });
});

window.FileUploader = FileUploader;