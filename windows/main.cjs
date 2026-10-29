const { app, BrowserWindow } = require('electron');
const path = require('node:path');
app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1100, height: 720, autoHideMenuBar: true, webPreferences: { nodeIntegration: false, contextIsolation: true } });
  win.loadFile(path.join(__dirname, 'game', 'index.html'));
});
app.on('window-all-closed', () => app.quit());
