const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const os = require('node:os');
const { WebSocketServer } = require('ws');
const PORT = 38471;
let server = null;
function localAddress() {
  const candidates = [];
  for (const [name, entries] of Object.entries(os.networkInterfaces())) {
    for (const entry of entries || []) {
      if (entry.family !== 'IPv4' || entry.internal) continue;
      const ip = entry.address;
      const privateIP = /^192\\.168\\./.test(ip) || /^10\\./.test(ip) ||
        /^172\\.(1[6-9]|2[0-9]|3[01])\\./.test(ip);
      const virtual = /virtual|vmware|vbox|hyper-v|vethernet|docker|wsl|tailscale|zerotier|vpn|loopback|bluetooth/i.test(name);
      candidates.push({ ip, score: (privateIP ? 10 : 0) + (/wi-?fi|wireless|wlan|ethernet/i.test(name) ? 5 : 0) - (virtual ? 100 : 0) });
    }
  }
  candidates.sort((a, b) => b.score - a.score);
  return candidates.length ? candidates[0].ip : '127.0.0.1';
}

ipcMain.handle('lan-host', async () => {
  if (server) return localAddress();
  server = new WebSocketServer({ host: '0.0.0.0', port: PORT });
  server.on('connection', ws => {
    const peers = [...server.clients].filter(c => c !== ws && c.readyState === 1);
    if (peers.length > 1) { ws.close(1013, 'Room full'); return; }
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
