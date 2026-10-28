import logging
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("corvus.dom_validator")

class DOMValidator:
    @staticmethod
    def validate_xss(url: str, payload: str, timeout_ms: int = 5000) -> int:
        """
        Phase 4: DOM Validation Engine (Playwright).
        Memverifikasi apakah suatu payload XSS benar-benar ter-render (reflected)
        di dalam HTML DOM tanpa sanitasi/encoding.
        
        Returns:
            1 jika rentan (payload tereksusi/terrefleksi utuh)
            0 jika aman (payload di-encode atau WAF memblokir)
        """
        if not payload or not url:
            return 0
            
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(timeout_ms)
                
                try:
                    # Injeksi payload ke URL jika belum ada
                    target_url = url
                    if payload not in url:
                        separator = "&" if "?" in url else "?"
                        target_url = f"{url}{separator}corvus_test={payload}"
                        
                    page.goto(target_url)
                    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
                except PlaywrightTimeoutError:
                    pass # Biarkan lanjut untuk melihat apa yang berhasil di-load sebelum timeout
                except Exception as e:
                    logger.warning(f"DOMValidator load error for {url}: {e}")
                    
                # Ambil DOM yang sudah di-render Playwright
                content = page.content()
                browser.close()
                
                # Validasi kemunculan string payload persis di DOM (tanpa HTML entities)
                if payload in content:
                    return 1
                return 0
        except Exception as e:
            logger.error(f"Playwright DOM Validator execution failed: {e}")
            return 0
