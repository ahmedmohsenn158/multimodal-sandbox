#!/bin/bash
set -e

echo "================================="
echo "Multimodal Sandbox GPU Check"
echo "================================="

if ! command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU: Not Found (nvidia-smi missing)"
    echo "Status:     FAIL"
    exit 1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -n 1)

echo "NVIDIA GPU: $GPU_NAME"
echo "VRAM:       $VRAM"

if nvidia-smi | grep -q "CUDA Version"; then
    echo "CUDA:       Available"
else
    echo "CUDA:       Not Available"
    echo "Status:     FAIL"
    exit 1
fi

if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "Docker GPU: Available"
else
    echo "Docker GPU: Not Available"
    echo "Status:     FAIL"
    exit 1
fi

echo "Status:     PASS"
