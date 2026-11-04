# Environment setup

## Quick start: what you have to do

Do this once on your laptop (~15 minutes, mostly waiting for downloads). Run every command in a terminal (PowerShell on Windows, Terminal on Mac/Linux).

**1. Install uv** (a fast Python package manager; it also downloads Python 3.12 for you)

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Mac / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Close and reopen the terminal afterwards, then check with `uv --version`.

**2. Download the project and go into its folder**
```bash
git clone <repo-url>
cd ML-for-Quantum-Error-Mitigation
```

**3. Create the environment**
```bash
uv venv --python 3.12 .venv
```
→ Creates a folder `.venv` inside the project containing a private copy of Python 3.12. It's separate from any other Python on your laptop, so nothing else gets broken. If you don't have Python 3.12, uv downloads it.

**4. Install the packages**
```bash
uv pip install -r setup/requirements.txt
```
→ Installs every package the project needs (Qiskit, IQM, Mitiq, scikit-learn, PyTorch, …) at **exactly** the versions in `requirements.txt`, into `.venv`. Everyone gets identical versions. This is the slow step (~1 GB).

**5. Activate the environment.** Do this **every time** you open a new terminal.

Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```
Mac / Linux:
```bash
source .venv/bin/activate
```
→ From now on, `python` in this terminal means the project's Python. You'll see `(.venv)` at the start of the prompt. Type `deactivate` to switch it off.
If PowerShell says "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

In VS Code you can skip this step: `Ctrl+Shift+P` → "Python: Select Interpreter" → choose the one inside `.venv`.

**6. Check that it works.** With the environment active, run:
```bash
python -c "import qiskit, qiskit_aer, mitiq, sklearn, torch, numpy; print('qiskit', qiskit.__version__, '| aer', qiskit_aer.__version__, '| mitiq', mitiq.__version__, '| sklearn', sklearn.__version__, '| torch', torch.__version__, '| numpy', numpy.__version__)"
```
Expected: `qiskit 2.1.2 | aer 0.17.2 | mitiq 1.1.0 | sklearn 1.9.1 | torch 2.15.0(+cpu) | numpy 2.2.6`

```bash
python -c "from iqm.qiskit_iqm import IQMFakeAdonis; b = IQMFakeAdonis(); print(b.num_qubits, 'qubits |', sorted(b.operation_names), '|', b.coupling_map)"
```
Expected: `5 qubits | ['cz', 'delay', 'id', 'measure', 'r'] | ...`

If both print without errors, you're done ✅. **Post a screenshot in the group chat.**

**Rules**
- Use Python **3.12**, not 3.13 or 3.14 (Mitiq doesn't support them).
- **Don't** `pip install qiskit-iqm` (it's outdated). IQM's Qiskit support is already included via `iqm-client[qiskit]`.
- Don't install or upgrade packages by hand. If you need a new package, ask; see "Updating packages" below.
- The `.venv` folder is never committed to git (it's in `.gitignore`).
- If something fails: check **Troubleshooting** at the bottom, then post the full error message in the chat.

---

The sections below give more detail and alternatives (plain pip, conda).
Everyone on the team uses **the same Python version and the same package versions** (from `requirements.txt`), so results and bugs are reproducible across laptops.

Takes ~15 minutes, mostly waiting for downloads (~1 GB, PyTorch is the biggest).

> Tested on 2026-11-04 on Windows 11 with Python 3.12. The versions below install together, the IQM 5-qubit simulator backend loads, and Mitiq gate folding works.

## What's in this folder

| File | What it is |
|---|---|
| `README.md` | These instructions |
| `requirements.in` | The short list of packages we *chose*. Edit this one. |
| `requirements.txt` | The full locked list (every package + exact version), generated from `requirements.in`. **Install from this one, never edit it by hand.** |

## Key versions

| Package | Version | Why it's pinned like this |
|---|---|---|
| Python | **3.12** | Mitiq does not support 3.13+ yet; IQM needs ≥ 3.11 |
| qiskit | 2.1.2 | IQM's adapter supports Qiskit < 2.2 |
| qiskit-aer | 0.17.2 | Simulator; IQM needs < 0.18 |
| iqm-client[qiskit] | 36.0.0 | IQM's Qiskit adapter, which contains the Lagrange backend and the fake 5-qubit backend |
| mitiq | 1.1.0 | Zero-noise extrapolation |
| numpy | 2.2.6 | Mitiq needs < 2.3 |
| scikit-learn | 1.9.1 | Linear regression, random forest |
| torch | 2.15.0 | MLP |

> ⚠️ **Do not `pip install qiskit-iqm`.** That package is no longer maintained (last release September 2025, only supports Qiskit < 1.3). Its code now lives in `iqm-client[qiskit]`, and you still import it as `iqm.qiskit_iqm`.

---

## Step 0 — Prerequisites (once per laptop)

1. **Git**: <https://git-scm.com/downloads>
2. **Python 3.12** (exactly 3.12.x, not 3.13 or 3.14):
   - Windows: installer from <https://www.python.org/downloads/>. Pick the latest 3.12.x and tick "Add python.exe to PATH". Check with `py -3.12 --version`.
   - macOS: `brew install python@3.12`, or the python.org installer.
   - Linux: `sudo apt install python3.12 python3.12-venv`, or your distro's equivalent.
3. **uv** (recommended, much faster than pip and can also install Python 3.12 for you): <https://docs.astral.sh/uv/getting-started/installation/>
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. **Editor**: VS Code with the *Python* and *Jupyter* extensions (or whatever you prefer).

## Step 1 — Get the repository

Once the shared repo exists:

```bash
git clone <repo-url>
cd ML-for-Quantum-Error-Mitigation
```

All commands below are run **from the repository root folder**.

## Step 2 — Create the environment

The environment lives in a folder called `.venv` inside the repo. It is git-ignored, so it is never committed.
Pick **one** option.

### Option A — uv (recommended)

```bash
uv venv --python 3.12 .venv
uv pip install -r setup/requirements.txt
```

`uv venv` downloads Python 3.12 automatically if you don't have it.

### Option B — plain Python + pip

Windows:
```powershell
py -3.12 -m venv .venv
```
macOS/Linux:
```bash
python3.12 -m venv .venv
```
Then activate it (Step 3) and run:
```bash
python -m pip install --upgrade pip
pip install -r setup/requirements.txt
```

### Option C — conda

```bash
conda create -n mlqem python=3.12 -y
conda activate mlqem
pip install -r setup/requirements.txt
```
(With conda, skip Step 3; `conda activate mlqem` is your activation command.)

## Step 3 — Activate the environment (every time you open a new terminal)

| Shell | Command |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Git Bash | `source .venv/Scripts/activate` |
| Windows cmd | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Your prompt should now start with `(.venv)`. To leave the environment: `deactivate`.

In VS Code: `Ctrl+Shift+P` → "Python: Select Interpreter" → pick the one in `.venv`.

## Step 4 — Register the environment in Jupyter

```bash
python -m ipykernel install --user --name mlqem --display-name "Python (mlqem)"
```
Then in Jupyter / VS Code notebooks, choose the kernel **"Python (mlqem)"**.

## Step 5 — Check that everything works

With the environment active, run these two commands.

**1. Versions**
```bash
python -c "import qiskit, qiskit_aer, mitiq, sklearn, torch, numpy; print('qiskit', qiskit.__version__, '| aer', qiskit_aer.__version__, '| mitiq', mitiq.__version__, '| sklearn', sklearn.__version__, '| torch', torch.__version__, '| numpy', numpy.__version__)"
```
Expected:
```
qiskit 2.1.2 | aer 0.17.2 | mitiq 1.1.0 | sklearn 1.9.1 | torch 2.15.0(+cpu) | numpy 2.2.6
```

**2. IQM fake 5-qubit backend (same chip layout as Lagrange)**
```bash
python -c "from iqm.qiskit_iqm import IQMFakeAdonis; b = IQMFakeAdonis(); print(b.num_qubits, 'qubits |', sorted(b.operation_names), '|', b.coupling_map)"
```
Expected (roughly): `5 qubits | ['cz', 'delay', 'id', 'measure', 'r'] | [[0, 2], [2, 0], [1, 2], ...]`

This shows:
- a **star**: every connection goes through qubit 2, the centre;
- native gates **`r`** (IQM's PRX rotation) and **`cz`**.

Mitiq may print a few warnings on import; that's fine. If both commands print without an error, you're done. ✅
Post a screenshot in the group chat so we know everyone is set up.

## Step 6 — Lagrange access (later, when we get it)

- Ask the lab staff for the **server URL** of Lagrange and whether an **access token** is needed.
- **Never commit tokens or passwords.** Put them in a file called `.env` in the repo root (it is git-ignored) or in an environment variable.
- The connection itself goes through `iqm.qiskit_iqm` (IQMProvider). We'll add a short guide here once we know the lab's procedure.

---

## Updating packages (only one person does this, then commits)

1. Add or change a line in `setup/requirements.in`.
2. Regenerate the lock file:
   ```bash
   uv pip compile setup/requirements.in --universal --python-version 3.12 -o setup/requirements.txt
   ```
3. Commit **both** files and tell the team.
4. Everyone else updates with:
   ```bash
   uv pip sync setup/requirements.txt
   ```
   (or `pip install -r setup/requirements.txt` with Option B/C)

Before raising any version, check the constraints in the "Key versions" table. Qiskit, Aer, numpy and Python are all held back by IQM or Mitiq.

## Troubleshooting

| Problem | Fix |
|---|---|
| `mitiq` fails to install / "requires Python <3.13" | You're on Python 3.13+. Delete `.venv` and recreate it with 3.12 (Step 2). |
| PowerShell: "running scripts is disabled on this system" | Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| `ModuleNotFoundError: No module named 'iqm'` | The environment isn't active, or VS Code is using another interpreter (Step 3). |
| `ModuleNotFoundError: No module named 'ply'` when using Mitiq with Qiskit | Install from `requirements.txt` (it includes `ply`), not by hand. |
| Linux: PyTorch download is huge (CUDA) | Fine to ignore, or install the CPU build first: `pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`, then the requirements. |
| Something else | Delete `.venv`, repeat Steps 2–5, then ask in the chat with the full error message. |

## Known issue for the ZNE work (not a setup problem)

Mitiq **cannot read IQM's native `r` gate**. Calling `fold_gates_at_random` on a circuit already transpiled for the IQM backend raises `CircuitConversionError`.
Folding works on circuits transpiled to `rx, ry, rz, cz` on the same coupling map (tested: 2 CZ → 6 CZ at scale factor 3).
WS2 must choose between:
- folding in that basis and then making sure the final IQM translation keeps the extra CZs; or
- doing the (simple) CZ folding ourselves and using Mitiq only for the extrapolation.

Tracked as risk R4 in `planning/PLAN.md`.
