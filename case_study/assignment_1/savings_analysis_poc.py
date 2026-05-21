import json
import difflib

# Simulated Data
PROSPECT_INVOICE = [
    {"desc": "Gloves Nitrile Blue Med 100/bx", "sku": "GLV-123-M", "price": 15.50, "qty": 10},
    {"desc": "Lidocaine 2% 1:100k Epinephrine", "sku": "LIDO-555", "price": 45.00, "qty": 2},
    {"desc": "Cotton Rolls #2 Medium 2000/cs", "sku": "COT-001", "price": 22.00, "qty": 5},
    {"desc": "Masks Level 3 Blue 50/bx", "sku": "MSK-L3", "price": 12.00, "qty": 20},
]

SOURCECLUB_CATALOG = [
    {"name": "Nitrile Exam Gloves, Blue, Medium, 100/Box", "sku": "SC-GLV-BM", "price": 9.50, "category": "Gloves"},
    {"name": "Lidocaine HCl 2% with Epinephrine 1:100,000", "sku": "SC-LIDO-2", "price": 32.00, "category": "Anesthetics"},
    {"name": "Cotton Rolls #2, Non-Sterile, 2000/Case", "sku": "SC-COT-2", "price": 16.50, "category": "Disposables"},
    {"name": "Earloop Face Mask, Level 3, Blue, 50/Box", "sku": "SC-MSK-L3B", "price": 8.00, "category": "PPE"},
]

def get_similarity(s1, s2):
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def match_items(prospect_items, catalog):
    matches = []
    for p_item in prospect_items:
        best_match = None
        highest_score = 0
        
        # In a real app, this would be a Vector Search (Pinecone/Chroma) 
        # followed by an LLM (Claude/GPT) to confirm the match.
        for c_item in catalog:
            score = get_similarity(p_item['desc'], c_item['name'])
            if score > highest_score:
                highest_score = score
                best_match = c_item
        
        # Confidence Thresholds
        status = "MATCHED" if highest_score > 0.8 else "FLAG_FOR_REVIEW"
        
        matches.append({
            "prospect_item": p_item['desc'],
            "prospect_price": p_item['price'],
            "sc_match": best_match['name'] if best_match else "N/A",
            "sc_price": best_match['price'] if best_match else 0,
            "savings_per_unit": p_item['price'] - best_match['price'] if best_match else 0,
            "total_savings": (p_item['price'] - best_match['price']) * p_item['qty'] if best_match else 0,
            "confidence": round(highest_score, 2),
            "status": status
        })
    return matches

def generate_report(matches):
    print(f"{'Prospect Item':<40} | {'SC Match':<40} | {'Savings':<10} | {'Status'}")
    print("-" * 110)
    total_savings = 0
    for m in matches:
        print(f"{m['prospect_item'][:40]:<40} | {m['sc_match'][:40]:<40} | ${m['total_savings']:<9.2f} | {m['status']}")
        total_savings += m['total_savings']
    print("-" * 110)
    print(f"{'TOTAL MONTHLY SAVINGS':<83} | ${total_savings:<9.2f}")
    print(f"{'ANNUAL SAVINGS ESTIMATE':<83} | ${total_savings * 12:<9.2f}")

if __name__ == "__main__":
    print("Running SourceClub Savings Analysis POC...\n")
    matches = match_items(PROSPECT_INVOICE, SOURCECLUB_CATALOG)
    generate_report(matches)
    
    print("\n--- LLM Integration Strategy ---")
    print("For low confidence items (e.g. status='FLAG_FOR_REVIEW'), the system would send:")
    print("Prompt: 'Is prospect product A (SKU: X) the same as catalog product B (SKU: Y)? Consider UoM differences.'")
    print("Result: LLM resolves fuzzy units like 'bx' vs 'box' and 'cs' vs 'case'.")
