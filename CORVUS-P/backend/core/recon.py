"""
Corvus Reconnaissance Module
Gathers network intelligence: DNS resolution, WHOIS (with RDAP fallback), Ping, and Fast Port Scan.
Results are structured to match the frontend ReconResults.jsx component.
"""

import socket
import subprocess
import time
import re
import logging
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

logger = logging.getLogger("corvus.recon")

# Common ports to scan with their typical service names
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
    27017: "MongoDB"
}


def extract_hostname(target: str) -> str:
    """Extract clean hostname/domain from target URL or string."""
    if "://" in target:
        parsed = urlparse(target)
        return parsed.hostname or target
    # Remove path/port if present
    host = target.split("/")[0].split(":")[0]
    return host


def resolve_dns(hostname: str) -> Dict[str, Any]:
    """Resolve hostname to IP addresses."""
    result = {"tested_address": "—", "public_addresses": "—"}
    try:
        ip = socket.gethostbyname(hostname)
        result["tested_address"] = ip

        # Try to get all addresses
        try:
            _, _, addrs = socket.gethostbyname_ex(hostname)
            result["public_addresses"] = ", ".join(addrs) if addrs else ip
        except Exception:
            result["public_addresses"] = ip
            
        logger.info(f"[recon] DNS resolved {hostname} -> {ip}")
    except socket.gaierror as e:
        logger.warning(f"[recon] DNS resolution failed for {hostname}: {e}")
        result["tested_address"] = f"DNS resolution failed: {hostname}"
        result["public_addresses"] = "Could not resolve"
    return result


def _fetch_rdap_whois(hostname: str) -> Dict[str, str]:
    """Fallback ke standar ICANN RDAP REST API (Port 443 HTTPS)."""
    data = {
        "source": "RDAP Protocol (ICANN)",
        "registrar": "—",
        "created": "—",
        "updated": "—",
        "expires": "—",
        "status": "—",
        "nameservers": "—"
    }
    try:
        # Query rdap.org
        url = f"https://rdap.org/domain/{hostname}"
        resp = requests.get(url, timeout=6, headers={"Accept": "application/rdap+json, application/json"})
        if resp.status_code == 200:
            rd = resp.json()

            # Status
            statuses = rd.get("status", [])
            if isinstance(statuses, list) and statuses:
                data["status"] = ", ".join(statuses[:3])

            # Dates / Events
            for event in rd.get("events", []):
                action = event.get("eventAction", "")
                date = event.get("eventDate", "")
                if "registration" in action:
                    data["created"] = date
                elif "last changed" in action or "updated" in action:
                    data["updated"] = date
                elif "expiration" in action:
                    data["expires"] = date

            # Registrar entity
            for entity in rd.get("entities", []):
                roles = entity.get("roles", [])
                if "registrar" in roles:
                    vcard = entity.get("vcardArray", [])
                    if len(vcard) > 1 and isinstance(vcard[1], list):
                        for field in vcard[1]:
                            if field[0] == "fn":
                                data["registrar"] = str(field[3])
                                break
                    if data["registrar"] == "—" and "handle" in entity:
                        data["registrar"] = entity["handle"]

            # Nameservers
            ns_list = []
            for ns in rd.get("nameservers", []):
                ldh = ns.get("ldhName")
                if ldh:
                    ns_list.append(ldh.lower())
            if ns_list:
                data["nameservers"] = "\n".join(ns_list)

            return data
    except Exception as e:
        logger.debug(f"[recon] RDAP fallback error for {hostname}: {e}")
    return {}


def lookup_whois(hostname: str) -> Dict[str, str]:
    """Perform WHOIS lookup for the domain with multi-tier fallback (python-whois -> OS -> RDAP)."""
    default = {
        "source": "—",
        "registrar": "—",
        "created": "—",
        "updated": "—",
        "expires": "—",
        "status": "—",
        "nameservers": "—"
    }

    # 1. Tier 1: Coba python-whois
    try:
        import whois
        w = whois.whois(hostname)
        
        def first_or_str(val):
            if isinstance(val, list):
                return ", ".join(str(v) for v in val if v)
            return str(val) if val else "—"
        
        def date_str(val):
            if isinstance(val, list):
                val = val[0] if val else None
            if val:
                try:
                    return val.strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception:
                    return str(val)
            return "—"
        
        if w.registrar or getattr(w, 'creation_date', None) is not None:
            default["source"] = first_or_str(w.registrar) if w.registrar else "WHOIS Lookup"
            default["registrar"] = first_or_str(w.registrar) if w.registrar else first_or_str(getattr(w, 'org', None))
            default["created"] = date_str(w.creation_date)
            default["updated"] = date_str(w.updated_date)
            default["expires"] = date_str(w.expiration_date)
            default["status"] = first_or_str(w.status)
            
            ns = w.name_servers
            if isinstance(ns, list):
                default["nameservers"] = "\n".join(str(n).lower() for n in ns if n)
            elif ns:
                default["nameservers"] = str(ns).lower()
                
            logger.info(f"[recon] python-whois lookup succeeded for {hostname}")
            return default
    except Exception as e:
        logger.warning(f"[recon] python-whois failed for {hostname}: {e}")

    # 2. Tier 2: Coba OS binary whois
    try:
        proc = subprocess.run(["whois", hostname], capture_output=True, text=True, timeout=8)
        if proc.returncode == 0 and proc.stdout:
            out = proc.stdout
            
            def extract(regex):
                m = re.search(regex, out, re.IGNORECASE)
                return m.group(1).strip() if m else "—"
            
            reg = extract(r"Registrar:\s*(.+)")
            if reg != "—":
                default["registrar"] = reg
                default["created"] = extract(r"Creation Date:\s*(.+)")
                default["updated"] = extract(r"Updated Date:\s*(.+)")
                
                exp = extract(r"Registry Expiry Date:\s*(.+)")
                if exp == "—": exp = extract(r"Expiration Date:\s*(.+)")
                if exp == "—": exp = extract(r"Expiry Date:\s*(.+)")
                default["expires"] = exp
                
                default["status"] = extract(r"Domain Status:\s*(.+)")
                ns = re.findall(r"Name Server:\s*(.+)", out, re.IGNORECASE)
                default["nameservers"] = "\n".join(ns).lower() if ns else "—"
                default["source"] = "OS WHOIS Service"
                
                logger.info(f"[recon] OS WHOIS fallback succeeded for {hostname}")
                return default
    except Exception as fallback_e:
        logger.debug(f"[recon] OS whois fallback failed: {fallback_e}")

    # 3. Tier 3: RDAP ICANN REST API Fallback
    rdap_res = _fetch_rdap_whois(hostname)
    if rdap_res and (rdap_res.get("created") != "—" or rdap_res.get("registrar") != "—"):
        default.update(rdap_res)
        logger.info(f"[recon] RDAP fallback succeeded for {hostname}")
        return default

    default["source"] = "WHOIS data protected / not publicly available"
    return default


def run_ping(hostname: str) -> Dict[str, str]:
    """Run ping against target and parse results."""
    default = {
        "protocol": "ICMP",
        "loss": "—",
        "stats": "—",
        "duration": "—",
        "raw": "Ping test not available."
    }
    try:
        # Use system ping: 4 packets, 3s timeout
        cmd = ["ping", "-c", "4", "-W", "3", hostname]
        start = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        elapsed = time.time() - start
        
        output = proc.stdout + proc.stderr
        default["raw"] = output.strip() if output.strip() else "No response received."
        default["duration"] = f"{elapsed:.2f}s"
        
        # Parse packet loss
        loss_match = re.search(r'(\d+(?:\.\d+)?%)\s*packet loss', output)
        if loss_match:
            default["loss"] = loss_match.group(1)
        
        # Parse min/avg/max
        rtt_match = re.search(r'rtt\s+min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
        if rtt_match:
            default["stats"] = f"Min: {rtt_match.group(1)}ms / Avg: {rtt_match.group(2)}ms / Max: {rtt_match.group(3)}ms"
        else:
            win_match = re.search(r'Minimum\s*=\s*(\d+)ms.*Maximum\s*=\s*(\d+)ms.*Average\s*=\s*(\d+)ms', output, re.DOTALL)
            if win_match:
                default["stats"] = f"Min: {win_match.group(1)}ms / Avg: {win_match.group(3)}ms / Max: {win_match.group(2)}ms"
        
        logger.info(f"[recon] Ping completed for {hostname}: loss={default['loss']}")
    except Exception as e:
        default["raw"] = f"ICMP Ping filtered or disabled by target: {str(e)}"
    return default


def _probe_single_port(hostname: str, port: int, service: str, timeout: float = 1.2) -> Dict[str, Any]:
    """Fungsi helper untuk cek satu port TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        conn_result = sock.connect_ex((hostname, port))
        sock.close()
        if conn_result == 0:
            return {
                "port": port,
                "protocol": "TCP",
                "state": "OPEN",
                "service": service
            }
    except Exception:
        pass
    return None


def scan_ports(hostname: str, timeout: float = 1.2) -> Dict[str, Any]:
    """Scan common ports on the target concurrently using ThreadPoolExecutor."""
    result = {
        "ptr": "—",
        "profile": "Top 19 Common Ports",
        "tested": f"{len(COMMON_PORTS)} ports",
        "duration": "—",
        "list": []
    }
    
    # Try PTR (reverse DNS)
    try:
        ip = socket.gethostbyname(hostname)
        try:
            ptr_name = socket.gethostbyaddr(ip)
            result["ptr"] = ptr_name[0] if ptr_name else "—"
        except socket.herror:
            result["ptr"] = "No PTR record"
    except Exception:
        result["ptr"] = "Could not resolve"
    
    start = time.time()
    open_ports = []
    
    # Concurrent scanning for fast execution
    with ThreadPoolExecutor(max_workers=min(25, len(COMMON_PORTS))) as executor:
        futures = [
            executor.submit(_probe_single_port, hostname, port, service, timeout)
            for port, service in COMMON_PORTS.items()
        ]
        for f in futures:
            port_info = f.result()
            if port_info:
                open_ports.append(port_info)
    
    # Sort by port number
    open_ports.sort(key=lambda x: x["port"])

    elapsed = time.time() - start
    result["duration"] = f"{elapsed:.2f}s"
    result["list"] = open_ports
    result["tested"] = f"{len(COMMON_PORTS)} ports ({len(open_ports)} open)"
    
    logger.info(f"[recon] Port scan completed for {hostname}: {len(open_ports)} open ports in {elapsed:.2f}s")
    return result


def run_recon(target: str) -> Dict[str, Any]:
    """
    Main entry point: runs all recon modules and returns a structured dict
    matching the frontend ReconResults.jsx component expectations.
    """
    hostname = extract_hostname(target)
    logger.info(f"[recon] Starting full reconnaissance for: {hostname}")
    
    # 1. DNS Resolution
    dns_data = resolve_dns(hostname)
    
    # 2. WHOIS Lookup (Multi-Tier)
    whois_data = lookup_whois(hostname)
    
    # 3. Ping
    ping_data = run_ping(hostname)
    
    # 4. Fast Concurrent Port Scan
    ports_data = scan_ports(hostname)
    
    recon_result = {
        "tested_address": dns_data["tested_address"],
        "public_addresses": dns_data["public_addresses"],
        "whois": whois_data,
        "ping": ping_data,
        "ports": ports_data
    }
    
    logger.info(f"[recon] Reconnaissance complete for {hostname}")
    return recon_result
