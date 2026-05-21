import json
import difflib
from typing import List, Dict

# --- CANONICAL DATA MODELS ---

PROSPECT_INVOICE = [
    {"desc": "Gloves Nitrile Blue Med 100/bx", "sku": "GLV-123-M", "price": 15.50, "qty": 10},
    {"desc": "Lidocaine 2% 1:100k Epinephrine", "sku": "LIDO-555", "price": 45.00, "qty": 2},
    {"desc": "Cotton Rolls #2 Medium 2000/cs", "sku": "COT-001", "price": 22.00, "qty": 5},
    {"desc": "Masks Level 3 Blue 50/bx", "sku": "MSK-L3", "price": 12.00, "qty": 20},
    {"desc": "Exact Match Item", "sku": "SC-EXACT-99", "price": 50.00, "qty": 1},
]

SOURCECLUB_CATALOG = [
    {"name": "Nitrile Exam Gloves, Blue, Medium, 100/Box", "sku": "SC-GLV-BM", "price": 9.50, "mfg_sku": "GLV-123-M"},
    {"name": "Lidocaine HCl 2% with Epinephrine 1:100,000", "sku": "SC-LIDO-2", "price": 32.00, "mfg_sku": "LIDO-555"},
    {"name": "Cotton Rolls #2, Non-Sterile, 2000/Case", "sku": "SC-COT-2", "price": 16.50, "mfg_sku": "COT-001"},
    {"name": "Earloop Face Mask, Level 3, Blue, 50/Box", "sku": "SC-MSK-L3B", "price": 8.00, "mfg_sku": "MSK-L3"},
    {"name": "Exact Match Item", "sku": "SC-EXACT-99", "price": 40.00, "mfg_sku": "MFG-99"},
]

# --- MATCHING ENGINE LOGIC ---

class MatchingEngine:
    def __init__(self, catalog: List[Dict]):
        self.catalog = catalog

    def stage_1_deterministic(self, p_item: Dict) -> Dict:
        """Exact SKU or Manufacturer SKU match."""
        for c_item in self.catalog:
            if p_item['sku'] == c_item['sku'] or p_item['sku'] == c_item['mfg_sku']:
                return c_item
        return None

    def stage_2_semantic_retrieval(self, p_item: Dict) -> List[Dict]:
        """Simulating Vector Search candidate retrieval."""
        candidates = []
        for c_item in self.catalog:
            score = difflib.SequenceMatcher(None, p_item['desc'].lower(), c_item['name'].lower()).ratio()
            if score > 0.4:
                candidates.append((score, c_item))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[:3]

    def stage_3_llm_judge(self, p_item: Dict, candidates: List) -> Dict:
        """Simulating LLM adjudication for the best candidate."""
        if not candidates:
            return None
        # Mocking LLM logic: picking the top candidate if it's over a threshold
        best_score, best_match = candidates[0]
        if best_score > 0.6:
            return best_match
        return None

    def process_invoice(self, invoice: List[Dict]):
        results = []
        for p_item in invoice:
            # 1. Deterministic
            match = self.stage_1_deterministic(p_item)
            method = "Deterministic"
            
            # 2. Semantic + LLM (if no deterministic match)
            if not match:
                candidates = self.stage_2_semantic_retrieval(p_item)
                match = self.stage_3_llm_judge(p_item, candidates)
                method = "LLM/Semantic" if match else "N/A"

            # Confidence Logic
            confidence = 1.0 if method == "Deterministic" else 0.85 if match else 0.0
            status = "AUTO-ACCEPT" if confidence > 0.9 else "REVIEW-QUEUE" if match else "NO-MATCH"

            results.append({
                "prospect": p_item,
                "match": match,
                "method": method,
                "confidence": confidence,
                "status": status
            })
        return results

# --- REPORT GENERATION ---

def print_report(results):
    print(f"{'Method':<15} | {'Prospect Item':<35} | {'SC Match':<35} | {'Savings':<8} | {'Status'}")
    print("-" * 115)
    total_savings = 0
    for r in results:
        p = r['prospect']
        m = r['match']
        savings = (p['price'] - m['price']) * p['qty'] if m else 0
        total_savings += savings
        
        m_name = m['name'] if m else "N/A"
        print(f"{r['method']:<15} | {p['desc'][:35]:<35} | {m_name[:35]:<35} | ${savings:<7.2f} | {r['status']}")
    
    print("-" * 115)
    print(f"{'TOTAL MONTHLY SAVINGS':<89} | ${total_savings:<7.2f}")
    print(f"{'ANNUAL SAVINGS ESTIMATE':<89} | ${total_savings * 12:<7.2f}")

if __name__ == "__main__":
    engine = MatchingEngine(SOURCECLUB_CATALOG)
    results = engine.process_invoice(PROSPECT_INVOICE)
    print("SourceClub Savings Analysis Engine - 3-Stage Pipeline POC\n")
    print_report(results)
