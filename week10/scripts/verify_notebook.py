"""Execute all cells and save the verification copy under ignored runs/."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
path = root/'notebooks/10_agentic_tower_verification.ipynb'
nb = nbformat.read(path, as_version=4)
nbformat.validate(nb)
NotebookClient(nb, timeout=120, kernel_name='python3',
               resources={'metadata': {'path': str(path.parent)}}).execute()
out = root/'runs/verification/executed.ipynb'
out.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, out)
print('Executed all notebook cells:', out)
