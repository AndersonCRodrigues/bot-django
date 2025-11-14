class FileUploader {
    constructor(options = {}) {
        this.dropZone = options.dropZone;
        this.fileInput = options.fileInput;
        this.previewArea = options.previewArea;

        const acceptAttr = this.dropZone?.getAttribute('data-accept');
        this.acceptType = acceptAttr || 'application/pdf';
        this.maxSize = options.maxSize || 50 * 1024 * 1024;

        this.init();
    }

    init() {
        if (!this.dropZone || !this.fileInput) return;

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

    isFileTypeAccepted(fileType) {
        if (this.acceptType === 'image/*') {
            return fileType.startsWith('image/');
        }

        if (this.acceptType === 'application/pdf') {
            return fileType === 'application/pdf';
        }

        return fileType === this.acceptType;
    }

    handleFiles(files) {
        const file = files[0];

        if (!file) return;

        if (!this.isFileTypeAccepted(file.type)) {
            this.showError('Tipo de arquivo não permitido.');
            return;
        }

        if (file.size > this.maxSize) {
            this.showError(`Arquivo muito grande. Máximo: ${Math.round(this.maxSize / 1024 / 1024)}MB`);
            return;
        }

        this.showPreview(file);
    }

    showPreview(file) {
        if (!this.previewArea) return;

        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);
        const icon = file.type.startsWith('image/') ? '🖼️' : '📄';

        this.previewArea.innerHTML = `
            <div class="flex items-center justify-between p-4 bg-[#1A1A1A] rounded-lg border border-[#27272A]">
                <div class="flex items-center space-x-3">
                    <div class="w-12 h-12 bg-[#6366F1] bg-opacity-10 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">${icon}</span>
                    </div>
                    <div>
                        <p class="font-medium text-white">${file.name}</p>
                        <p class="text-sm text-[#71717A]">${sizeInMB} MB</p>
                    </div>
                </div>
                <button type="button" onclick="this.closest('.file-uploader').querySelector('input[type=file]').value=''; this.parentElement.parentElement.classList.add('hidden');" class="text-[#DC2626] hover:text-[#EF4444]">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `;

        this.previewArea.classList.remove('hidden');
    }

    showError(message) {
        alert(message);
    }
}

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