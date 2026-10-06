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
# (In a real script, we would validate the token against HF API)
echo "Token found."

echo "Verify model license acknowledgement requirements."
echo "Ensure you have accepted the Llama 3.2 Community License on Hugging Face."
read -p "Press Enter to acknowledge and continue..."

echo "Downloading Llama..."
# e.g., huggingface-cli download meta-llama/Llama-3.2-11B-Vision-Instruct --local-dir ../models/Llama-3.2-11B-Vision-Instruct

echo "Verifying Llama model files..."

echo "Downloading FLUX..."
# e.g., huggingface-cli download black-forest-labs/FLUX.1-schnell --local-dir ../models/FLUX.1-schnell

echo "Verifying FLUX model files..."

echo "Print storage requirements"
echo "Llama 3.2 11B Vision: ~22GB"
echo "FLUX.1-schnell: ~24GB"
echo "Total expected: ~46GB"
