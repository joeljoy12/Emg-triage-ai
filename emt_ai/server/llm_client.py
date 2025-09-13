from __future__ import annotations
from typing import Optional, Dict, Any
import requests, logging, re

logger = logging.getLogger(__name__)


def _clean_reason_text(raw: str) -> str:
    """
    Normalize the LLM output to a single, clean sentence:
    - Strip JSON/markdown/braces/quotes/labels
    - Keep only the first sentence-like span
    - Ensure trailing period
    """
    if not raw:
        return ""

    text = raw.strip()

    # Remove common prefixes/labels
    text = re.sub(r'^\s*(reason|explanation)\s*[:\-]\s*', '', text, flags=re.I)

    # If it looks like JSON, drop braces and keys
    text = re.sub(r'^[\[\{]\s*', '', text)
    text = re.sub(r'[\]\}]\s*$', '', text)
    text = re.sub(r'"reason"\s*:\s*', '', text, flags=re.I)
    text = text.strip().strip('"').strip("'").strip()

    # Remove code fences / backticks / markdown bullets
    text = re.sub(r'`{1,3}', '', text)
    text = re.sub(r'^\s*[-*•]\s*', '', text)

    # Grab the first sentence-like chunk (end with . ! ?)
    m = re.search(r'([^.!?]{6,250}[.!?])', text)
    if m:
        text = m.group(1).strip()
    else:
        text = " ".join(text.split())[:220]

    if text and text[-1] not in ".!?":
        text += "."

    return text


class LLMClient:
    SYS_PROMPT = (
        "You are an emergency triage assistant. Follow START and WHO Basic Emergency Care scope. "
        "NO medications. NO invasive procedures. Keep to layperson first-aid reasoning. "
        "Return only ONE short explanatory sentence. "
    )

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.2:latest", timeout: int = 12):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_alive(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=1)
            return r.status_code == 200
        except Exception:
            return False

    def safe_reason(self, label: str, description: str, vitals: Dict[str, Any]) -> Optional[str]:
        """
        Ask the local LLM for ONE concise sentence (≤22 words) explaining the chosen label.
        Returns None if Ollama is unavailable or any error occurs.
        """
        if not self.is_alive():
            return None

        prompt = f"""
You are an emergency triage assistant. Use START triage and WHO Basic Emergency Care scope.
Answer with ONE short, plain-English sentence (≤22 words) that explains WHY the chosen triage label fits.
Do NOT output JSON, lists, bullets, or labels. Do NOT start with "Reason:".
No meds, no invasive procedures, no speculation.

Style:
- Start with the clinical signal, then the implication.
- Prefer numbers where available (e.g., "RR 34/min (>30)").
- Do not mention “rules” or “START”, just the clinical logic.

Examples (format you must imitate — one sentence only):
Immediate → RR 34/min (>30) indicates respiratory compromise; prioritize immediate care.
Expectant → Apnea with no pulse indicates non-survivable status; allocate resources to salvageable patients.
Minor → Ambulatory with stable vitals suggests minor injuries suitable for delayed treatment.
Delayed → Stable vitals and following commands indicate delayed priority.

Now write exactly one sentence:

Label: {label}
Description: {description}
Vitals: {vitals}
""".strip()

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "repeat_penalty": 1.05,
                    "num_predict": 64,
                    "stop": ["\n\n", "Label:", "Description:", "Vitals:", "Reason:", "Examples:"],
                },
            }
            r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            r.raise_for_status()
            raw = (r.json().get("response") or "").strip()
            cleaned = _clean_reason_text(raw)
            return cleaned or None
        except Exception as e:
            logger.warning("LLMClient.safe_reason failed: %s", e)
            return None
