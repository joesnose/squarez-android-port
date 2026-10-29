const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const os = require('node:os');
const dgram = require('node:dgram');
const { WebSocketServer } = require('ws');
const PORT = 38471;
let server = null;
let discovery = null;
const DISCOVERY_PORT = 38472;
function startDiscovery() {
  if (discovery) return;
  const socket = dgram.createSocket({ type: 'udp4', reuseAddr: true });
  socket.on('error', err => console.error('LAN discovery:', err));
  socket.on('message', (data, remote) => {
    if (data.toString().trim() === 'SQUAREZ_DISCOVER_V1' && server && server.address())
      socket.send(Buffer.from('SQUAREZ_HOST_V1'), remote.port, remote.address);
  });
  socket.bind(DISCOVERY_PORT, '0.0.0.0');
  discovery = socket;
}
function stopDiscovery() { if (discovery) { discovery.close(); discovery = null; } }
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
  const candidate = new WebSocketServer({ host: '0.0.0.0', port: PORT });
  try {
    await new Promise((resolve, reject) => {
      if (candidate.address()) return resolve();
      candidate.once('listening', resolve);
      candidate.once('error', reject);
    });
  } catch (err) {
    try { candidate.close(); } catch {}
    throw new Error('LAN server could not listen on port ' + PORT + ': ' + err.message);
  }
  server = candidate;
  startDiscovery();
  server.on('error', err => console.error('LAN server:', err));
  server.on('connection', ws => {
    const peers = [...server.clients].filter(c => c !== ws && c.readyState === 1);
    if (peers.length > 1) { ws.close(1013, 'Room full'); return; }
    for (const peer of peers) peer.send(JSON.stringify({ __lan: 'joined' }));
    ws.on('message', data => {
      for (const client of server.clients) if (client !== ws && client.readyState === 1) client.send(data.toString());
    });
  });
  return localAddress();
});
ipcMain.handle('lan-stop', () => {
  stopDiscovery();
  if (server) {
    const previous = server;
    server = null;
    for (const c of previous.clients) c.close();
    previous.close();
  }
});
ipcMain.handle('lan-discover', async () => {
  const socket = dgram.createSocket('udp4');
  const hosts = new Set();
  return await new Promise(resolve => {
    socket.on('error', () => { try { socket.close(); } catch {} resolve([...hosts]); });
    socket.on('message', (data, remote) => { if (data.toString().trim() === 'SQUAREZ_HOST_V1') hosts.add(remote.address); });
    socket.bind(0, () => {
      socket.setBroadcast(true);
      for (const entries of Object.values(os.networkInterfaces())) for (const entry of entries || []) {
        if (entry.family !== 'IPv4' || entry.internal) continue;
        const parts = entry.address.split('.').map(Number);
        const mask = entry.netmask.split('.').map(Number);
        const broadcast = parts.map((n, i) => (n | (~mask[i] & 255))).join('.');
        socket.send('SQUAREZ_DISCOVER_V1', DISCOVERY_PORT, broadcast, () => {});
      }
      socket.send('SQUAREZ_DISCOVER_V1', DISCOVERY_PORT, '255.255.255.255', () => {});
      setTimeout(() => { socket.close(); resolve([...hosts]); }, 1800);
    });
  });
});
app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1100, height: 720, autoHideMenuBar: true, webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.cjs') } });
  win.loadFile(path.join(__dirname, 'game', 'index.html'));
});
app.on('window-all-closed', () => app.quit());
