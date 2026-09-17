const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const fs = require('fs');

let logPath = path.join(app.getPath('userData'), 'error.log');
function writeLog(msg) {
  try { fs.appendFileSync(logPath, new Date().toISOString() + ' | ' + msg + '\n'); } catch (e) {}
}
process.on('uncaughtException', (err) => { writeLog('MAIN uncaught: ' + (err && err.stack || err)); });
process.on('unhandledRejection', (reason) => { writeLog('MAIN rejection: ' + (reason && reason.stack || reason)); });
ipcMain.on('log-error', (event, msg) => writeLog('RENDERER: ' + msg));

app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}

let win = null;

function createWindow() {
  const { workArea } = screen.getPrimaryDisplay();
  const winW = 500;
  const winH = 540;
  const x = workArea.x + workArea.width - winW - 24;
  const y = workArea.y + workArea.height - winH - 24;

  win = new BrowserWindow({
    width: winW,
    height: winH,
    x,
    y,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.setAlwaysOnTop(true, 'screen-saver');
  win.setIgnoreMouseEvents(true, { forward: true });
  win.loadFile('index.html');

  win.webContents.on('console-message', (event, level, message, line, sourceId) => {
    if (level >= 3) writeLog('CONSOLE[' + level + '] ' + sourceId + ':' + line + ' ' + message);
  });
  win.webContents.on('render-process-gone', (event, details) => {
    writeLog('RENDERER GONE: ' + JSON.stringify(details));
  });
}

ipcMain.on('set-ignore-mouse', (event, ignore) => {
  if (!win || win.isDestroyed()) return;
  win.setIgnoreMouseEvents(!!ignore, { forward: true });
});

ipcMain.on('move-window', (event, rel) => {
  try {
    if (!win || win.isDestroyed()) return;
    const { workArea } = screen.getPrimaryDisplay();
    const [cx, cy] = win.getPosition();
    const [w, h] = win.getSize();
    let x = Math.round(cx + (rel && rel.x || 0));
    let y = Math.round(cy + (rel && rel.y || 0));
    x = Math.min(Math.max(x, workArea.x - w + 60), workArea.x + workArea.width - 60);
    y = Math.min(Math.max(y, workArea.y), workArea.y + workArea.height - 60);
    win.setPosition(x, y);
  } catch (err) {
    writeLog('move-window error: ' + (err && err.stack || err));
  }
});

ipcMain.on('quit-app', () => app.quit());

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());