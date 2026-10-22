# core/agent.py
import os
import json
import time
import requests
import arxiv
import google.generativeai as genai

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def fetch_arxiv_papers(query, max_results=3):
    """ArXiv se real research papers fetch karta hai taaki hallucination na ho."""
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        papers = []
        for result in search.results():
            papers.append(f"Title: {result.title}\nSummary: {result.summary[:300]}...")
        return "\n---\n".join(papers)
    except Exception as e:
        return f"Error fetching papers: {str(e)}"

def check_and_update_visited(domain):
    """Global duplicate prevention: Check if domain was already explored."""
    visited_path = "data/visited_domains.json"
    os.makedirs("data", exist_ok=True)
    
    if os.path.exists(visited_path):
        with open(visited_path, "r") as f:
            visited = json.load(f)
    else:
        visited = []
        
    normalized = domain.strip().lower()
    if normalized in visited:
        return True # Already visited
        
    visited.append(normalized)
    with open(visited_path, "w") as f:
        json.dump(visited, f, indent=4)
    return False

def trigger_github_child_workflow(subdomain_path):
    """GitHub API ke zariye GH_PAT use karke naya child workflow spawn karta hai."""
    token = os.getenv("GH_PAT") # Yahan GH_PAT use ho raha hai
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

def run_agent():
    # 1. Get current domain from environment payload or 'x' file
    current_domain = os.getenv("TARGET_DOMAIN", "")
    x_file_path = "x"
    
    if not current_domain and os.path.exists(x_file_path):
        with open(x_file_path, "r") as f:
            current_domain = f.read().strip()
            
    if not current_domain:
        current_domain = "Mathematics related to Tech and Cryptography" # Default seed

    print(f"🎯 Current Exploring Domain: {current_domain}")

    # 2. Check Global Duplicates
    if check_and_update_visited(current_domain):
        print(f"🔄 Domain already visited/explored. Skipping to prevent loops: {current_domain}")
        return

    # 3. Grounding via ArXiv
    arxiv_context = fetch_arxiv_papers(current_domain)

    prompt = f"""
    You are an autonomous scientific and patent discovery agent.
    Current Domain / Focus: {current_domain}
    
    Real Research Context from ArXiv:
    {arxiv_context}
    
    Task:
    Analyze the domain and research context. 
    1. Check if this domain has reached a scientific void, academic dead-end, or a boundary where modern technology/mathematics cannot progress further.
    2. If a wall is reached, set 'is_wall_reached' to true and provide details.
    3. If research can expand, choose up to 5 ultra-specific, high-value technical/mathematical subdomains (Strictly max 5, do not exceed).
    
    Return ONLY a valid JSON object in this exact format:
    {{
        "is_wall_reached": false,
        "wall_reason": "",
        "subdomains": ["Subdomain 1", "Subdomain 2"]
    }}
    """

    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(clean_text)
    except Exception as e:
        print("❌ JSON Parse Error:", e)
        print("Raw text:", response.text)
        return

    # 4. Handle Wall Hit State
    if data.get("is_wall_reached", False):
        print("🧱 Scientific Wall Hit!")
        report = {
            "domain_path": current_domain,
            "status": "Academic Wall Detected",
            "reason": data.get("wall_reason", "No reason provided"),
            "priority_score": 85
        }
        with open("the_wall_report.json", "w") as f:
            json.dump(report, f, indent=4)
        
        os.makedirs("ideas", exist_ok=True)
        with open("ideas/execution_trail.md", "a") as trail:
            trail.write(f"\n- **Wall Reached at:** {current_domain} | **Reason:** {data.get('wall_reason')}")
    
    # 5. Handle Expansion State (Max 5 subdomains)
    else:
        subdomains = data.get("subdomains", [])[:5] # Enforce strict max 5 limit
        print(f"🌿 Selected Subdomains ({len(subdomains)}): {subdomains}")
        
        for sub in subdomains:
            next_path = f"{current_domain} -> {sub}"
            
            # Trigger GitHub API to spawn independent child workflow
            trigger_github_child_workflow(next_path)
            time.sleep(2) # Rate limit gap between dispatches

if __name__ == "__main__":
    run_agent()
    
