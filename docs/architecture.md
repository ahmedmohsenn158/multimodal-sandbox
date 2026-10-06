# Multimodal Sandbox Architecture

## Services

1. **Gateway**: Nginx reverse proxy routing traffic to appropriate containers.
2. **Web**: React frontend portal with Vision Chat and Image Studio.
3. **Sandbox API**: FastAPI backend acting as orchestrator, managing GPU locks, queues, and safety filters.
4. **Open WebUI**: Chat UI interface connected to VLM.
5. **VLM Server**: vLLM instance serving Llama-3.2-11B-Vision-Instruct.
6. **ComfyUI**: Image generation backend running FLUX.1-schnell.

## Principles
- **Resource Management**: Uses a lock/queue to prevent VLM and Image generation from crashing due to OOM.
- **Safety**: Multi-layered prompt sanitization.
- **Local First**: All inference is done on the host RTX 5090.
