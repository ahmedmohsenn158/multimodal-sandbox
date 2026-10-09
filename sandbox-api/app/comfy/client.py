"""Small, defensive client for the local ComfyUI HTTP API."""

import json
import os
import secrets
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import requests

COMFY_ENDPOINT = os.getenv("COMFY_ENDPOINT", "http://comfyui:8188").rstrip("/")
WORKFLOWS_DIR = (
    Path("/workflows")
    if Path("/workflows").is_dir()
    else Path("./comfy/workflows")
)
REQUEST_TIMEOUT_SECONDS = float(os.getenv("COMFY_REQUEST_TIMEOUT_SECONDS", "30"))
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1536"))


class ComfyClient:
    def __init__(
        self,
        base_url: str | None = None,
        workflows_dir: Path | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or COMFY_ENDPOINT).rstrip("/")
        self.workflows_dir = Path(workflows_dir or WORKFLOWS_DIR)
        self.timeout = timeout or REQUEST_TIMEOUT_SECONDS

    def check_health(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def load_workflow_template(
        self, template_name: str = "flux_schnell_txt2img.json"
    ) -> dict[str, Any]:
        # Do not allow a caller to supply a path outside the configured workflow folder.
        if Path(template_name).name != template_name:
            raise ValueError("Workflow template must be a filename, not a path")
        path = self.workflows_dir / template_name
        if not path.is_file():
            raise FileNotFoundError(
                f"ComfyUI workflow not found: {path}. Check the /workflows volume mount."
            )
        try:
            with path.open("r", encoding="utf-8") as file:
                workflow = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid workflow JSON at {path}: {exc}") from exc
        if not isinstance(workflow, dict):
            raise ValueError(f"Workflow at {path} must contain a JSON object")
        return workflow

    @staticmethod
    def _validate_dimensions(width: int, height: int) -> None:
        for name, value in (("width", width), ("height", height)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
            if value < 512 or value > MAX_IMAGE_DIMENSION:
                raise ValueError(
                    f"{name} must be between 512 and {MAX_IMAGE_DIMENSION} pixels"
                )
            if value % 8 != 0:
                raise ValueError(f"{name} must be divisible by 8")

    @staticmethod
    def _normalize_seed(seed: int | None) -> int:
        # The UI/API use -1 as the random-seed sentinel. ComfyUI requires >= 0.
        if seed is None or seed == -1:
            return secrets.randbelow(2**63)
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be -1 (random) or a non-negative integer")
        if seed >= 2**64:
            raise ValueError("seed must be smaller than 2^64")
        return seed

    @staticmethod
    def _validate_expected_nodes(workflow: dict[str, Any]) -> None:
        expected = {
            "3": "KSampler",
            "4": "CheckpointLoaderSimple",
            "5": "EmptyLatentImage",
            "6": "CLIPTextEncode",
            "8": "VAEDecode",
            "9": "SaveImage",
            "11": "ModelSamplingFlux",
        }
        for node_id, expected_type in expected.items():
            node = workflow.get(node_id)
            if not isinstance(node, dict) or node.get("class_type") != expected_type:
                raise ValueError(
                    f"Workflow node {node_id} must be a {expected_type}; "
                    "the workflow and ComfyClient node mapping are out of sync."
                )
            if not isinstance(node.get("inputs"), dict):
                raise ValueError(f"Workflow node {node_id} has no inputs object")

    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
    ) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            return {"status": "error", "message": "Prompt cannot be empty."}
        try:
            self._validate_dimensions(width, height)
            normalized_seed = self._normalize_seed(seed)
            workflow = self.load_workflow_template()
            self._validate_expected_nodes(workflow)

            # Node 3: KSampler. Never submit the application's -1 sentinel to ComfyUI.
            workflow["3"]["inputs"]["seed"] = normalized_seed
            # Node 5: latent image shape.
            workflow["5"]["inputs"]["width"] = width
            workflow["5"]["inputs"]["height"] = height
            # Node 6: positive prompt.
            workflow["6"]["inputs"]["text"] = prompt.strip()
            # Node 11: FLUX sampling dimensions must match the latent dimensions.
            workflow["11"]["inputs"]["width"] = width
            workflow["11"]["inputs"]["height"] = height
            # These are required inputs in current ComfyUI versions.
            workflow["11"]["inputs"].setdefault("max_shift", 1.15)
            workflow["11"]["inputs"].setdefault("base_shift", 0.5)
            # Remove the obsolete/nonexistent ModelSamplingFlux input from older templates.
            workflow["11"]["inputs"].pop("weight", None)

            response = requests.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow},
                timeout=self.timeout,
            )
            if not response.ok:
                # ComfyUI returns useful node-validation details in its response body.
                detail = response.text.strip()
                if len(detail) > 2000:
                    detail = detail[:2000] + "…"
                return {
                    "status": "error",
                    "message": f"ComfyUI rejected the workflow (HTTP {response.status_code}): {detail or response.reason}",
                }

            try:
                data = response.json()
            except ValueError:
                return {
                    "status": "error",
                    "message": "ComfyUI returned a successful HTTP status but invalid JSON.",
                }
            prompt_id = data.get("prompt_id")
            if not prompt_id:
                return {
                    "status": "error",
                    "message": f"ComfyUI accepted no prompt_id. Response: {data}",
                }
            return {"status": "success", "prompt_id": str(prompt_id), "seed": normalized_seed}

        except requests.Timeout:
            return {
                "status": "error",
                "message": "Timed out submitting the workflow to ComfyUI. Check whether ComfyUI is responsive before retrying.",
            }
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Cannot reach ComfyUI at {self.base_url}: {exc}"}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return {"status": "error", "message": str(exc)}

    def get_job_status(self, prompt_id: str) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/history/{prompt_id}", timeout=10
            )
            response.raise_for_status()
            history = response.json()

            # Jobs may not appear in /history until ComfyUI finishes execution.
            if prompt_id not in history:
                return {"status": "queued_or_running"}

            record = history[prompt_id]
            outputs = record.get("outputs", {})
            image_outputs = outputs.get("9", {}).get("images", [])
            if image_outputs:
                image = image_outputs[0]
                filename = Path(str(image.get("filename", ""))).name
                if not filename:
                    return {"status": "error", "message": "ComfyUI returned an empty output filename."}

                # Preserve a safe relative output subfolder, if ComfyUI reports one.
                subfolder_raw = str(image.get("subfolder", "")).replace("\\", "/")
                subfolder_path = PurePosixPath(subfolder_raw)
                if subfolder_path.is_absolute() or ".." in subfolder_path.parts:
                    return {"status": "error", "message": "ComfyUI returned an unsafe output path."}
                relative_path = subfolder_path / filename if subfolder_raw else PurePosixPath(filename)
                url_path = quote(relative_path.as_posix(), safe="/")
                return {
                    "status": "completed",
                    "filename": filename,
                    "subfolder": subfolder_path.as_posix() if subfolder_raw else "",
                    "relative_path": relative_path.as_posix(),
                    "image_url": f"/images/{url_path}",
                }

            status_data = record.get("status") or {}
            status_string = str(status_data.get("status_str", "")).lower()
            completed = bool(status_data.get("completed"))
            if status_string in {"error", "failed"} or (completed and not image_outputs):
                messages = status_data.get("messages") or record.get("messages") or []
                detail = repr(messages)
                if len(detail) > 1500:
                    detail = detail[:1500] + "…"
                return {
                    "status": "error",
                    "message": f"ComfyUI finished without an image (status={status_string or 'completed'}). {detail}",
                }
            return {"status": "queued_or_running"}

        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error querying ComfyUI history: {exc}"}
        except (ValueError, TypeError, KeyError) as exc:
            return {"status": "error", "message": f"Invalid ComfyUI history response: {exc}"}


comfy_client = ComfyClient()
