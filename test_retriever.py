import json

from knowledge_base.retriever import retrieve_context

with open("sample_data/opportunity.json", "r") as f:
    deal = json.load(f)

context = retrieve_context(deal)

print("\n========== RETRIEVED CONTEXT ==========\n")
print(context)