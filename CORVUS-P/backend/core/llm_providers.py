import httpx
import logging
import os
from backend.config import settings

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

import re

def call_river(messages: list, model: str = None) -> dict:
    """
    Invokes the River.ai Cloud LLM API using river-client.
    Default model: Qwen/Qwen3.5-9B (or configured via RIVER_MODEL).
    """
    api_key = getattr(settings, "RIVER_API_KEY", "") or os.getenv("RIVER_API_KEY", "")
    if not api_key:
        return {
            "result": "Error: RIVER_API_KEY tidak dikonfigurasi di server.",
            "model_used": "river",
            "tokens_used": 0
        }
        
    model_name = model or getattr(settings, "RIVER_MODEL", "") or os.getenv("RIVER_MODEL", "Qwen/Qwen3.5-9B")
    
    # Format messages list into standard ChatML for Qwen models on River
    has_system = any(m.get("role", "").lower() == "system" for m in messages)
    prompt_parts = []
    
    if not has_system:
        prompt_parts.append("<|im_start|>system\nYou are an expert cybersecurity AI for Corvus Security Scanner. Provide direct, professional, and well-structured analysis. Do not include internal monologue or <think> tags.<|im_end|>")

    for m in messages:
        role = m.get("role", "user").lower()
        content = m.get("content", "")
        if role == "system":
            content += "\nProvide direct, professional analysis without internal monologue or <think> tags."
        prompt_parts.append(f"<|im_start|>{role}\n{content}\n<|im_end|>")
    prompt_parts.append("<|im_start|>assistant\n")
    prompt = "\n".join(prompt_parts)
    
    try:
        from contextlib import closing
        import river_client as river
        
        with closing(river.Client(api_key=api_key)) as client:
            samples = client.sample(
                prompt,
                base_model=model_name,
                max_tokens=1500,
                temperature=0.2,
                stop=["<|im_end|>", "<|endoftext|>"]
            )
            if samples and len(samples) > 0:
                raw_text = samples[0].text or ""
                # Strip internal reasoning/thinking tags
                if "</think>" in raw_text:
                    cleaned_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
                elif "<think>" in raw_text:
                    cleaned_text = re.sub(r"<think>.*", "", raw_text, flags=re.DOTALL).strip()
                else:
                    cleaned_text = raw_text.strip()
                    
                final_text = cleaned_text if cleaned_text else raw_text.strip()
                
                return {
                    "result": final_text,
                    "model_used": f"river/{model_name}",
                    "tokens_used": getattr(samples[0], "tokens_used", 300)
                }
            return {
                "result": "No content generated from River.ai.",
                "model_used": f"river/{model_name}",
                "tokens_used": 0
            }
    except Exception as e:
        logger.error(f"LLM Call failed for River.ai: {str(e)}")
        return {
            "result": f"Error calling River.ai: {str(e)}",
            "model_used": f"river/{model_name}",
            "tokens_used": 0
        }

def call_qwen(messages: list, model: str = None) -> dict:
    """Legacy wrapper forwarding to River.ai with Qwen model."""
    return call_river(messages, model=model)

def call_gemini(messages: list, model: str = "gemini-3.5-flash-lite") -> dict:
    """
    Invokes the Google Gemini LLM API.
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

def call_openrouter(messages: list, model: str = "google/gemini-3.5-flash-lite") -> dict:
    """
    Invokes an LLM via OpenRouter API (OpenAI-compatible).
    Default model: google/gemini-3.5-flash-lite
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "result": "Error: OPENROUTER_API_KEY tidak dikonfigurasi di server.",
            "model_used": "openrouter",
            "tokens_used": 0
        }
        
    try:
        res = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://corvusnoct.my.id",
                "X-Title": "Corvus Security Scanner"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 500
            },
            timeout=60
        )
        if res.status_code == 200:
            data = res.json()
            return {
                "result": data["choices"][0]["message"]["content"],
                "model_used": f"openrouter/{model}",
                "tokens_used": data.get("usage", {}).get("total_tokens", 200)
            }
        raise Exception(f"OpenRouter error response: {res.text}")
    except Exception as e:
        logger.error(f"LLM Call failed for OpenRouter: {str(e)}")
        return {
            "result": f"Error calling OpenRouter: {str(e)}",
            "model_used": "openrouter",
            "tokens_used": 0
        }

def call_llm(messages: list, target_ai: str = "auto") -> dict:
    """
    Router to direct requests to the appropriate LLM.
    If 'auto', tries providers in order: river (primary), gemini (backup), openrouter (fallback).
    """
    providers = ["river", "gemini", "openrouter"]
    
    if target_ai in ["river", "qwen"]:
        providers = ["river"]
    elif target_ai in ["gemini", "openrouter"]:
        providers = [target_ai]
        
    last_response = None
    for provider in providers:
        if provider == "gemini":
            resp = call_gemini(messages)
        elif provider == "river":
            resp = call_river(messages)
        elif provider == "openrouter":
            resp = call_openrouter(messages)
        else:
            resp = call_gemini(messages)
            
        last_response = resp
        if resp and isinstance(resp, dict) and not str(resp.get("result", "")).startswith("Error"):
            return resp
            
    return last_response
