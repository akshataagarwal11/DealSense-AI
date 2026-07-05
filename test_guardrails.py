import json

from guardrails.engine import run_guardrails


with open("sample_data/opportunity.json", "r") as f:
    deal = json.load(f)

result = run_guardrails(deal)

print("\n===== GUARDRAIL RESULTS =====")
print(json.dumps(result, indent=4))