# tracklet — one-command interface (see README for the reproduce recipe)
.PHONY: setup fetch run test test-golden build clean-room clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

# Create the virtualenv and install tracklet (editable) + dev deps.
# Stranger-reproducible: `make setup` then `./scripts/install_indexes.sh` for the solver gate.
setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip wheel
	$(PIP) install -e ".[dev]"
	@echo "venv ready. Plate-solver gate (one-time): ./scripts/install_indexes.sh"

# One-shot: fetch frozen real-data fixtures (TLE + Gaia cone). Online; run once, then offline.
fetch:
	$(PY) scripts/fetch_fixtures.py

# The one command: synthetic scene -> pipeline -> out/{residual.txt, overlay.png, report.md}.
run:
	$(PY) -m tracklet.run $(ARGS)

# Unit suite that needs NO solver installed.
test:
	$(PY) -m pytest -m "not solver" -q

# The @solver golden e2e (needs solve-field + indexes): render frozen scene -> residual < threshold.
test-golden:
	$(PY) -m pytest -m solver -q

# Build the wheel + sdist offline (no PyPI build-isolation; reuses the dev-extra build backend).
# Run `make setup` first so build/setuptools/wheel are present in the venv.
build:
	$(PY) -m build --no-isolation

# Autonomous clean-machine proof: fresh temp clone + fresh python3.14 venv + NON-editable
# `pip install . -c requirements.lock` -> the installed `tracklet` CLI reproduces the synthetic
# residual < 10" + the non-solver suite green from the install. Reuses the host's solve-field +
# wired indexes (loud remediation if absent). Hermetic; never touches the dev venv; never pushes.
# Run on a CLEAN tree — it clones the COMMITTED HEAD.
clean-room:
	bash scripts/clean_room_reproduce.sh

clean:
	rm -rf out/*.fits out/*.png out/*.md out/residual.txt
	rm -rf dist/ build/
