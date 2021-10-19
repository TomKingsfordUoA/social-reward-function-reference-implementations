#!/bin/bash

cd "$(dirname "$0")/.."
set -e

#echo '=== Linting ==='
#flake8 srf_reference_implementations *.py

#echo '=== Static Type Checking ==='
#mypy --strict srf_reference_implementations setup.py

echo '=== Testing ==='
pytest -v srf_reference_implementations

echo '=== Checking Manifest ==='
check-manifest -v

echo '=== Checking setup.py ==='
python setup.py check

echo '=== Smoke Test of CLI ==='
rm -r test_output_dir || true
mkdir test_output_dir
PYTHONPATH=$(pwd) python3 srf_reference_implementations/cli.py -t srf_reference_implementations/interfaces/test_resources/GENEA_sample_transcript.json -o test_output_dir
rm -r test_output_dir || true

echo '=== Check for FIXME comments ==='
(! grep -r -i -e "#\s*FIXME" . --exclude-dir=venv --exclude-dir=pymo) || exit 1

echo "SUCCESS"