// electron/main.js
// Electron main process – wraps index.html in a native desktop window.

const { app, BrowserWindow, dialog, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// ── Security: disable remote content loading ────────────────────────────────
app.on('web-contents-created', (_, contents) => {
  contents.on('will-navigate', (event, url) => {
    // Allow local file:// navigation; block everything else
    if (!url.startsWith('file://')) {
      event.preventDefault();
    }
  });
});

// ── Window creation ─────────────────────────────────────────────────────────
function createWindow() {
  const win = new BrowserWindow({
    width: 820,
    height: 640,
    minWidth: 600,
    minHeight: 480,
    title: 'SB3 Converter & Extractor',
    // Use native frame on all platforms for consistency
    frame: true,
    backgroundColor: '#1e1e2e',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Load the bundled web UI
  win.loadFile(path.join(__dirname, '..', 'index.html'));

  // Open DevTools in dev mode
  if (process.argv.includes('--dev')) {
    win.webContents.openDevTools();
  }

  // Open external links in the default browser, not inside Electron
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // macOS: re-create window when dock icon is clicked with no open windows
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Quit on all platforms (including macOS) when all windows are closed
  app.quit();
});

// ── IPC: Save file dialog ───────────────────────────────────────────────────
// The renderer calls window.electronAPI.saveFile(filename, uint8array)
// and we handle the actual file write here in the main process.
ipcMain.handle('save-file', async (_, { suggestedName, buffer }) => {
  const { filePath, canceled } = await dialog.showSaveDialog({
    title: 'Save extracted archive',
    defaultPath: path.join(os.homedir(), 'Downloads', suggestedName),
    filters: [
      { name: 'ZIP Archive', extensions: ['zip'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });

  if (canceled || !filePath) {
    return { success: false, reason: 'canceled' };
  }

  try {
    fs.writeFileSync(filePath, Buffer.from(buffer));
    // Open the containing folder in the system file manager
    shell.showItemInFolder(filePath);
    return { success: true, filePath };
  } catch (err) {
    return { success: false, reason: err.message };
  }
});

// ── IPC: Open file dialog ───────────────────────────────────────────────────
ipcMain.handle('open-file-dialog', async () => {
  const { filePaths, canceled } = await dialog.showOpenDialog({
    title: 'Select Scratch Project',
    filters: [
      { name: 'Scratch Projects', extensions: ['sb3', 'zip'] },
      { name: 'All Files', extensions: ['*'] },
    ],
    properties: ['openFile'],
  });

  if (canceled || filePaths.length === 0) {
    return { canceled: true };
  }

  try {
    const filePath = filePaths[0];
    const buffer = fs.readFileSync(filePath);
    return {
      canceled: false,
      name: path.basename(filePath),
      buffer: buffer.buffer.slice(
        buffer.byteOffset,
        buffer.byteOffset + buffer.byteLength,
      ),
    };
  } catch (err) {
    return { canceled: true, error: err.message };
  }
});
