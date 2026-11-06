# Environment setup

Run the commands in a terminal (PowerShell on Windows), from the project folder.

## 1. Install uv

Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Mac / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then reopen the terminal.

## 2. Clone the repo

```bash
git clone https://github.com/TucanoCode04/ML-for-Quantum-Error-Mitigation.git
cd ML-for-Quantum-Error-Mitigation
```

## 3. Create the environment and install the packages

```bash
uv venv --python 3.12 .venv
uv pip install -r setup/requirements.txt
uv pip install --no-deps lagrangeclient==0.1.3 --index-url https://gitlab.linksfoundation.com/api/v4/projects/1709/packages/pypi/simple
```

The last line installs the lab's login tool for Lagrange (PoliTo SSO).

## 4. Activate the environment (every new terminal)

Windows: `.venv\Scripts\Activate.ps1`
Mac / Linux: `source .venv/bin/activate`

If PowerShell blocks it, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 5. Test it

```bash
python setup/check_env.py
python setup/check_lagrange.py
```

The second one prints a link: open it and log in with PoliTo SSO. It only connects to Lagrange, it doesn't run anything on the machine.

If everything says PASS, post a screenshot in the chat. If something fails, bring your laptop to the next meeting.

## Rules

- Python **3.12** only (not 3.13+).
- Don't install `qiskit-iqm` (outdated, already replaced by `iqm-client[qiskit]`).
- Don't install or upgrade packages by hand. New packages go in `requirements.in`, then the lock file is regenerated with:
  `uv pip compile setup/requirements.in --universal --python-version 3.12 -o setup/requirements.txt`
