"""
Mock Stripe + HubSpot data representing the multi-location dental group scenario.
In production this is replaced by live API calls to both platforms.
"""

STRIPE_CUSTOMERS = [
    {"stripe_customer_id": "cus_AAA001", "name": "Auburn Dental Group", "email": "billing@auburndentalgroup.com"},
    {"stripe_customer_id": "cus_BBB002", "name": "Demit Dental - Main", "email": "admin@demitdental.com"},
    {"stripe_customer_id": "cus_BBB003", "name": "Demit Dental - Eastside", "email": "admin@demitdental.com"},
    {"stripe_customer_id": "cus_CCC004", "name": "Bright Smiles Dental", "email": "billing@brightsmiles.io"},
    {"stripe_customer_id": "cus_DDD005", "name": "Sunrise Ortho & Dental", "email": "ops@sunriseortho.com"},
    {"stripe_customer_id": "cus_DDD006", "name": "Sunrise Ortho - Westlake", "email": "ops@sunriseortho.com"},
    {"stripe_customer_id": "cus_DDD007", "name": "Sunrise Ortho - Midtown", "email": "ops@sunriseortho.com"},
    {"stripe_customer_id": "cus_EEE008", "name": "Family First Dentistry", "email": "hello@familyfirst.dental"},
]

STRIPE_SUBSCRIPTIONS = [
    {"stripe_sub_id": "sub_001", "stripe_customer_id": "cus_AAA001", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-15", "past_due": False},
    {"stripe_sub_id": "sub_002", "stripe_customer_id": "cus_AAA001", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-15", "past_due": False},
    {"stripe_sub_id": "sub_003", "stripe_customer_id": "cus_AAA001", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-15", "past_due": False},
    {"stripe_sub_id": "sub_004", "stripe_customer_id": "cus_BBB002", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-20", "past_due": False},
    {"stripe_sub_id": "sub_005", "stripe_customer_id": "cus_BBB003", "status": "past_due", "mrr": 299, "plan": "Pro", "current_period_end": "2026-05-20", "past_due": True},
    {"stripe_sub_id": "sub_006", "stripe_customer_id": "cus_CCC004", "status": "active",   "mrr": 199, "plan": "Starter", "current_period_end": "2026-06-10", "past_due": False},
    {"stripe_sub_id": "sub_007", "stripe_customer_id": "cus_DDD005", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-25", "past_due": False},
    {"stripe_sub_id": "sub_008", "stripe_customer_id": "cus_DDD006", "status": "active",   "mrr": 299, "plan": "Pro", "current_period_end": "2026-06-25", "past_due": False},
    {"stripe_sub_id": "sub_009", "stripe_customer_id": "cus_DDD007", "status": "canceled", "mrr": 0,   "plan": "Pro", "current_period_end": "2026-05-01", "past_due": False},
    {"stripe_sub_id": "sub_010", "stripe_customer_id": "cus_EEE008", "status": "active",   "mrr": 199, "plan": "Starter", "current_period_end": "2026-06-18", "past_due": False},
]

HUBSPOT_COMPANIES = [
    {"hs_company_id": "HS-1001", "name": "Auburn Dental Group",    "domain": "auburndentalgroup.com", "owner": "Jake P."},
    {"hs_company_id": "HS-1002", "name": "Demit Dental",           "domain": "demitdental.com",       "owner": "Sarah M."},
    {"hs_company_id": "HS-1003", "name": "Bright Smiles Dental",   "domain": "brightsmiles.io",       "owner": "Jake P."},
    {"hs_company_id": "HS-1004", "name": "Sunrise Orthodontics",   "domain": "sunriseortho.com",      "owner": "Sarah M."},
    {"hs_company_id": "HS-1005", "name": "Family First Dentistry", "domain": "familyfirst.dental",    "owner": "Jake P."},
]

HUBSPOT_LOCATIONS = [
    {"hs_location_id": "LOC-101", "hs_company_id": "HS-1001", "name": "Auburn Dental - Main St"},
    {"hs_location_id": "LOC-102", "hs_company_id": "HS-1001", "name": "Auburn Dental - North"},
    {"hs_location_id": "LOC-103", "hs_company_id": "HS-1001", "name": "Auburn Dental - Eastside"},
    {"hs_location_id": "LOC-104", "hs_company_id": "HS-1002", "name": "Demit Dental - Main"},
    {"hs_location_id": "LOC-105", "hs_company_id": "HS-1002", "name": "Demit Dental - Eastside"},
    {"hs_location_id": "LOC-106", "hs_company_id": "HS-1003", "name": "Bright Smiles - Downtown"},
    {"hs_location_id": "LOC-107", "hs_company_id": "HS-1004", "name": "Sunrise - Westlake"},
    {"hs_location_id": "LOC-108", "hs_company_id": "HS-1004", "name": "Sunrise - Midtown"},
    {"hs_location_id": "LOC-109", "hs_company_id": "HS-1004", "name": "Sunrise - Main (Canceled)"},
    {"hs_location_id": "LOC-110", "hs_company_id": "HS-1005", "name": "Family First - Oak Ave"},
]

# Canonical mapping table: the "data spine" linking all three systems
MAPPING_TABLE = [
    {"stripe_sub_id": "sub_001", "stripe_customer_id": "cus_AAA001", "hs_location_id": "LOC-101", "hs_company_id": "HS-1001"},
    {"stripe_sub_id": "sub_002", "stripe_customer_id": "cus_AAA001", "hs_location_id": "LOC-102", "hs_company_id": "HS-1001"},
    {"stripe_sub_id": "sub_003", "stripe_customer_id": "cus_AAA001", "hs_location_id": "LOC-103", "hs_company_id": "HS-1001"},
    {"stripe_sub_id": "sub_004", "stripe_customer_id": "cus_BBB002", "hs_location_id": "LOC-104", "hs_company_id": "HS-1002"},
    {"stripe_sub_id": "sub_005", "stripe_customer_id": "cus_BBB003", "hs_location_id": "LOC-105", "hs_company_id": "HS-1002"},
    {"stripe_sub_id": "sub_006", "stripe_customer_id": "cus_CCC004", "hs_location_id": "LOC-106", "hs_company_id": "HS-1003"},
    {"stripe_sub_id": "sub_007", "stripe_customer_id": "cus_DDD005", "hs_location_id": "LOC-107", "hs_company_id": "HS-1004"},
    {"stripe_sub_id": "sub_008", "stripe_customer_id": "cus_DDD006", "hs_location_id": "LOC-108", "hs_company_id": "HS-1004"},
    {"stripe_sub_id": "sub_009", "stripe_customer_id": "cus_DDD007", "hs_location_id": "LOC-109", "hs_company_id": "HS-1004"},
    {"stripe_sub_id": "sub_010", "stripe_customer_id": "cus_EEE008", "hs_location_id": "LOC-110", "hs_company_id": "HS-1005"},
]
