# ComfyUI image for RTX 5090 (Blackwell, compute capability sm_120).
#
# Blackwell GPUs need a PyTorch build compiled for CUDA 12.8+; ComfyUI and its
# comfy_kitchen backend recommend CUDA 13.0 (cu130). Older images such as
# pytorch/pytorch:2.5.1-cuda12.1 do NOT contain sm_120 kernels and fail at startup.
#
# PyTorch pip wheels bundle their own CUDA runtime, so a slim Python base is
# enough. The host only needs a recent NVIDIA driver (>= 580 for CUDA 13.0).
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CUDA wheel index. Switch to cu128 if the host driver is older than 580.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu130

# Install PyTorch FIRST so ComfyUI's requirements.txt does not pull a CPU/old build.
RUN pip install --upgrade pip && \
    pip install torch torchvision torchaudio --index-url ${TORCH_INDEX_URL}

WORKDIR /app

# Pin a ComfyUI tag/commit for event reproducibility, e.g. --build-arg COMFYUI_REF=v0.3.x
ARG COMFYUI_REF=master
RUN git clone https://github.com/comfyanonymous/ComfyUI.git . && \
    git checkout ${COMFYUI_REF}

# torch is already satisfied, so pip keeps the CUDA 13 build installed above.
RUN pip install -r requirements.txt

# Fail the build early if the installed torch cannot target Blackwell.
RUN python -c "import torch; archs=torch.cuda.get_arch_list(); print('torch', torch.__version__, archs); assert 'sm_120' in archs, 'PyTorch build lacks sm_120 (RTX 5090) support'"

EXPOSE 8188

CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
