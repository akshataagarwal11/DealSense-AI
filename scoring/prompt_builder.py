import config
 
def build_scoring_prompt(deal: dict, guardrail_output: dict,
                          rag_context: str) -> str:
    '''
    Construct the full Claude API prompt.
    This is the most critical function in the project.
    Every field must be present and correctly formatted.
    '''
 
    critical_flags_text = '\n'.join(
        guardrail_output['critical_flags']
    ) or 'None'
    all_flags_text = '\n'.join(
        guardrail_output['flags']
    ) or 'None'
    force_score_text = (
        f"FORCED TO: {guardrail_output['force_score']} "
        f"(critical guardrail triggered — do not override)"
        if guardrail_output['force_score']
        else 'No force — apply your judgment'
    )
 
    return f'''You are DealSense AI, an enterprise sales risk analyst.
Your role: assess deal risk with full transparency and actionable reasoning.
You must respond ONLY with valid JSON. No preamble. No markdown. No explanation
outside the JSON object. Failure to return valid JSON will break the pipeline.
 
=== SCORING POLICIES AND HISTORICAL CONTEXT ===
{rag_context}
 
=== GUARDRAIL ENGINE OUTPUT ===
Pre-Score: {guardrail_output['pre_score']}
Force Score: {force_score_text}
Critical Flags (CANNOT BE OVERRIDDEN):
{critical_flags_text}
All Flags:
{all_flags_text}
Needs Human Review: {guardrail_output['needs_human_review']}
 
=== DEAL DATA ===
Deal Name: {deal['name']}
Account: {deal['account_name']}
Stage: {deal['stage']}
Deal Value: ${deal['amount']:,.0f}
Probability: {deal['probability']}%
Close Date: {deal['close_date']}
Days to Close: {deal['days_to_close']}
Days Since Last Activity: {deal['days_since_activity']}
Last Activity Date: {deal['last_activity_date']}
Company Size: {deal['company_size']} ({deal['num_employees']} employees)
Lead Source: {deal['lead_source']}
Next Step: {deal['next_step']}
Owner: {deal['owner_name']}
 
=== SCORING INSTRUCTIONS ===
1. If force_score is set, final_score MUST match it exactly.
2. Reference the policy documents in policy_references.
3. Every risk factor must have a specific, actionable explanation.
4. Recommended actions must name a specific owner and timeline.
5. Confidence reflects how certain you are given available data.
6. Narrative must be professional, specific, and useful to a sales manager.
 
Respond with ONLY this JSON structure:
{{
  "final_score": "High|Medium|Low",
  "confidence": 0-100,
  "risk_factors": [
    {{"factor": "", "severity": "High|Medium|Low", "explanation": ""}}
    // exactly 5 items
  ],
  "recommended_actions": [
    {{"action": "", "timeline": "", "owner": ""}}
    // exactly 3 items
  ],
  "policy_references": [""],
  "narrative_summary": "",
  "confidence_explanation": ""
}}'''
