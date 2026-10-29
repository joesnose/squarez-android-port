from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

folder = Path(__file__).parent
art = Image.open(BytesIO(base64.b64decode((folder / 'icon-image.b64').read_text().strip()))).convert('RGB')
canvas = Image.new('RGBA', (256, 256), (3, 13, 28, 255))
art.thumbnail((256, 256), Image.Resampling.LANCZOS)
canvas.paste(art, ((256 - art.width) // 2, (256 - art.height) // 2))
canvas.save(folder / 'icon.ico', format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Created Windows icon')
