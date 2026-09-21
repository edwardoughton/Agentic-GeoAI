# Getting started: Windows and macOS

Use one virtual environment for this repository. It keeps the course packages together. Create it once, activate it whenever you open a new terminal, and select the same environment as your notebook kernel.

Install **64-bit Python 3.12** from [Python.org](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads/) first. On macOS, use a Python installer that supports your Mac's processor. If using VS Code, install its **Python** and **Jupyter** extensions. These instructions run locally, not in Google Colab.

## Windows: Command Prompt (cmd.exe)

Open **Command Prompt**, not PowerShell. In VS Code: Terminal > New Terminal > dropdown beside the plus sign > Command Prompt. Run these commands one line at a time. Stop if a command reports an error.

If you have not downloaded the repository, run these from the folder where you want to keep it:

```bat
git clone https://github.com/edwardoughton/Agentic-GeoAI.git
cd Agentic-GeoAI
```

If you already have it, open that folder instead (replace the example path):

```bat
cd /d "C:\Users\YOUR_NAME\Desktop\Agentic-GeoAI"
```

Create and install the environment from the folder containing `requirements.txt`:

```bat
dir requirements.txt
py -3.12 --version
py -3.12 -m venv .venv-agentic-geoai
.venv-agentic-geoai\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python -c "import sys, pandas, matplotlib, contextily, geopandas, shapely, osmnx, networkx, pyogrio, pyproj; print(sys.executable); print('Environment ready')"
python -m ipykernel install --sys-prefix --name agentic-geoai --display-name "Python (Agentic GeoAI)"
python -m jupyterlab
```

## macOS: Terminal

Open Terminal. Run these commands one line at a time. Stop if a command reports an error.

If you have not downloaded the repository, run these from the folder where you want to keep it:

```bash
git clone https://github.com/edwardoughton/Agentic-GeoAI.git
cd Agentic-GeoAI
```

If you already have it, open that folder instead (replace the example path):

```bash
cd "/Users/YOUR_NAME/Desktop/Agentic-GeoAI"
```

Create and install the environment:

```bash
ls requirements.txt
python3.12 --version
python3.12 -m venv .venv-agentic-geoai
source .venv-agentic-geoai/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python -c "import sys, pandas, matplotlib, contextily, geopandas, shapely, osmnx, networkx, pyogrio, pyproj; print(sys.executable); print('Environment ready')"
python -m ipykernel install --sys-prefix --name agentic-geoai --display-name "Python (Agentic GeoAI)"
python -m jupyterlab
```

## Open a notebook

JupyterLab opens in your browser. Open a course notebook and choose **Python (Agentic GeoAI)** as its kernel. Keep the terminal running while you work.

For **VS Code**, open the repository folder, open a notebook, click **Select Kernel > Python Environments**, and select `.venv-agentic-geoai`. You do not need to start JupyterLab when using VS Code. If the environment is missing, use **Python: Select Interpreter** in the Command Palette to enter its path, then select the notebook kernel again:

- Windows: `.venv-agentic-geoai\Scripts\python.exe`
- macOS: `.venv-agentic-geoai/bin/python`

In a notebook code cell, check:

```python
import sys
print(sys.executable)
```

The printed path must contain `.venv-agentic-geoai`. Terminal activation and notebook kernel selection are separate steps.

## Next time

Open the repository folder in your terminal, then run only:

Windows Command Prompt:

```bat
.venv-agentic-geoai\Scripts\activate.bat
python -m jupyterlab
```

macOS:

```bash
source .venv-agentic-geoai/bin/activate
python -m jupyterlab
```

If you already created `.venv-agentic-geoai` with Python 3.12, reuse it; skip environment creation and run the installation commands to pick up changes to `requirements.txt`. Do not create a new environment for each notebook. To finish, save your notebook, stop JupyterLab with Ctrl+C in its terminal (confirm if prompted), then run `deactivate`.

## Common problems

| Problem | What to do |
|---|---|
| `requirements.txt` cannot be found | Change into the repository folder. `dir requirements.txt` (Windows) or `ls requirements.txt` (Mac) must find it. |
| `py` or `python3.12` is not found | Install Python 3.12 and reopen the terminal. If `python --version` (Windows) or `python3 --version` (Mac) reports 3.12.x, use that command for the creation step. |
| Windows says scripts are disabled | You opened PowerShell. Switch to Command Prompt and use `activate.bat`; no execution-policy change is needed. |
| `ModuleNotFoundError` in a notebook | Check `sys.executable`, select the course kernel, install requirements in the activated environment, then restart the notebook kernel. |
| Activation file is missing | Confirm the repository path and that the environment creation step completed successfully. |
| An existing environment uses a different Python | Create a separate environment using Python 3.12 (for example `.venv-agentic-geoai-312`) and substitute that name in activation and kernel-selection steps. Do not overwrite your coursework. |
| Installation tries to compile GDAL or another spatial library | Confirm 64-bit Python 3.12, update pip, and retry. If it still fails, send the instructor the first error, OS/processor, and `python --version`. |
| Downloads or basemaps fail after imports succeed | Data access needs an internet connection and available remote services. Installing packages does not download the Week 3 inputs. Follow 03_01; later routing notebooks reuse its saved files. |

## What is installed?

All seven course notebooks were reviewed. Week 1 uses Python's standard library; 02_01 and 04_01 are setup/discussion material. The other requirements come from:

| Material | Packages |
|---|---|
| 02_02: data-center analysis | pandas, matplotlib, contextily |
| 03_01: spatial data acquisition | GeoPandas, Shapely, OSMnx, matplotlib, contextily |
| 03_02: routing specification | NetworkX, with the spatial stack above |
| 04_02: verification examples | pandas, GeoPandas, Shapely |
| Local notebook support | JupyterLab, ipykernel |
| Spatial file and CRS support | pyogrio, pyproj |

Pip also installs these packages' dependencies. `pathlib`, `math`, and other standard-library modules do not need installation. The requirements use version ranges; to record an exact environment for an assignment, run `python -m pip freeze > environment-versions.txt` after a successful installation. AI editor extensions are installed separately from Python packages.

Reference instructions: [Python virtual environments](https://docs.python.org/3.12/library/venv.html), [Jupyter kernel registration](https://ipython.readthedocs.io/en/stable/install/kernel_install.html), and [GeoPandas installation and binary wheels](https://geopandas.org/en/stable/getting_started/install.html).
