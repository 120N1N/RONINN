import httpx
import logging

logger = logging.getLogger("corvus.llm_providers")

def test_connection(provider: str, api_key: str, model: str = None) -> tuple:
    """
    Test connectivity to the given LLM provider using the provided API key and model.
    Returns (True, "Success") if connection is successful, (False, "Error message") otherwise.
    """
    provider_clean = provider.lower().strip()
    try:
        if provider_clean == "openai":
            res = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model or "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            if res.status_code != 200:
                return False, f"OpenAI Error {res.status_code}: {res.text}"
            return True, "Koneksi berhasil"
            
        elif provider_clean == "anthropic":
            res = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model or "claude-3-haiku-20240307",
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "ping"}]
                },
                timeout=10
            )
            if res.status_code != 200:
                return False, f"Anthropic Error {res.status_code}: {res.text}"
            return True, "Koneksi berhasil"
            
        elif provider_clean == "google":
            if model:
                chosen_model = model.lower().replace(" ", "-")
            else:
                chosen_model = "gemini-3.5-flash"
                
            res = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": "ping"}]}]},
                timeout=10
            )
            if res.status_code != 200:
                return False, f"Gemini Error {res.status_code}: {res.text}"
            return True, "Koneksi berhasil"
            
        elif provider_clean in ["groq", "deepseek", "cohere"]:
            if provider_clean == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                default_m = "llama3-8b-8192"
            elif provider_clean == "deepseek":
                url = "https://api.deepseek.com/v1/chat/completions"
                default_m = "deepseek-chat"
            else: # cohere
                url = "https://api.cohere.com/v1/chat-compat"
                default_m = "command-r"
                
            res = httpx.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model or default_m,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            if res.status_code not in [200, 201]:
                return False, f"{provider_clean.capitalize()} Error {res.status_code}: {res.text}"
            return True, "Koneksi berhasil"
            
        return False, "Provider tidak didukung"
    except Exception as e:
        logger.error(f"Test connection failed for {provider}: {str(e)}")
        return False, f"Gagal terkoneksi jaringan: {str(e)}"

def call_llm(provider: str, api_key: str, messages: list, model: str = None) -> dict:
    """
    Invokes the LLM API using direct REST endpoints.
    Returns a unified dict schema: {"result": str, "model_used": str, "tokens_used": int}
    """
    provider_clean = provider.lower().strip()
    try:
        if provider_clean == "openai":
            chosen_model = model or "gpt-4o-mini"
            res = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": chosen_model,
                    "messages": messages,
                    "max_tokens": 1000
                },
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                return {
                    "result": data["choices"][0]["message"]["content"],
                    "model_used": chosen_model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 150)
                }
            raise Exception(f"OpenAI error response: {res.text}")
            
        elif provider_clean == "anthropic":
            # Map standard system message to anthropic structure if present
            system_msg = None
            filtered_msgs = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    filtered_msgs.append(m)
            
            chosen_model = model or "claude-3-haiku-20240307"
            body = {
                "model": chosen_model,
                "max_tokens": 1000,
                "messages": filtered_msgs
            }
            if system_msg:
                body["system"] = system_msg
                
            res = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=body,
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                input_t = data.get("usage", {}).get("input_tokens", 100)
                output_t = data.get("usage", {}).get("output_tokens", 50)
                return {
                    "result": data["content"][0]["text"],
                    "model_used": chosen_model,
                    "tokens_used": input_t + output_t
                }
            raise Exception(f"Anthropic error response: {res.text}")
            
        elif provider_clean == "google":
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
                
            if model:
                chosen_model = model.lower().replace(" ", "-")
            else:
                chosen_model = "gemini-3.5-flash"
                
            res = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent?key={api_key}",
                json=body,
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                try:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                except KeyError:
                    text = "No content generated."
                return {
                    "result": text,
                    "model_used": chosen_model,
                    "tokens_used": 200
                }
            raise Exception(f"Gemini error response: {res.text}")
            
        elif provider_clean in ["groq", "deepseek", "cohere"]:
            if provider_clean == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                default_m = "llama3-8b-8192"
            elif provider_clean == "deepseek":
                url = "https://api.deepseek.com/v1/chat/completions"
                default_m = "deepseek-chat"
            else: # cohere
                url = "https://api.cohere.com/v1/chat-compat"
                default_m = "command-r"
                
            chosen_model = model or default_m
            res = httpx.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": chosen_model,
                    "messages": messages,
                    "max_tokens": 1000
                },
                timeout=30
            )
            if res.status_code in [200, 201]:
                data = res.json()
                return {
                    "result": data["choices"][0]["message"]["content"],
                    "model_used": chosen_model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 150)
                }
            raise Exception(f"{provider.upper()} error response: {res.text}")
            
        raise Exception("Unsupported LLM Provider")
    except Exception as e:
        logger.error(f"LLM Call failed for {provider}: {str(e)}")
        return {
            "result": f"Error calling {provider}: {str(e)}",
            "model_used": provider,
            "tokens_used": 0
        }
