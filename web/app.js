// Глобальное состояние приложения
let appState = {
    files: new Map(),
    selectedFileId: null,
    scanning: false,
    startTime: null,
    timerInterval: null
};

async function checkForUpdates() {
    try {
        logMessage('info', 'Checking for updates...');
        
        const result = await pywebview.api.check_updates();
        
        if (result.success && result.available) {
            showUpdateDialog(result);
        } else if (result.success) {
            alert('You are using the latest version!');
            logMessage('info', 'No updates available');
        } else {
            alert(`Failed to check updates: ${result.error || 'Unknown error'}`);
            logMessage('error', `Update check failed: ${result.error}`);
        }
    } catch (error) {
        logMessage('error', `Failed to check updates: ${error}`);
        alert('Failed to check for updates. Please check your internet connection.');
    }
}

function showUpdateDialog(updateInfo) {
    const dialog = document.createElement('div');
    dialog.className = 'update-dialog';
    dialog.innerHTML = `
        <div class="update-dialog-overlay"></div>
        <div class="update-dialog-content">
            <h2>🎉 Update Available!</h2>
            <div class="update-info">
                <p class="update-version">Version ${updateInfo.version}</p>
                <p class="update-release">${updateInfo.release_name}</p>
                <div class="update-changelog">
                    <h3>What's New:</h3>
                    <pre>${updateInfo.changelog}</pre>
                </div>
            </div>
            <div class="update-progress" id="update-progress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="update-progress-fill"></div>
                </div>
                <p id="update-progress-text">Downloading...</p>
            </div>
            <div class="update-actions">
                <button class="btn btn-success" id="btn-download-update">
                    ⬇️ Download & Install
                </button>
                <button class="btn btn-secondary" id="btn-cancel-update">
                    Cancel
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Event listeners
    document.getElementById('btn-download-update').addEventListener('click', async () => {
        await downloadAndInstallUpdate();
    });
    
    document.getElementById('btn-cancel-update').addEventListener('click', () => {
        dialog.remove();
    });
}

async function downloadAndInstallUpdate() {
    try {
        const progressDiv = document.getElementById('update-progress');
        const downloadBtn = document.getElementById('btn-download-update');
        
        progressDiv.style.display = 'block';
        downloadBtn.disabled = true;
        
        logMessage('info', 'Downloading update...');
        
        const downloadResult = await pywebview.api.download_update();
        
        if (downloadResult.success) {
            logMessage('info', 'Installing update...');
            document.getElementById('update-progress-text').textContent = 'Installing...';
            
            const installResult = await pywebview.api.install_update(downloadResult.file_path);
            
            if (installResult.success) {
                alert('Update installed successfully! The application will restart now.');
                // Приложение перезапустится автоматически
            } else {
                alert(`Installation failed: ${installResult.message}`);
                progressDiv.style.display = 'none';
                downloadBtn.disabled = false;
            }
        } else {
            alert(`Download failed: ${downloadResult.message || downloadResult.error}`);
            progressDiv.style.display = 'none';
            downloadBtn.disabled = false;
        }
    } catch (error) {
        logMessage('error', `Update failed: ${error}`);
        alert('Update failed. Please try again later.');
    }
}

function updateDownloadProgress(progress, downloaded, total) {
    const progressFill = document.getElementById('update-progress-fill');
    const progressText = document.getElementById('update-progress-text');
    
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    if (progressText) {
        const downloadedMB = (downloaded / 1024 / 1024).toFixed(2);
        const totalMB = (total / 1024 / 1024).toFixed(2);
        progressText.textContent = `Downloading... ${downloadedMB}MB / ${totalMB}MB (${Math.round(progress)}%)`;
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initMatrixBackground();
    initEventListeners();
    document.getElementById('btn-check-updates').addEventListener('click', checkForUpdates);
    logMessage('info', 'Matrix Scanner - Minecraft Anti-Cheat initialized');
    logMessage('info', 'Click START SCAN to search for Minecraft cheats (.jar/.exe)');
    logMessage('info', 'Detecting: LiquidBounce, Wurst, Impact, Meteor, and 60+ more clients');
});

// Matrix Rain Effect
function initMatrixBackground() {
    const canvas = document.getElementById('matrix-canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()';
    const fontSize = 14;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = Array(columns).fill(0).map(() => Math.random() * canvas.height / fontSize);
    
    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff00';
        ctx.font = fontSize + 'px monospace';
        
        for (let i = 0; i < drops.length; i++) {
            const text = chars.charAt(Math.floor(Math.random() * chars.length));
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 33);
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Event Listeners
function initEventListeners() {
    document.getElementById('btn-start-scan').addEventListener('click', startScan);
    document.getElementById('btn-stop-scan').addEventListener('click', stopScan);
    document.getElementById('btn-clear-threats').addEventListener('click', clearThreats);
    document.getElementById('btn-export').addEventListener('click', exportReport);
    document.getElementById('btn-clear-list').addEventListener('click', clearList);
    document.getElementById('btn-clear-console').addEventListener('click', clearConsole);
    document.getElementById('btn-refresh-list').addEventListener('click', refreshList);
}

async function startScan() {
    const scanMode = document.querySelector('input[name="scan-mode"]:checked').value;
    
    // Очищаем предыдущие результаты
    appState.files.clear();
    document.getElementById('file-list').innerHTML = '';
    
    try {
        const result = await pywebview.api.start_scan(scanMode);
        
        if (result.success) {
            appState.scanning = true;
            appState.startTime = Date.now();
            
            document.getElementById('btn-start-scan').disabled = true;
            document.getElementById('btn-stop-scan').disabled = false;
            document.getElementById('progress-container').style.display = 'block';
            document.getElementById('empty-state').style.display = 'none';
            
            const statusEl = document.getElementById('app-status');
            statusEl.textContent = 'SCANNING';
            statusEl.classList.add('scanning');
            
            // Запускаем таймер (обновляется через Python)
            // Таймер будет обновляться функцией updateTimer(), вызываемой из Python
        } else {
            logMessage('warning', result.message);
        }
    } catch (error) {
        logMessage('error', `Failed to start scan: ${error}`);
    }
}

async function stopScan() {
    try {
        const result = await pywebview.api.stop_scan();
        onScanComplete();
    } catch (error) {
        logMessage('error', `Failed to stop scan: ${error}`);
    }
}

async function clearThreats() {
    if (!confirm('This will delete all detected cheat files and kill their processes. Continue?')) {
        return;
    }
    
    try {
        logMessage('warning', 'Clearing threats...');
        const result = await pywebview.api.clear_threats();
        
        if (result.success) {
            // Удаляем угрозы из UI
            const fileList = document.getElementById('file-list');
            const threatItems = fileList.querySelectorAll('.file-item.threat');
            threatItems.forEach(item => item.remove());
            
            // Проверяем, остались ли файлы
            if (fileList.children.length === 0) {
                document.getElementById('empty-state').style.display = 'flex';
            }
            
            document.getElementById('btn-clear-threats').disabled = true;
            
            logMessage('info', `Successfully cleared ${result.deleted} threat(s)`);
            if (result.processes_killed > 0) {
                logMessage('info', `Killed ${result.processes_killed} process(es)`);
            }
        }
    } catch (error) {
        logMessage('error', `Failed to clear threats: ${error}`);
    }
}

async function exportReport() {
    try {
        const reportData = {
            timestamp: new Date().toISOString(),
            version: '2.4.1',
            stats: {
                scanned: parseInt(document.getElementById('stat-scanned').textContent),
                threats: parseInt(document.getElementById('stat-threats').textContent),
                clean: parseInt(document.getElementById('stat-clean').textContent),
                time: document.getElementById('stat-time').textContent
            },
            files: Array.from(appState.files.values())
        };
        
        const result = await pywebview.api.export_report(reportData);
        if (result.success) {
            logMessage('info', `Report exported successfully`);
        }
    } catch (error) {
        logMessage('error', `Failed to export report: ${error}`);
    }
}

async function clearList() {
    try {
        const result = await pywebview.api.clear_list();
        if (result.success) {
            appState.files.clear();
            appState.selectedFileId = null;
            
            document.getElementById('file-list').innerHTML = '';
            document.getElementById('empty-state').style.display = 'flex';
            document.getElementById('details-container').innerHTML = `
                <div class="empty-details">
                    <div class="empty-icon">👆</div>
                    <p>Select a threat to view details</p>
                </div>
            `;
            
            document.getElementById('stat-scanned').textContent = '0';
            document.getElementById('stat-threats').textContent = '0';
            document.getElementById('stat-clean').textContent = '0';
            document.getElementById('stat-time').textContent = '0:00';
            
            document.getElementById('btn-clear-threats').disabled = true;
        }
    } catch (error) {
        logMessage('error', `Failed to clear list: ${error}`);
    }
}

function refreshList() {
    logMessage('info', 'Refreshing list...');
}

function clearConsole() {
    const consoleLog = document.getElementById('console-log');
    consoleLog.innerHTML = `
        <div class="console-entry">
            <span class="console-time">[${getCurrentTime()}]</span>
            <span class="console-message">Console cleared.</span>
        </div>
    `;
}

// UI Update Functions (called from Python)
function addFileToList(fileData) {
    appState.files.set(fileData.id, fileData);
    
    document.getElementById('empty-state').style.display = 'none';
    
    const fileList = document.getElementById('file-list');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item scanning';
    fileItem.dataset.fileId = fileData.id;
    fileItem.innerHTML = `
        <div class="file-icon">⏳</div>
        <div class="file-info">
            <div class="file-name">${fileData.name}</div>
            <div class="file-path">${fileData.path}</div>
        </div>
        <div class="file-status">
            <span class="status-badge scanning">scanning</span>
        </div>
    `;
    
    fileItem.addEventListener('click', () => selectFile(fileData.id));
    fileList.appendChild(fileItem);
}

function updateFileStatus(fileId, status, result) {
    const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
    if (!fileItem) return;
    
    fileItem.className = `file-item ${status}`;
    
    const icon = fileItem.querySelector('.file-icon');
    const badge = fileItem.querySelector('.status-badge');
    
    switch (status) {
        case 'scanning':
            icon.textContent = '⏳';
            badge.className = 'status-badge scanning';
            badge.textContent = 'scanning';
            break;
        case 'threat':
            icon.textContent = '🦠';
            badge.className = 'status-badge threat';
            badge.textContent = 'THREAT';
            
            // Добавляем индикатор запущенного процесса
            if (result && result.isRunning) {
                badge.innerHTML = 'THREAT <span style="color: #ff0000;">●</span> RUNNING';
            }
            break;
        case 'clean':
            icon.textContent = '✅';
            badge.className = 'status-badge clean';
            badge.textContent = 'clean';
            break;
        case 'error':
            icon.textContent = '❌';
            badge.className = 'status-badge pending';
            badge.textContent = 'error';
            break;
    }
    
    if (result) {
        const file = appState.files.get(fileId);
        if (file) {
            file.result = result;
            file.status = status;
            
            if (appState.selectedFileId === fileId) {
                showFileDetails(file);
            }
        }
    }
}

function updateStats(scanned, threats, clean) {
    document.getElementById('stat-scanned').textContent = scanned;
    document.getElementById('stat-threats').textContent = threats;
    document.getElementById('stat-clean').textContent = clean;
    
    document.getElementById('btn-clear-threats').disabled = threats === 0;
}

function updateProgress(percent, fileName) {
    document.getElementById('progress-fill').style.width = `${percent}%`;
    document.getElementById('progress-percent').textContent = `${Math.round(percent)}%`;
    document.getElementById('progress-text').textContent = fileName;
}

// Функция обновления таймера (вызывается из Python)
function updateTimer(elapsed) {
    document.getElementById('stat-time').textContent = formatTime(elapsed * 1000);
}

function onScanComplete() {
    appState.scanning = false;
    
    document.getElementById('btn-start-scan').disabled = false;
    document.getElementById('btn-stop-scan').disabled = true;
    
    const statusEl = document.getElementById('app-status');
    statusEl.textContent = 'READY';
    statusEl.classList.remove('scanning');
    
    setTimeout(() => {
        document.getElementById('progress-container').style.display = 'none';
    }, 2000);
}

function selectFile(fileId) {
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
    if (fileItem) {
        fileItem.classList.add('selected');
    }
    
    appState.selectedFileId = fileId;
    const file = appState.files.get(fileId);
    
    if (file) {
        showFileDetails(file);
    }
}

function showFileDetails(file) {
    const container = document.getElementById('details-container');
    
    let html = `
        <div class="detail-section">
            <h4>📄 File Information</h4>
            <div class="detail-row">
                <span class="detail-label">Name:</span>
                <span class="detail-value">${file.name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Path:</span>
                <span class="detail-value">${file.path}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="detail-value">${file.status.toUpperCase()}</span>
            </div>
    `;
    
    if (file.result) {
        html += `
            <div class="detail-row">
                <span class="detail-label">Size:</span>
                <span class="detail-value">${formatBytes(file.result.size)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">SHA256:</span>
                <span class="detail-value">${file.result.hash}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Scan Date:</span>
                <span class="detail-value">${formatDate(file.result.scanDate)}</span>
            </div>
        </div>
        `;
        
        if (file.result.isThreat) {
            const threatLevelHTML = Array(3).fill(0).map((_, i) => 
                `<span class="${i < file.result.threatLevel ? 'active' : ''}"></span>`
            ).join('');
            
            html += `
                <div class="detail-section">
                    <h4>🦠 Threat Information</h4>
                    <div class="threat-info">
                        <div class="detail-row">
                            <span class="detail-label">Type:</span>
                            <span class="detail-value">${file.result.threatType}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Severity:</span>
                            <div class="threat-level">${threatLevelHTML}</div>
                        </div>
                        ${file.result.isRunning ? `
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value" style="color: #ff0000;">● PROCESS RUNNING</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="detail-section">
                    <h4>⚙️ Actions</h4>
                    <div class="detail-actions">
                        <button class="btn btn-warning" onclick="quarantineFile('${file.id}')">
                            📦 Quarantine & Kill
                        </button>
                        <button class="btn btn-danger" onclick="deleteFile('${file.id}')">
                            🗑️ Delete & Kill
                        </button>
                    </div>
                </div>
            `;
        }
    } else {
        html += '</div>';
    }
    
    container.innerHTML = html;
}

async function quarantineFile(fileId) {
    const file = appState.files.get(fileId);
    if (!file) return;
    
    try {
        const result = await pywebview.api.quarantine_file(file.path);
        if (result.success) {
            const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
            if (fileItem) fileItem.remove();
            
            appState.files.delete(fileId);
            
            const threats = parseInt(document.getElementById('stat-threats').textContent);
            updateStats(
                parseInt(document.getElementById('stat-scanned').textContent),
                threats - 1,
                parseInt(document.getElementById('stat-clean').textContent)
            );
            
            document.getElementById('details-container').innerHTML = `
                <div class="empty-details">
                    <div class="empty-icon">👆</div>
                    <p>Select a threat to view details</p>
                </div>
            `;
        }
    } catch (error) {
        logMessage('error', `Failed to quarantine file: ${error}`);
    }
}

async function deleteFile(fileId) {
    const file = appState.files.get(fileId);
    if (!file) return;
    
    if (!confirm(`Delete ${file.name} and kill its process?`)) {
        return;
    }
    
    try {
        const result = await pywebview.api.delete_file(file.path);
        if (result.success) {
            const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
            if (fileItem) fileItem.remove();
            
            appState.files.delete(fileId);
            
            const threats = parseInt(document.getElementById('stat-threats').textContent);
            updateStats(
                parseInt(document.getElementById('stat-scanned').textContent),
                threats - 1,
                parseInt(document.getElementById('stat-clean').textContent)
            );
            
            document.getElementById('details-container').innerHTML = `
                <div class="empty-details">
                    <div class="empty-icon">👆</div>
                    <p>Select a threat to view details</p>
                </div>
            `;
        } else {
            alert(result.message);
        }
    } catch (error) {
        logMessage('error', `Failed to delete file: ${error}`);
    }
}

// Logging
function addLog(level, message) {
    logMessage(level, message);
}

function logMessage(level, message) {
    const consoleLog = document.getElementById('console-log');
    const entry = document.createElement('div');
    entry.className = 'console-entry';
    entry.innerHTML = `
        <span class="console-time">[${getCurrentTime()}]</span>
        <span class="console-message ${level}">${escapeHtml(message)}</span>
    `;
    consoleLog.appendChild(entry);
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

// Utility Functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

function formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
}

function getCurrentTime() {
    return new Date().toLocaleTimeString();
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
function showUpdateNotification(version) {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">🔔</span>
            <span class="notification-text">New version ${version} available!</span>
            <button class="notification-btn" onclick="checkForUpdates()">Update Now</button>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">✕</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 100);
}