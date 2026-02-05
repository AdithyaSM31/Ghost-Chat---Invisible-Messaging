// Tab Switching
function switchTab(tabId) {
    // Buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Panels
    document.querySelectorAll('.panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
}

// Drag and Drop & File Input Handling
function setupFileUpload(dropAreaId, inputName, previewId) {
    const dropArea = document.getElementById(dropAreaId);
    const input = dropArea.querySelector('input');
    const preview = document.getElementById(previewId);

    // Drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'), false);
    });

    dropArea.addEventListener('drop', handleDrop, false);
    input.addEventListener('change', handleFiles, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        input.files = files; // Assign to input
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        const file = e.target.files[0];
        if (file) {
            previewFile(file, preview);
            dropArea.querySelector('.file-msg').textContent = file.name;
        }
    }
}

function previewFile(file, previewElement) {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function() {
        previewElement.innerHTML = `<img src="${reader.result}" alt="Preview">`;
        previewElement.classList.remove('hidden');
    }
}

// Initialize File Uploads
document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload('dropAreaEnc', 'image', 'previewEnc');
    setupFileUpload('dropAreaDec', 'image', 'previewDec');
});

// Form Submissions
const loader = document.getElementById('loader');

// Encrypt Form
document.getElementById('encryptForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    loader.classList.remove('hidden');
    
    const formData = new FormData(e.target);
    const resultArea = document.getElementById('encResult');
    
    try {
        const response = await fetch('/encrypt_hide', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('downloadBtn').href = data.download_url;
            document.getElementById('capUsed').textContent = data.stats.capacity_used;
            resultArea.classList.remove('hidden');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('An unexpected error occurred: ' + error);
    } finally {
        loader.classList.add('hidden');
    }
});

// Decrypt Form
document.getElementById('decryptForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    loader.classList.remove('hidden');
    
    const formData = new FormData(e.target);
    const resultArea = document.getElementById('decResult');
    
    try {
        const response = await fetch('/extract_decrypt', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('revealedMessage').textContent = data.message;
            resultArea.classList.remove('hidden');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('An unexpected error occurred: ' + error);
    } finally {
        loader.classList.add('hidden');
    }
});
