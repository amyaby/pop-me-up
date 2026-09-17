const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bubble', {
  move: (rel) => ipcRenderer.send('move-window', rel),
  quit: () => ipcRenderer.send('quit-app'),
  log: (msg) => ipcRenderer.send('log-error', msg),
  setIgnoreMouse: (ignore) => ipcRenderer.send('set-ignore-mouse', ignore),
  platform: process.platform,
});