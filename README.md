# ML for Quantum Error Mitigation

Reproduction of [Liao et al., *Machine Learning for Practical Quantum Error Mitigation* (2023)](https://arxiv.org/abs/2309.17368) on IQM hardware, as a team project at Politecnico di Torino.

**Idea:** run circuits on a noisy device, then train a model that maps the noisy expectation values ⟨Zᵢ⟩ plus circuit features (gate counts, rotation-angle histogram) to the ideal values. Following the paper, the main model is a random forest, with linear regression as a baseline.

**Status:** work in progress. Noisy simulation on `IQMFakeAdonis`; runs on Politecnico's IQM computer (Lagrange) are the target.

## Structure
```
mlqem/
  circuits/    random circuit generation and compilation to IQM native gates
  simulation/  ideal (exact) and noisy <Z_i> values
  models/      features, training, metrics
setup/         environment setup (uv, Python 3.12) and connection checks
```

## Quick start
```bash
uv venv --python 3.12 .venv
uv pip install -r setup/requirements.txt
python setup/check_env.py
```
See `setup/README.md` for the full setup, including access to the IQM machine.
