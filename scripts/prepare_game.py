"""Copy upstream web game into Android assets and add player-grab touch controls."""
from pathlib import Path
import shutil
import sys

source, target = map(Path, sys.argv[1:3])
if not (source / "index.html").exists():
    raise SystemExit("Missing upstream index.html")
shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git", ".github", "tests", "scripts", "node_modules"), dirs_exist_ok=True)

path = target / "src" / "touch.js"
s = path.read_text()
needle = "    this.setVisible(matchMedia('(pointer: coarse)').matches);"
assert needle in s, "Upstream touch.js changed; review integration"
s = s.replace(needle, """    this.direct = null;
    // Capture-phase listener runs before PSP joystick overlay can intercept the player grab.
    document.addEventListener('pointerdown', e => this.grabPlayer(e), true);
    document.addEventListener('pointermove', e => this.dragPlayer(e), true);
    for (const type of ['pointerup', 'pointercancel'])
      document.addEventListener(type, e => this.releasePlayer(e), true);
""" + needle)
needle = "  setVisible(on) {"
assert needle in s
s = s.replace(needle, """  gamePoint(e) {
    const c = document.getElementById('screen');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    if (!r.width || !r.height || e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return null;
    return { x: (e.clientX - r.left) * c.width / r.width, y: (e.clientY - r.top) * c.height / r.height };
  }

  grabPlayer(e) {
    if (e.pointerType === 'mouse' || this.direct || !this.app || this.app.screen !== 'game') return;
    const g = this.app.game;
    if (!g || g.paused || g.state !== 0) return;
    const p = this.gamePoint(e);
    if (!p) return;
    const padding = 8; // game pixels on every side
    if (p.x < g.px - padding || p.x > g.px + g.psize + padding || p.y < g.py - padding || p.y > g.py + g.psize + padding) return;
    this.direct = { id: e.pointerId, x: p.x - g.px, y: p.y - g.py, targetX: g.px, targetY: g.py };
    e.preventDefault();
    e.stopImmediatePropagation();
  }

  dragPlayer(e) {
    if (!this.direct || this.direct.id !== e.pointerId) return;
    const p = this.gamePoint(e);
    if (p) { this.direct.targetX = p.x - this.direct.x; this.direct.targetY = p.y - this.direct.y; }
    e.preventDefault();
    e.stopImmediatePropagation();
  }

  releasePlayer(e) {
    if (!this.direct || this.direct.id !== e.pointerId) return;
    this.direct = null;
    e.preventDefault();
    e.stopImmediatePropagation();
  }

""" + needle)
s = s.replace("    this.pointers.clear();", "    this.direct = null;\n    this.pointers.clear();", 1)
path.write_text(s)

path = target / "src" / "main.js"
s = path.read_text()
needle = "    this.touch = new TouchControls(() => {"
assert needle in s
s = s.replace(needle, needle)  # attach app immediately after constructor, below
needle = "    if (this.touch.visible) this.device = 'touch';"
assert needle in s
s = s.replace(needle, "    this.touch.app = this.app;\n" + needle)
needle = "    if (this.capture) this.updateCapture();"
assert needle in s
s = s.replace(needle, """    if (t.direct && this.app.screen === 'game' && this.app.game && !this.app.game.paused) {
      const g = this.app.game;
      const d = t.direct;
      const dx = d.targetX - g.px, dy = d.targetY - g.py;
      // Feed normal analog input so gameplay speed limits and collision logic remain intact.
      if (Math.abs(dx) > 1) ax = dx < 0 ? 0 : 255;
      else ax = 0x82;
      if (Math.abs(dy) > 1) ay = dy < 0 ? 0 : 255;
      else ay = 0x82;
      this.device = 'touch';
    }
""" + needle)
path.write_text(s)

# Android's embedded secure-origin WebView doesn't need the PWA service worker.
pwa = target / "src" / "pwa.js"
if pwa.exists():
    code = pwa.read_text()
    code = "'use strict';\n// Disabled in Android wrapper; local assets are served by WebViewAssetLoader.\n"
    pwa.write_text(code)
print("Copied game and installed direct touch controls with 8px padding.")
