from backend.core.VulnCore import VulnManager

print("[*] Running VulnManager.run_all_modules test...")
try:
    results = VulnManager.run_all_modules(
        target_url="http://example.com",
        discovered_endpoints=[
            "http://example.com/api/test?user_id=1",
            "http://example.com/admin",
            "http://example.com/login",
            "http://example.com/redirect?dest=https://example.com"
        ],
        scan_context={"mode": "standard"}
    )
    print(f"\n[+] SUCCESS! Total findings generated: {len(results)}")
    for r in results:
        print(f"    - [{r.get('owasp_code')}] {r.get('name')} | Severity: {r.get('severity')} | Path: {r.get('location')}")
except Exception as e:
    import traceback
    traceback.print_exc()
