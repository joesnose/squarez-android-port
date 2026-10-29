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
