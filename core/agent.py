def trigger_github_child_workflow(subdomain_path):
    """GitHub API ke zariye agle subdomain ke liye naya workflow spawn karta hai."""
    token = os.getenv("GH_PAT") # Yahan GITHUB_TOKEN ki jagah GH_PAT kar diya
    repo = os.getenv("GITHUB_REPOSITORY") # e.g., "username/repo-name"
    
    if not token or not repo:
        print("⚠️ GH_PAT Token or Repo env missing. Skipping API trigger.")
        return

    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "event_type": "spawn-child",
        "client_payload": {"domain_path": subdomain_path}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 204:
            print(f"🚀 Successfully spawned child workflow for: {subdomain_path}")
        else:
            print(f"❌ Failed to spawn workflow: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception during workflow dispatch: {str(e)}")
      
