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

# "../.venv/Scripts/hf.exe" download \
#     meta-llama/Llama-3.2-11B-Vision-Instruct \
#     --local-dir "../models/Llama-3.2-11B-Vision-Instruct" \
#     --token "$HF_TOKEN"

# echo "Verifying Llama model files..."

# if [ ! -d "../models/Llama-3.2-11B-Vision-Instruct" ]; then
#     echo "Error: Llama model files not found."
#     exit 1
# fi

# echo "Llama download complete."

echo ""
echo "Downloading FLUX.1-schnell (All-in-one FP8 checkpoint)..."

"../.venv/Scripts/hf.exe" download \
    Comfy-Org/flux1-schnell \
    flux1-schnell-fp8.safetensors \
    --local-dir "../models" \
    --token "$HF_TOKEN"

echo "Verifying FLUX model files..."

if [ ! -f "../models/flux1-schnell-fp8.safetensors" ]; then
    echo "Error: FLUX model file not found."
    exit 1
fi

echo "FLUX download complete."

echo ""
echo "Storage requirements:"
echo "Llama 3.2 11B Vision: ~22GB"
echo "FLUX.1-schnell (FP8): ~17GB"
echo "Total expected: ~39GB"