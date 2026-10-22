# core/judge.py
import os
import json
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_and_rank():
    all_reports = []
    
    # Scan entire repo for wall reports
    for root, dirs, files in os.walk("."):
        if "the_wall_report.json" in files:
            file_path = os.path.join(root, "the_wall_report.json")
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    all_reports.append(data)
            except Exception:
                continue

    scored_reports = []
    for report in all_reports:
        prompt = f"""
        Rate this research domain for a patent opportunity based on 3 criteria (1 to 100 total score):
        1. Commercial Viability (Market/Industry impact)
        2. IP Patentability (Uniqueness and new path)
        3. Execution Feasibility (Can be done via software/simulation by a small team)
        
        Domain Data: {json.dumps(report)}
        
        Return ONLY a JSON object with integer key 'priority_score' and 'why_prioritised'.
        Format: {{"priority_score": 90, "why_prioritised": "reason here"}}
        """
        try:
            res = model.generate_content(prompt)
            clean_res = res.text.replace("```json", "").replace("```", "").strip()
            score_data = json.loads(clean_res)
            report['priority_score'] = score_data.get('priority_score', 50)
            report['why_prioritised'] = score_data.get('why_prioritised', '')
        except:
            report['priority_score'] = 50
            report['why_prioritised'] = "Evaluated via fallback"
            
        scored_reports.append(report)

    # Sort by highest priority score and take top 20
    top_20 = sorted(scored_reports, key=lambda x: x.get('priority_score', 0), reverse=True)[:20]

    os.makedirs("output", exist_ok=True)
    output_path = "output/TOP_20_PATENT_OPPORTUNITIES.json"
    with open(output_path, "w") as f:
        json.dump(top_20, f, indent=4)

    print(f"🎯 Goldmine Ready! Top 20 opportunities exported to {output_path}")

if __name__ == "__main__":
    evaluate_and_rank()
