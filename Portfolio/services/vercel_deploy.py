import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

def deploy_to_vercel(html_content: str, project_name: str) -> str:
    """
    Deploys the given HTML content to Vercel and returns the live URL.
    """
    token = os.environ.get("VERCEL_API_TOKEN")
    if not token:
        raise Exception("Vercel API token not configured in .env")

    # Format the project name for Vercel (lowercase, no spaces)
    safe_project_name = "".join([c if c.isalnum() else "-" for c in project_name]).lower().strip("-")
    if not safe_project_name:
        safe_project_name = "portifyai-portfolio"

    url = "https://api.vercel.com/v13/deployments"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "PortifyAI/1.0"
    }
    
    payload = {
        "name": safe_project_name,
        "target": "production",
        "files": [
            {
                "file": "index.html",
                "data": html_content
            }
        ],
        "projectSettings": {
            "framework": None
        }
    }
    
    # Use session with retries for robust connection
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    response = session.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code in [200, 201]:
        # Always return the clean, predictable alias regardless of what team-slug alias Vercel might return in the JSON
        return f"https://{safe_project_name}.vercel.app"
    else:
        raise Exception(f"Failed to deploy to Vercel: {response.text}")
