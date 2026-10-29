const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const os = require('node:os');
const { WebSocketServer } = require('ws');
const PORT = 38471;
let server = null;
function localAddress() {
  const candidates = [];
  for (const [name, entries] of Object.entries(os.networkInterfaces())) {
    if (/virtual|vbox|vmware|hyper-v|vethernet|docker|wsl|loopback|tailscale|zerotier|bluetooth/i.test(name)) continue;
    for (const entry of entries || []) {
      if (entry.family !== 'IPv4' || entry.internal || entry.address.startsWith('169.254.')) continue;
      candidates.push({ name, address: entry.address });
    }
  }
  const preferred = candidates.find(c => c.address.startsWith('192.168.1.'));
  const physical = candidates.find(c => /wi-?fi|wireless|ethernet/i.test(c.name));
  return (preferred || physical || candidates[0] || { address: '127.0.0.1' }).address;
}

ipcMain.handle('lan-host', async () => {
  if (server && server.address()) return localAddress();
  if (server) { try { server.close(); } catch {} server = null; }
  const instance = new WebSocketServer({ host: '0.0.0.0', port: PORT });
  try {
    await new Promise((resolve, reject) => {
      instance.once('listening', resolve);
      instance.once('error', reject);
    });
  } catch (err) {
    try { instance.close(); } catch {}
    throw new Error('LAN server failed to start on port ' + PORT + ': ' + err.message);
  }
  server = instance;
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
ipcMain.handle('lan-stop', () => {
  if (server) {
    const previous = server;
    server = null;
    for (const c of previous.clients) c.close();
    previous.close();
  }
});
app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1100, height: 720, autoHideMenuBar: true, webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.cjs') } });
  win.loadFile(path.join(__dirname, 'game', 'index.html'));
});
app.on('window-all-closed', () => app.quit());
