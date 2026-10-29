// Local-network multiplayer. No PeerJS, STUN, TURN or internet matchmaking.
const PORT = 38471;
export const ROOM_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
export const ROOM_CODE_LENGTH = 4;
export class Link {
  constructor() {
    this.ws = null; this.closed = false; this.onPeer = () => {};
    this.onMessage = () => {}; this.onClose = () => {};
  }
  get connected() { return !!this.ws && this.ws.readyState === WebSocket.OPEN; }
  async host() {
    if (!window.squarezLAN) throw new Error('Host a LAN game from Windows; Android can join');
    const address = await window.squarezLAN.host();
    await this.connect('127.0.0.1');
    return address;
  }
  async join(address) { await this.connect(address); }
  connect(address) {
    if (!/^(?:\\d{1,3}\\.){3}\\d{1,3}$/.test(address)) return Promise.reject(new Error('Enter the host PC IPv4 address'));
    return new Promise((resolve, reject) => {
      const ws = new WebSocket('ws://' + address + ':' + PORT);
      this.ws = ws;
      const timer = setTimeout(() => { ws.close(); reject(new Error('LAN connection timed out')); }, 8000);
      ws.onopen = () => { clearTimeout(timer); resolve(); };
      ws.onerror = () => { clearTimeout(timer); reject(new Error('Cannot reach host. Check Wi-Fi and Windows Firewall')); };
      ws.onmessage = e => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.__lan === 'joined') this.onPeer(true);
          else this.onMessage(msg);
        } catch {}
      };
      ws.onclose = () => { if (!this.closed) this.onClose('lost'); };
    });
  }
  send(msg) { if (this.connected) this.ws.send(JSON.stringify(msg)); }
  close() {
    this.closed = true;
    if (this.ws) this.ws.close();
    if (window.squarezLAN) window.squarezLAN.stop();
  }
}
