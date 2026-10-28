# backend/utils/asset_helper.py
import re
from urllib.parse import urlparse
from typing import List, Tuple

STATIC_EXTENSIONS = (
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx",
    ".css", ".less", ".scss", ".sass",
    ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".avif", ".bmp", ".tiff",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mp3", ".wav", ".ogg", ".webm", ".avi", ".mov", ".mkv",
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".rar", ".7z",
    ".dll", ".exe", ".bin", ".wasm", ".iso", ".dat"
)

STATIC_DIR_PATTERNS = [
    r"/static/", r"/assets/", r"/chunks/", r"/dist/", r"/build/",
    r"/webpack/", r"/node_modules/", r"/vendor/", r"/bundles/",
    r"/images/", r"/img/", r"/fonts/", r"/css/", r"/styles/"
]

def is_static_asset(url_or_path: str) -> bool:
    """
    Menentukan apakah URL atau path merupakan file asset statis
    (seperti .js, .css, gambar, font, dsb) yang BUKAN rute aksi API/aplikasi.
    """
    if not url_or_path:
        return False
        
    try:
        parsed = urlparse(url_or_path)
        path = parsed.path.lower()
    except Exception:
        path = str(url_or_path).lower()
        
    # Cek ekstensi file
    clean_path = path.split("?")[0].split("#")[0]
    if clean_path.endswith(STATIC_EXTENSIONS):
        return True
        
    # Cek pola folder statis jika ada ekstensi apapun
    if any(re.search(pat, clean_path) for pat in STATIC_DIR_PATTERNS):
        if "." in clean_path.split("/")[-1]:
            return True
            
    return False

def is_js_asset(url_or_path: str) -> bool:
    """
    Menentukan apakah URL atau path merupakan file JavaScript (.js, .mjs, .cjs).
    """
    if not url_or_path:
        return False
    try:
        parsed = urlparse(url_or_path)
        path = parsed.path.lower().split("?")[0].split("#")[0]
    except Exception:
        path = str(url_or_path).lower().split("?")[0].split("#")[0]
    return path.endswith((".js", ".mjs", ".cjs"))

def classify_discovered_urls(urls: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Memisahkan URL hasil penemuan (crawling / direct bruteforce) menjadi:
    1. api_endpoints: Rute dinamis / API / halaman web aksi
    2. js_assets: File JavaScript statis untuk Asset Analyst (secret & endpoint scanner)
    3. other_static: Asset statis lainnya (css, image, font, dll)
    """
    api_endpoints = []
    js_assets = []
    other_static = []
    
    seen_api = set()
    seen_js = set()
    seen_other = set()
    
    for u in urls:
        u_clean = u.strip()
        if not u_clean:
            continue
            
        if is_js_asset(u_clean):
            if u_clean not in seen_js:
                seen_js.add(u_clean)
                js_assets.append(u_clean)
        elif is_static_asset(u_clean):
            if u_clean not in seen_other:
                seen_other.add(u_clean)
                other_static.append(u_clean)
        else:
            if u_clean not in seen_api:
                seen_api.add(u_clean)
                api_endpoints.append(u_clean)
                
    return api_endpoints, js_assets, other_static
