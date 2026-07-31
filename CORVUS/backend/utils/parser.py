import json
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("corvus.parser")

class Parser:
    @staticmethod
    def parse_nuclei(output: str) -> List[Dict[str, Any]]:
        """Parses Nuclei JSON output lines."""
        results = []
        for line in output.strip().split('\n'):
            if not line: continue
            try:
                data = json.loads(line)
                # Ensure endpoint is extracted from matched-at or template-id
                endpoint = data.get("matched-at") or data.get("url", "/")
                results.append({
                    "type": data.get("template-id"),
                    "severity": data.get("info", {}).get("severity", "info").lower(),
                    "source": "nuclei",
                    "endpoint": endpoint,
                    "raw": data,
                    "confidence": 1.0
                })
            except json.JSONDecodeError:
                continue
        return results

    @staticmethod
    def parse_subfinder(output: str) -> List[str]:
        """Parses subfinder output (list of domains)."""
        return [line.strip() for line in output.strip().split('\n') if line.strip()]

    @staticmethod
    def parse_httpx(output: str) -> List[Dict[str, str]]:
        """Parses httpx JSON output."""
        results = []
        for line in output.strip().split('\n'):
            if not line: continue
            try:
                data = json.loads(line)
                results.append({
                    "url": data.get("url"),
                    "title": data.get("title"),
                    "status_code": data.get("status_code"),
                    "host": data.get("host")
                })
            except json.JSONDecodeError:
                continue
        return results
    
    @staticmethod
    def parse_dalfox(output: str) -> List[Dict[str, Any]]:
        """Parses Dalfox output (expecting JSON per line or simple text)."""
        results = []
        for line in output.strip().split('\n'):
            if not line: continue
            if '"type":"vulnerability"' in line: # Dalfox JSON format
                try:
                    data = json.loads(line)
                    results.append({
                        "type": "xss",
                        "severity": "HIGH",
                        "source": "dalfox",
                        "endpoint": data.get("url"),
                        "raw": data,
                        "confidence": 1.0
                    })
                except: continue
            elif "[POC]" in line: # Dalfox text format
                # Example: [POC][G][V] http://target.com/page?q=...
                parts = line.split(" ")
                url = parts[-1] if parts else "unknown"
                results.append({
                    "type": "xss",
                    "severity": "HIGH",
                    "source": "dalfox",
                    "endpoint": url,
                    "raw": line,
                    "confidence": 0.9
                })
        return results
