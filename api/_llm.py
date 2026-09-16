import json
import os
import urllib.error
import urllib.request

class LlmError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

def read_llm_config():
    return {
        "base_url": (os.environ.get("LLM_BASE_URL") or "").rstrip("/"),
        "model": os.environ.get("LLM_MODEL") or "",
        "api_key": os.environ.get("LLM_API_KEY") or "",
    }

def chat_completion(system: str, user: str, *, timeout: float = 45.0) -> str:
    cfg = read_llm_config()
    if not cfg["base_url"] or not cfg["model"]:
        raise LlmError("LLM이 설정되지 않았습니다", status=503)
    payload = json.dumps({
        "model": cfg["model"],
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{cfg['base_url']}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key'] or 'not-needed'}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LlmError(f"LLM HTTP {e.code}", status=e.code) from e
    except urllib.error.URLError as e:
        raise LlmError(f"LLM 네트워크 오류: {e}", status=None) from e
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    if not content.strip():
        raise LlmError("LLM 응답이 비어 있습니다")
    return content.strip()
