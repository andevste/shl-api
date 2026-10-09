# Justfile for shl-api
# Run `just` to list all recipes.

set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

venv     := ".venv"
bin      := venv / "bin"
python   := bin / "python"
pip      := bin / "pip"
sys_py   := env_var_or_default("PYTHON", "python3")
src      := "src"
tests    := "tests"

# List all available recipes
default:
    @just --list --unsorted

# ─── Environment ────────────────────────────────────────────────────────────

# Create the virtual environment (if missing)
venv:
    @test -x {{python}} || {{sys_py}} -m venv {{venv}}
    @echo "venv ready: {{venv}}"

# Create venv and install package with all dev + cli extras (editable)
install: venv
    {{pip}} install --upgrade pip
    {{pip}} install -e ".[dev,cli]"

# Alias for install
setup: install

# Upgrade all installed dependencies to latest allowed versions
upgrade: venv
    {{pip}} install --upgrade -e ".[dev,cli]"

# Show installed packages in the venv
deps:
    {{pip}} list

# ─── Testing ────────────────────────────────────────────────────────────────

# Run offline unit tests (excludes live API tests)
test *args:
    {{python}} -m pytest -m "not live" {{args}}

# Run only live integration tests against www.shl.se
test-live *args:
    {{python}} -m pytest -m live {{args}}

# Run the whole test suite (unit + live)
test-all *args:
    {{python}} -m pytest {{args}}

# Run tests with coverage report (terminal + HTML in htmlcov/)
cov *args:
    {{python}} -m pytest -m "not live" --cov --cov-report=term-missing --cov-report=html {{args}}

# Re-run only the tests that failed last time
test-failed:
    {{python}} -m pytest --lf

# ─── Code quality ───────────────────────────────────────────────────────────

# Lint with ruff
lint:
    {{bin}}/ruff check {{src}} {{tests}}

# Auto-fix lint issues
lint-fix:
    {{bin}}/ruff check --fix {{src}} {{tests}}

# Format code with ruff
fmt:
    {{bin}}/ruff format {{src}} {{tests}}
    {{bin}}/ruff check --select I --fix {{src}} {{tests}}

# Check formatting without changing files
fmt-check:
    {{bin}}/ruff format --check {{src}} {{tests}}

# Static type checking with mypy
typecheck:
    {{bin}}/mypy

# Run all checks: lint, format check, typecheck and unit tests
check: lint fmt-check typecheck test

# Fix everything that can be fixed automatically
fix: lint-fix fmt

# ─── Build & release ────────────────────────────────────────────────────────

# Build sdist and wheel into dist/
build: clean-build
    {{python}} -m build
    @ls -lh dist/

# Validate built distributions (metadata, README rendering)
check-dist: build
    {{bin}}/twine check dist/*

# Upload to TestPyPI
publish-test: check-dist
    {{bin}}/twine upload --repository testpypi dist/*

# Upload to PyPI (asks for confirmation)
[confirm]
publish: check check-dist
    {{bin}}/twine upload dist/*

# Print current package version
version:
    @grep -m1 '^version' pyproject.toml | cut -d'"' -f2

# Bump version in pyproject.toml and __init__.py, e.g. `just bump 0.2.0`
bump new_version:
    sed -i 's/^version = ".*"/version = "{{new_version}}"/' pyproject.toml
    sed -i 's/^__version__ = ".*"/__version__ = "{{new_version}}"/' {{src}}/shl/__init__.py
    @echo "Version bumped to {{new_version}}"

# Commit version bump and create git tag v<version>
release new_version: check (bump new_version)
    git add pyproject.toml {{src}}/shl/__init__.py
    git commit -m "Release v{{new_version}}"
    git tag -a "v{{new_version}}" -m "Release v{{new_version}}"
    @echo "Tagged v{{new_version}}. Push with: git push && git push --tags"

# ─── Run ────────────────────────────────────────────────────────────────────

# Run the shl CLI, e.g. `just run standings` or `just run team FBK --json`
run *args:
    {{bin}}/shl {{args}}

# Quick smoke test of the CLI against the live API
smoke:
    {{bin}}/shl teams
    {{bin}}/shl standings
    {{bin}}/shl last
    {{bin}}/shl next

# Open a Python REPL with an SHLClient instance named `client`
repl:
    {{python}} -i -c "from shl import *; client = SHLClient(); print('client = SHLClient() ready')"

# ─── CI ─────────────────────────────────────────────────────────────────────

# Everything CI should run: install, checks, live tests, build
ci: install check test-live check-dist

# ─── Cleanup ────────────────────────────────────────────────────────────────

# Remove build artifacts
clean-build:
    rm -rf build/ dist/ *.egg-info {{src}}/*.egg-info

# Remove caches, coverage and build artifacts
clean: clean-build
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
    find . -path ./{{venv}} -prune -o -type d -name __pycache__ -exec rm -rf {} +

# Remove everything including the virtual environment
[confirm]
clean-all: clean
    rm -rf {{venv}}
