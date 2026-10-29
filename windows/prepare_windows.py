import shutil
import sys
from pathlib import Path
source, dest = map(Path, sys.argv[1:3])
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(source, dest, ignore=shutil.ignore_patterns('.git'))
game = dest / 'src' / 'game.js'
code = game.read_text()
needle = "    this.stat('pixels', Math.abs(this.px - x0) + Math.abs(this.py - y0));"
assert needle in code
replacement = """
    const mouse = window.squarezMouseTarget;
    if (mouse && !this.paused) {
      this.px = Math.max(0, Math.min(FIELD_RIGHT - this.psize, Math.round(mouse.x - this.psize / 2)));
      this.py = Math.max(0, Math.min(FIELD_BOTTOM - this.psize, Math.round(mouse.y - this.psize / 2)));
      if (this.px !== x0 || this.py !== y0) this.moved = true;
    }
"""
game.write_text(code.replace(needle, replacement + needle))
index = dest / 'index.html'
html = index.read_text()
assert '</body>' in html
script = """
<script>
(() => {
  const canvas = document.getElementById('screen');
  const update = e => {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    window.squarezMouseTarget = {
      x: (e.clientX - rect.left) * canvas.width / rect.width,
      y: (e.clientY - rect.top) * canvas.height / rect.height
    };
  };
  canvas.addEventListener('mousemove', update);
  canvas.addEventListener('mouseenter', update);
  canvas.addEventListener('mouseleave', () => { window.squarezMouseTarget = null; });
})();
</script>
"""
index.write_text(html.replace('</body>', script + '</body>'))

main = dest / 'src' / 'main.js'
code = main.read_text()
assert "  { kind: 'screen', screen: 'credits', label: 'Credits' }," in code
code = code.replace("  { kind: 'screen', screen: 'credits', label: 'Credits' },", "  { kind: 'screen', screen: 'credits', label: 'Credits' },\n  { kind: 'exit', label: 'Exit' },", 1)
assert "  { key: 'padsetup', label: 'Controller Setup', action: true }," in code
code = code.replace("  { key: 'padsetup', label: 'Controller Setup', action: true },", "  { key: 'padsetup', label: 'Controller Setup', action: true },\n  { key: 'fullscreen', label: 'Fullscreen:', bool: true },", 1)
assert "    if (item.kind === 'screen') {" in code
code = code.replace("    if (item.kind === 'screen') {", "    if (item.kind === 'exit') {\n      window.close();\n      return;\n    }\n    if (item.kind === 'screen') {", 1)
assert "      if (changed && row.key === 'vibration'" in code
code = code.replace("      if (changed && row.key === 'vibration'", """      if (changed && row.key === 'fullscreen') {
        if (o.fullscreen) document.documentElement.requestFullscreen().catch(() => { o.fullscreen = false; this.toast('Fullscreen unavailable'); });
        else if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      }
      if (changed && row.key === 'vibration'""", 1)
assert "      Object.assign(this.options, DEFAULT_OPTIONS);" in code
code = code.replace("      Object.assign(this.options, DEFAULT_OPTIONS);", """      Object.assign(this.options, DEFAULT_OPTIONS);
      this.options.fullscreen = false;
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});""", 1)
assert "    this.options = { ...DEFAULT_OPTIONS, ...loadJSON('squarez.options', {}) };" in code
code = code.replace("    this.options = { ...DEFAULT_OPTIONS, ...loadJSON('squarez.options', {}) };", """    this.options = { ...DEFAULT_OPTIONS, ...loadJSON('squarez.options', {}), fullscreen: false };
    document.addEventListener('fullscreenchange', () => {
      this.options.fullscreen = !!document.fullscreenElement;
    });""", 1)
main.write_text(code)

# Expose menu lengths so pointer hit testing follows upstream menu layout.
main = dest / 'src' / 'main.js'
code = main.read_text()
marker = 'class App {'
assert marker in code
code = code.replace(marker, 'window.squarezMenuLayout = { menuCount: MENU_ITEMS.length, optionCount: OPTION_ROWS.length };\n' + marker, 1)
main.write_text(code)

index = dest / 'index.html'
html = index.read_text()
pointer_script = """
<script>
(() => {
  const canvas = document.getElementById('screen');
  const position = event => {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * canvas.width / rect.width,
      y: (event.clientY - rect.top) * canvas.height / rect.height
    };
  };
  const indexAt = (y, start, step, count) => {
    const n = Math.round((y - start) / step);
    return n >= 0 && n < count && Math.abs(y - (start + n * step)) <= step / 2 ? n : -1;
  };
  const input = action => ({
    pressed: key => key === action,
    nav: key => key === action
  });
  const select = (app, point, activate) => {
    const layout = window.squarezMenuLayout;
    if (!layout) return false;
    if (app.screen === 'menu') {
      if (app.timedMenu) {
        const n = indexAt(point.y, 0x41 + app.menuIndex * 12, 10, 5);
        if (n >= 0 && point.x >= 0x140) {
          app.timedIndex = n;
          if (activate) app.updateMenu(input('accept'));
          return true;
        }
        return false;
      }
      const n = indexAt(point.y, 0x41, 12, layout.menuCount);
      if (n >= 0 && point.x >= 0xc0) {
        app.menuIndex = n;
        if (activate) app.updateMenu(input('accept'));
        return true;
      }
    }
    if (app.screen === 'options') {
      const n = indexAt(point.y, 0x1a, 15, layout.optionCount + 1);
      if (n >= 0 && point.x >= 0x10) {
        app.optionIndex = n;
        if (activate) app.updateOptions(input(point.x > 0xc0 && n < layout.optionCount ? 'right' : 'accept'));
        return true;
      }
    }
    if (app.screen === 'multi') {
      const rows = [0x24, 0x32, 0x48, 0x56];
      const n = rows.findIndex(y => Math.abs(point.y - y) <= 7);
      if (n >= 0 && point.x >= 0x10) {
        app.multiRow = n;
        if (activate) app.updateMulti(input(n < 2 ? 'right' : 'accept'));
        return true;
      }
    }
    if (app.screen === 'custom') {
      const n = indexAt(point.y, 0x2c, 12, Math.min(17, app.customGames.length - app.customTop));
      if (n >= 0 && point.x >= 0x10) {
        app.customIndex = app.customTop + n;
        if (activate) app.updateCustom(input('accept'));
        return true;
      }
    }
    if (app.screen === 'game' && app.game && app.game.paused) {
      const n = indexAt(point.y, 0x28, 12, app.pauseItems().length);
      if (n >= 0 && point.x >= 0x10) {
        app.pauseIndex = n;
        if (activate) app.updateGame(input('accept'));
        return true;
      }
    }
    return false;
  };
  canvas.addEventListener('mousemove', e => {
    const app = window.squarez;
    if (app && app.screen !== 'game') select(app, position(e), false);
    canvas.style.cursor = app && ['menu', 'options', 'multi', 'custom'].includes(app.screen) ? 'pointer' : 'default';
  });
  canvas.addEventListener('click', e => {
    const app = window.squarez;
    if (!app || app.screen === 'loading') return;
    if (select(app, position(e), true)) return;
    if (app.screen === 'instructions') app.page = Math.min(4, app.page + 1);
    else if (app.screen === 'highscores') app.updateHighscores(input('pageRight'));
    else if (app.screen === 'credits') app.screen = 'menu';
  });
  canvas.addEventListener('contextmenu', e => {
    e.preventDefault();
    const app = window.squarez;
    if (!app) return;
    if (app.screen === 'menu' && app.timedMenu) app.timedMenu = false;
    else if (app.screen === 'options') app.updateOptions(input('back'));
    else if (app.screen !== 'game' && app.screen !== 'menu') app.screen = 'menu';
  });
})();
</script>
"""
index.write_text(html.replace('</body>', pointer_script + '</body>'))
