"""Replace online matchmaking with local IP-based multiplayer and add touch menus."""
from pathlib import Path
import shutil
import sys
root = Path(__file__).resolve().parent.parent
dest = Path(sys.argv[1])
shutil.copyfile(root / 'scripts' / 'lan_net.js', dest / 'src' / 'lan_net.js')
main = dest / 'src' / 'main.js'
s = main.read_text()
old = "import { Link, ROOM_LETTERS, ROOM_CODE_LENGTH } from './net.js';"
assert old in s
s = s.replace(old, "import { Link, ROOM_LETTERS, ROOM_CODE_LENGTH } from './lan_net.js';")
old = "      this.openCode(code => this.joinGame(code));"
assert old in s
s = s.replace(old, "      this.askLanAddress(address => this.joinGame(address));")
marker = "  newLink(role) {"
assert marker in s
s = s.replace(marker, """  askLanAddress(done) {
    const panel = document.createElement('div');
    panel.style.cssText = 'position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:#000c;z-index:99999';
    const form = document.createElement('form');
    form.style.cssText = 'background:#192a39;padding:20px;color:white;font:18px sans-serif;max-width:90vw;max-height:90vh;overflow:auto';
    form.innerHTML = '<strong>Find LAN games</strong><div id="lanResults" style="margin:14px 0">Searching your network...</div><button type="button" id="lanRefresh">Search again</button><hr><label>Manual IP address<br><input name="ip" inputmode="decimal" placeholder="192.168.1.100" style="font-size:18px;margin:8px 0;padding:8px;max-width:75vw"></label><br><button type="submit">Connect by IP</button> <button type="button" id="lanCancel">Cancel</button>';
    panel.appendChild(form); document.body.appendChild(panel);
    const results = form.querySelector('#lanResults');
    const connect = ip => { panel.remove(); delete window.squarezDiscoveryResult; done(ip); };
    const render = hosts => {
      if (!panel.isConnected) return;
      results.textContent = hosts.length ? 'Available hosts:' : 'No games found. Try manual IP or search again.';
      for (const ip of hosts) {
        const button = document.createElement('button');
        button.type = 'button'; button.textContent = 'Join ' + ip;
        button.style.cssText = 'display:block;padding:10px;margin:6px 0;font-size:18px';
        button.onclick = () => connect(ip);
        results.appendChild(button);
      }
    };
    const discover = async () => {
      results.textContent = 'Searching your network...';
      try {
        if (window.squarezLAN && window.squarezLAN.discover) render(await window.squarezLAN.discover());
        else if (window.SquarezDiscovery) {
          window.squarezDiscoveryResult = render;
          window.SquarezDiscovery.discover();
        } else render([]);
      } catch (err) { results.textContent = 'Discovery unavailable: ' + err.message; }
    };
    form.querySelector('#lanRefresh').onclick = discover;
    form.querySelector('#lanCancel').onclick = () => { panel.remove(); delete window.squarezDiscoveryResult; };
    form.onsubmit = e => { e.preventDefault(); const ip = form.elements.ip.value.trim(); if (ip) connect(ip); };
    discover();
  }

""" + marker)
s = s.replace("'The host gets a room code to give the other player.',", "'Windows hosts; Android or Windows joins using the PC IP.',")
s = s.replace("'Players are connected through the free PeerJS service.',", "'Same Wi-Fi/LAN only. No Internet matchmaking.',")
s = s.replace("r.center('ROOM CODE', 0x50, COLORS.alt);", "r.center('HOST IP ADDRESS', 0x50, COLORS.alt);")
s = s.replace("r.center(mp.code, 0x62, COLORS.warning, 1, 4);", "r.center(mp.code, 0x62, COLORS.warning);")
s = s.replace("'Your opponent picks Multiplayer > Join Game and enters this code.'", "'Join Game on the other device and enter this IP address.'")
s = s.replace("'Connecting to the matchmaking server...'", "'Starting local LAN host...'")
s = s.replace("r.center(`Joining game ${mp.code}...`, 0x60, COLORS.text, blink ? ALPHA_M : 1);", "r.center(`Connecting to ${mp.code}...`, 0x60, COLORS.text, blink ? ALPHA_M : 1);")
main.write_text(s)
