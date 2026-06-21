"""
LangGraph Orchestration - Usage Examples
========================================

This document shows how to use the complete LangGraph reconnaissance workflow.
"""

# Example 1: Submit a reconnaissance job with workflow execution
# ===========================================================

import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Create and sign an RoE
# (Uses the `scripts/sign_roe.py` script or manual HMAC-SHA256)

roe_payload = {
    "client_name": "ACME Corp Security Team",
    "authorized_by": "Chief Security Officer",
    "contact_email": "security@acme.com",
    "in_scope_assets": {
        "domains": ["acme.com"],
        "ip_ranges": ["203.0.113.0/24"],
        "ip_exclusions": ["203.0.113.5"]
    },
    "excluded_assets": ["internal-lab.acme.com"],
    "active_scanning_authorized": False,  # Passive-only for this example
    "allowed_active_tools": [],
    "valid_from": datetime.now().isoformat(),
    "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
    "notes": "Quarterly security assessment"
}

# Step 2: Submit the job
response = httpx.post(
    f"{BASE_URL}/jobs",
    json={
        "apex_domain": "acme.com",
        "roe": roe_payload  # Include signature if required
    }
)

job_data = response.json()
job_id = job_data["job_id"]
print(f"✅ Job authorized: {job_id}")
print(f"   Active scanning authorized: {job_data['active_scanning_authorized']}")

# Step 3: Run the complete workflow
response = httpx.post(f"{BASE_URL}/jobs/{job_id}/run-workflow")

workflow_result = response.json()
print(f"\n✅ Workflow completed: {workflow_result['status']}")

# Step 4: Inspect the results
results = workflow_result["result"]
print(f"\n📊 Discovered Assets:")
print(f"   Domains: {results['discovered_domains']}")
print(f"   Subdomains: {results['discovered_subdomains']}")
print(f"   IPs: {results['discovered_ips']}")

print(f"\n🔍 Knowledge Base References:")
for agent_name, agent_data in results["kb_refs"].items():
    print(f"   - {agent_name.upper()}: {list(agent_data.keys())}")


# Example 2: Active reconnaissance (with network scanning)
# ========================================================

roe_payload_active = {
    "client_name": "ACME Corp Security Team",
    "authorized_by": "Chief Security Officer",
    "contact_email": "security@acme.com",
    "in_scope_assets": {
        "domains": ["acme.com"],
        "ip_ranges": ["203.0.113.0/24"]
    },
    "excluded_assets": [],
    "active_scanning_authorized": True,  # ✅ Allow network scanning
    "allowed_active_tools": ["nmap"],    # Can add: shodan, censys, etc.
    "valid_from": datetime.now().isoformat(),
    "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
    "notes": "Penetration testing engagement - authorized by management"
}

response = httpx.post(
    f"{BASE_URL}/jobs",
    json={"apex_domain": "acme.com", "roe": roe_payload_active}
)

job_id = response.json()["job_id"]
print(f"\n🚀 Active scanning job: {job_id}")

# Run workflow - will now include network scanning
response = httpx.post(f"{BASE_URL}/jobs/{job_id}/run-workflow")
workflow_result = response.json()

# Network results are included when active_scanning_authorized=True
if "network" in workflow_result["result"]["kb_refs"]:
    print("✅ Network scanning results included")
    network_data = workflow_result["result"]["kb_refs"]["network"]
    for target in network_data["targets"][:3]:  # Show first 3
        print(f"   {target['ip']}: {target['open_ports']}")


# Example 3: Retrieve job status and results later
# ==================================================

response = httpx.get(f"{BASE_URL}/jobs/{job_id}")
job_info = response.json()
print(f"\nJob Status: {job_info['status']}")
print(f"Created at: {job_info['created_at']}")


# Graph Execution Flow (Behind the Scenes)
# =========================================
"""
1. OSINT Node:
   - Runs: OsintAgent.run(apex_domain="acme.com")
   - Collects: DNS records (A, AAAA, MX, TXT, NS)
   - Collects: Subdomains via Certificate Transparency logs
   - Result: state.discovered_ips += [...], state.discovered_subdomains += [...]
   
2. Web Node:
   - Runs: WebAgent.run(hosts=["acme.com", "www.acme.com", ...])
   - Collects: Server headers, page titles, content-type
   - Result: state.kb_refs["web"] = {hosts: [...]}
   
3. Network Node (CONDITIONAL):
   - If active_scanning_authorized=False: SKIPPED (go to Threat Intel)
   - If active_scanning_authorized=True:
     - Runs: NetworkAgent.run(ips=state.discovered_ips)
     - Probes: Ports 22, 80, 443, 8080, 8443
     - Result: state.kb_refs["network"] = {targets: [...]}
   
4. Threat Intel Node:
   - Runs: ThreatIntelAgent.run(assets=[{domain, ip}...])
   - Adds: Reputation scores (0-1), CVE listings
   - Result: state.kb_refs["threat_intel"] = {assets: [...]}
   
5. Return:
   - All kb_refs and discovered_* fields returned to API
   - Job status set to COMPLETED
   - Database persisted
"""
