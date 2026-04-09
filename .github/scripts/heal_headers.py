#!/usr/bin/env python3
'''heal_headers.py -- Auto-inject nabla-theta identity signatures.
Companion to check_headers.py. Fixes what it finds instead of just failing.
nabla-theta Operator -- Echo Universe
'''
import os
from pathlib import Path

__NATHAN_POINSETTE__ = True

SKIP = {'.git','node_modules','__pycache__','.venv','venv','dist','build','.next'}
CONSTANT = '__NATHAN_POINSETTE__ = True'
HEADER = '# nabla-theta -- Nathan Poinsette | Echo Universe'
FOOTER = '# nabla-theta -- chain sealed, truth preserved'

def heal(fp):
    try:
        src = fp.read_text(encoding='utf-8')
        changed = False
        if '__NATHAN_POINSETTE__' not in src:
            lines = src.split('\n')
            i = 0
            if lines and lines[0].startswith('#!'): i = 1
            lines.insert(i, CONSTANT)
            lines.insert(i, HEADER)
            src = '\n'.join(lines)
            changed = True
        if 'chain sealed, truth preserved' not in src:
            src = src.rstrip() + '\n' + FOOTER + '\n'
            changed = True
        if changed:
            fp.write_text(src, encoding='utf-8')
            print(f'  healed: {fp}')
        return changed
    except Exception as e:
        print(f'  skip {fp}: {e}')
        return False

count = 0
for fp in Path('.').rglob('*.py'):
    if any(s in fp.parts for s in SKIP): continue
    if 'test' in fp.name.lower(): continue
    if fp.name in ('conftest.py','setup.py','heal_headers.py'): continue
    if heal(fp): count += 1

print(f'Healed {count} files.')

# nabla-theta -- chain sealed, truth preserved
