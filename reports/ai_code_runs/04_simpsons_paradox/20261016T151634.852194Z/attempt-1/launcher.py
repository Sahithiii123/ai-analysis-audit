from __future__ import annotations
import runpy
import sys
import traceback
from pathlib import Path

workspace = Path('/workspace')
try:
    runpy.run_path(str(workspace / 'pasted_code.py'), run_name='__main__')
except BaseException:
    traceback.print_exc()
    sys.exit(1)
finally:
    try:
        import matplotlib.pyplot as plt
        figure_dir = workspace / 'figures'
        figure_dir.mkdir(exist_ok=True)
        for number in plt.get_fignums():
            figure = plt.figure(number)
            figure.savefig(figure_dir / f'figure-{number:03d}.png', bbox_inches='tight')
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
