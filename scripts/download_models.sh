#!/bin/bash
set -e

# Load environment variables
if [ -f "../.env" ]; then
    source ../.env
fi

if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN is not set in .env"
    exit 1
fi

echo "Checking HF_TOKEN..."
echo "Token found."

PYTHON="../.venv/Scripts/python.exe"

echo ""
echo "Verify model license acknowledgement requirements."
echo "Ensure you have accepted the Llama 3.2 Community License on Hugging Face."
read -p "Press Enter to continue..."

echo ""
echo "Downloading Llama 3.2 11B Vision..."

"../.venv/Scripts/hf.exe" download \
    meta-llama/Llama-3.2-11B-Vision-Instruct \
    --local-dir "../models/Llama-3.2-11B-Vision-Instruct" \
    --token "$HF_TOKEN"

echo "Verifying Llama model files..."

if [ ! -d "../models/Llama-3.2-11B-Vision-Instruct" ]; then
    echo "Error: Llama model files not found."
    exit 1
fi

echo "Llama download complete."

echo ""
echo "Downloading FLUX.1-schnell..."

"../.venv/Scripts/hf.exe" download \
    black-forest-labs/FLUX.1-schnell \
    --local-dir "../models/FLUX.1-schnell" \
    --token "$HF_TOKEN"

echo "Verifying FLUX model files..."

if [ ! -d "../models/FLUX.1-schnell" ]; then
    echo "Error: FLUX model files not found."
    exit 1
fi

echo "FLUX download complete."

echo ""
echo "Storage requirements:"
echo "Llama 3.2 11B Vision: ~22GB"
echo "FLUX.1-schnell: ~24GB"
echo "Total expected: ~46GB"