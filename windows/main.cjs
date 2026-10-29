const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const os = require('node:os');
const { WebSocketServer } = require('ws');
const PORT = 38471;
let server = null;
function localAddress() {
  for (const entries of Object.values(os.networkInterfaces())) {
    for (const entry of entries || []) if (entry.family === 'IPv4' && !entry.internal) return entry.address;
  }
  return '127.0.0.1';
}
ipcMain.handle('lan-host', async () => {
  if (server) return localAddress();
  server = new WebSocketServer({ host: '0.0.0.0', port: PORT });
  server.on('connection', ws => {
    const peers = [...server.clients].filter(c => c !== ws && c.readyState === 1);
    if (peers.length > 0) { ws.close(1013, 'Room full'); return; }
    for (const peer of peers) peer.send(JSON.stringify({ __lan: 'joined' }));
    ws.on('message', data => {
      for (const client of server.clients) if (client !== ws && client.readyState === 1) client.send(data.toString());
    });
  });
  server.on('error', err => console.error('LAN server:', err));
  return localAddress();
});
ipcMain.handle('lan-stop', () => { if (server) { for (const c of server.clients) c.close(); server.close(); server = null; } });
app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1100, height: 720, autoHideMenuBar: true, webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.cjs') } });
  win.loadFile(path.join(__dirname, 'game', 'index.html'));
});
app.on('window-all-closed', () => app.quit());
