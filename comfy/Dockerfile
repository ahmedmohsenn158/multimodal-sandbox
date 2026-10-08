FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the latest ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8188

CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
