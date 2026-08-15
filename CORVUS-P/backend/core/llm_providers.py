import httpx
import logging
import os

logger = logging.getLogger("corvus.llm_providers")

def is_llm_refusal(response_text: str) -> bool:
    """Mendeteksi apakah LLM menolak memberikan analisis karena safety guardrails."""
    if not response_text:
        return False
        
    refusal_keywords = [
        "cannot fulfill",
        "cannot assist",
        "against my safety guidelines",
        "as an ai",
        "privacy policy",
        "i cannot provide",
        "i am sorry, but i cannot"
    ]
    text_lower = response_text.lower()
    return any(keyword in text_lower for keyword in refusal_keywords)

def call_qwen(messages: list, model: str = "qwen-plus") -> dict:
    """
    Invokes the Qwen LLM API.
    """
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        return {
            "result": "Error: QWEN_API_KEY tidak dikonfigurasi di server.",
            "model_used": "qwen",
            "tokens_used": 0
        }
        
    try:
        res = httpx.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 1500
            },
            timeout=45
        )
        if res.status_code == 200:
            data = res.json()
            return {
                "result": data["choices"][0]["message"]["content"],
                "model_used": model,
                "tokens_used": data.get("usage", {}).get("total_tokens", 150)
            }
        raise Exception(f"Qwen error response: {res.text}")
    except Exception as e:
        logger.error(f"LLM Call failed for Qwen: {str(e)}")
        return {
            "result": f"Error calling Qwen: {str(e)}",
            "model_used": model,
            "tokens_used": 0
        }

def call_gemini(messages: list, model: str = "gemini-1.5-flash-latest") -> dict:
    """
    Invokes the Google Gemini LLM API (Antigravity proxy).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "result": "Error: GEMINI_API_KEY tidak dikonfigurasi di server.",
            "model_used": "gemini",
            "tokens_used": 0
        }
        
    try:
        contents = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = {"parts": [{"text": m["content"]}]}
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m["content"]}]
                })
        body = {"contents": contents}
        if system_instruction:
            body["systemInstruction"] = system_instruction
            
        res = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json=body,
            timeout=45
        )
        if res.status_code == 200:
            data = res.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except KeyError:
                text = "No content generated."
            return {
                "result": text,
                "model_used": model,
                "tokens_used": 200
            }
        raise Exception(f"Gemini error response: {res.text}")
    except Exception as e:
        logger.error(f"LLM Call failed for Gemini: {str(e)}")
        return {
            "result": f"Error calling Gemini: {str(e)}",
            "model_used": model,
            "tokens_used": 0
        }

def call_llm(messages: list, target_ai: str = "qwen") -> dict:
    """
    Router to direct requests to the appropriate LLM.
    """
    if target_ai == "gemini":
        return call_gemini(messages)
    return call_qwen(messages)
