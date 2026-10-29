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
