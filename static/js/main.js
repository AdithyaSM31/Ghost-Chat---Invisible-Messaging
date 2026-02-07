// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

// Drag/Drop & File Input
function setupFileUpload(dropAreaId, inputName, previewId) {
    const dropArea = document.getElementById(dropAreaId);
    const input = dropArea.querySelector('input');
    const preview = document.getElementById(previewId);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'), false);
    });

    dropArea.addEventListener('drop', e => {
        input.files = e.dataTransfer.files;
        handleFiles(input.files[0], preview, dropArea);
    });

    input.addEventListener('change', e => {
        handleFiles(e.target.files[0], preview, dropArea);
    });
}

function handleFiles(file, previewElement, dropArea) {
    if (file) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = function() {
            previewElement.innerHTML = `<img src="${reader.result}" alt="Preview">`;
            previewElement.classList.remove('hidden');
        }
        dropArea.querySelector('.file-msg').textContent = file.name;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload('dropAreaEnc', 'image', 'previewEnc');
    setupFileUpload('dropAreaDec', 'image', 'previewDec');
});


// ---------------------------------------------------------
// Logic Handler (Hybrid: Server vs Client)
// ---------------------------------------------------------

const isOffline = window.location.protocol === 'file:' || 
                  (window.Capacitor && window.Capacitor.isNativePlatform());

const loader = document.getElementById('loader');

// Helper: Convert File to ImageData
function getImageData(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                resolve({
                    imageData: ctx.getImageData(0, 0, canvas.width, canvas.height),
                    canvas: canvas
                });
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

// Encryption Handler
document.getElementById('encryptForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    loader.classList.remove('hidden');
    
    const formData = new FormData(e.target);
    const resultArea = document.getElementById('encResult');
    
    // Try Client-Side (Offline) if configured, or fall back if server fails
    if (isOffline) {
        await handleOfflineEncrypt(formData, resultArea);
    } else {
        try {
            const response = await fetch('/encrypt_hide', { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok) {
                showEncSuccess(data, resultArea);
            } else {
                alert('Server Error: ' + data.error);
                loader.classList.add('hidden');
            }
        } catch (error) {
            console.log("Server unreachable. Switching to Offline Mode.");
            await handleOfflineEncrypt(formData, resultArea);
        }
    }
});

async function handleOfflineEncrypt(formData, resultArea) {
    try {
        const file = formData.get('image');
        const message = formData.get('message');
        const password = formData.get('password');

        // 1. Encrypt
        const encrypted = await GhostEngine.encryptMessage(password, message);
        
        // 2. Pack
        const packed = GhostEngine.pack(encrypted);
        
        // 3. Embed (LSB)
        const { imageData, canvas } = await getImageData(file);
        
        // Embed modified pixels
        GhostEngine.embedLSB(imageData, packed);
        
        // Put back to canvas
        const ctx = canvas.getContext('2d');
        ctx.putImageData(imageData, 0, 0);
        
        // Export
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        const url = URL.createObjectURL(blob);
        
        // Show params
        const stats = {
            capacity_used: ((packed.length / (imageData.width * imageData.height * 3 / 8)) * 100).toFixed(2) + "%"
        };
        
        showEncSuccess({ download_url: url, stats: stats }, resultArea);
        
    } catch (e) {
        alert("Offline Error: " + e.message);
        loader.classList.add('hidden');
    }
}

function showEncSuccess(data, resultArea) {
    const btn = document.getElementById('downloadBtn');
    btn.href = data.download_url;
    
    // Default desktop behavior
    if (data.download_url.startsWith('blob:')) {
        btn.download = "ghost_msg.png";
    }

    // Android/Capacitor Native Handling
    if (window.Capacitor && window.Capacitor.isNativePlatform()) {
        btn.textContent = "Save Image to Documents";
        btn.onclick = async (e) => {
            e.preventDefault();
            const originalText = btn.textContent;
            btn.textContent = "Saving...";
            
            try {
                // 1. Fetch the blob data
                const response = await fetch(data.download_url);
                const blob = await response.blob();
                
                // 2. Convert to Base64
                const reader = new FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = async () => {
                    const base64Data = reader.result;
                    
                    try {
                        const { Filesystem } = Capacitor.Plugins;
                        const fileName = 'ghost_' + new Date().getTime() + '.png';
                        
                        // 3. Write to Documents folder
                        await Filesystem.writeFile({
                            path: fileName,
                            data: base64Data,
                            directory: 'DOCUMENTS'
                        });
                        
                        alert("Saved successfully!\nLocation: Documents/" + fileName);
                    } catch (err) {
                        // Fallback: Try native sharing if filesystem permission fails
                        if (navigator.share) {
                             const file = new File([blob], "ghost_msg.png", { type: "image/png" });
                             await navigator.share({ files: [file] }).catch(() => {});
                        } else {
                            alert("Save failed: " + err.message);
                        }
                    }
                    btn.textContent = originalText;
                };
            } catch (err) {
                alert("Error: " + err.message);
                btn.textContent = originalText;
            }
        };
    }
    
    document.getElementById('capUsed').textContent = data.stats.capacity_used;
    resultArea.classList.remove('hidden');
    loader.classList.add('hidden');
}


// Decryption Handler
document.getElementById('decryptForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    loader.classList.remove('hidden');
    
    const formData = new FormData(e.target);
    const resultArea = document.getElementById('decResult');
    
    if (isOffline) {
        await handleOfflineDecrypt(formData, resultArea);
    } else {
        try {
            const response = await fetch('/extract_decrypt', { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok) {
                showDecSuccess(data.message, resultArea);
            } else {
                alert('Server Error: ' + data.error);
                loader.classList.add('hidden');
            }
        } catch (error) {
             console.log("Server unreachable. Switching to Offline Mode.");
             await handleOfflineDecrypt(formData, resultArea);
        }
    }
});

async function handleOfflineDecrypt(formData, resultArea) {
    try {
        const file = formData.get('image');
        const password = formData.get('password');
        
        const { imageData } = await getImageData(file);
        
        // Extract
        const packed = GhostEngine.extractLSB(imageData);
        
        // Decrypt
        const message = await GhostEngine.decryptMessage(password, packed);
        
        showDecSuccess(message, resultArea);
    } catch (e) {
        const msg = e.message === "Invalid Ghost Header" 
            ? "No hidden message found (or file was compressed)." 
            : e.message;
        alert("Offline Error: " + msg);
        loader.classList.add('hidden');
    }
}

function showDecSuccess(message, resultArea) {
    document.getElementById('revealedMessage').textContent = message;
    resultArea.classList.remove('hidden');
    loader.classList.add('hidden');
}
