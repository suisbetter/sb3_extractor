// electron/preload.js
// Exposes a safe, narrow API to the renderer via contextBridge.
// The renderer can call these functions; it CANNOT access Node.js directly.

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  /** True when running inside Electron (lets index.html adapt its behaviour). */
  isElectron: true,

  /**
   * Open the native "Open File" dialog.
   * @returns {Promise<{canceled: boolean, name?: string, buffer?: ArrayBuffer, error?: string}>}
   */
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),

  /**
   * Open the native "Save File" dialog and write the file.
   * @param {string} suggestedName   Default file name shown in the dialog.
   * @param {ArrayBuffer} buffer     File contents.
   * @returns {Promise<{success: boolean, filePath?: string, reason?: string}>}
   */
  saveFile: (suggestedName, buffer) =>
    ipcRenderer.invoke('save-file', { suggestedName, buffer }),
});
