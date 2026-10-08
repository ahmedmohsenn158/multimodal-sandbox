FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the latest ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Patch comfy_kitchen typing issue for PyTorch custom_ops
RUN find /opt/conda/lib/ -name "*.py" -path "*/comfy_kitchen/*" -exec sed -i 's/list\[int\]/typing.List\[int\]/g' {} + && \
    find /opt/conda/lib/ -name "*.py" -path "*/comfy_kitchen/*" -exec sed -i '1s/^/import typing\n/' {} +

EXPOSE 8188

CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
