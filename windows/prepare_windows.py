import shutil
import sys
from pathlib import Path
source, dest = map(Path, sys.argv[1:3])
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(source, dest, ignore=shutil.ignore_patterns('.git'))
