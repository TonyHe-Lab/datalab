#!/usr/bin/env bash
set -euo pipefail

echo "Installing spaCy and downloading requested model (default: en_core_web_sm)..."
python -m pip install --upgrade pip
python -m pip install "spacy>=3.5.0"

# MODEL env var can be set to en_core_web_sm or en_core_web_trf (trf requires extra deps)
MODEL=${1:-${SPACY_MODEL:-en_core_web_sm}}
echo "Requested model: $MODEL"

if [ "$MODEL" = "en_core_web_trf" ]; then
	echo "Installing transformer dependencies for en_core_web_trf..."
	python -m pip install "torch" "transformers"
fi

python -m spacy download "$MODEL"

echo "spaCy setup complete (model: $MODEL)."