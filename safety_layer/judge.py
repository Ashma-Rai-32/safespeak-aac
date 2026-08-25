"""
The safety layer's core judgment function.

judge(patient_input, generated_phrase, judge_model) ->
    {
      "predicted_label": "SUPPORTED" | "UNSUPPORTED",
      "reason": str,
      "violation_category": str,
      "deterministic_flags": dict,
    }

Combination policy: deterministic checks are a fast, cheap first pass. The LLM
judge (scoring prompt against the locked criterion) makes the actual call on
subtler fabrications the deterministic checks can't catch (e.g. fabricated
consent, invented causal claims). Final policy:

  - If the LLM judge says UNSUPPORTED, the result is UNSUPPORTED (LLM judge is
    authoritative for nuanced cases).
  - If the LLM judge says SUPPORTED but a deterministic check flagged something,
    we override to UNSUPPORTED. This is a safety-first tiebreak: a mechanical
    red flag (unlicensed entity, negation mismatch, unlicensed urgency) should
    not be silently overridden by an LLM that may have been too lenient. Better
    to over-block (false_blocked cost) than silently pass a fabrication
    (false_supported cost, the more dangerous error per docs/01).
  - If both agree, that's the result.

This override policy is itself a documented design decision, not an implicit
detail, because it directly affects the false_supported_rate / false_blocked_rate
tradeoff described in docs/02-bigquery-schema.md section 6.
"""

from safety_layer.deterministic_checks import run_deterministic_checks
from safety_layer.gemini_client import call_gemini, parse_json_response
from safety_layer.scoring_prompt import build_scoring_prompt, PROMPT_VERSION

VALID_LABELS = {"SUPPORTED", "UNSUPPORTED"}
VALID_CATEGORIES = {
    "consent_fabrication", "negation_flip", "entity_injection",
    "timeframe_urgency", "causal_fabrication", "none",
}


def judge(patient_input, generated_phrase, judge_model="gemini-3.1-flash-lite"):
    det_flags = run_deterministic_checks(patient_input, generated_phrase)

    prompt = build_scoring_prompt(patient_input, generated_phrase)
    raw_response, latency_ms = call_gemini(prompt, model_name=judge_model)

    try:
        parsed = parse_json_response(raw_response)
        llm_verdict = parsed.get("verdict", "").upper()
        llm_reason = parsed.get("reason", "")
        llm_category = parsed.get("violation_category", "none")
    except (ValueError, AttributeError) as e:
        # If the judge model returns malformed JSON, fail safe: block and
        # flag for human review rather than silently passing it through.
        return {
            "predicted_label": "UNSUPPORTED",
            "reason": f"Judge model returned unparseable output, failing safe. Raw error: {e}",
            "violation_category": "none",
            "deterministic_flags": det_flags,
            "judge_model": judge_model,
            "prompt_version": PROMPT_VERSION,
            "raw_judge_response": raw_response,
        }

    if llm_verdict not in VALID_LABELS:
        llm_verdict = "UNSUPPORTED"
        llm_reason = f"(Judge model gave invalid verdict '{llm_verdict}', failing safe.) {llm_reason}"

    final_label = llm_verdict
    final_reason = llm_reason
    final_category = llm_category if llm_category in VALID_CATEGORIES else "none"

    if llm_verdict == "SUPPORTED" and det_flags["any_flag"]:
        final_label = "UNSUPPORTED"
        flag_summary = []
        if det_flags["negation_mismatch"]:
            flag_summary.append("negation mismatch")
        if det_flags["injected_entities"]:
            flag_summary.append(f"unlicensed entities: {det_flags['injected_entities']}")
        if det_flags["unlicensed_urgency"]:
            flag_summary.append("unlicensed urgency escalation")
        final_reason = (
            f"Overridden to UNSUPPORTED by deterministic check(s): {'; '.join(flag_summary)}. "
            f"(LLM judge had said SUPPORTED: \"{llm_reason}\")"
        )

    return {
        "predicted_label": final_label,
        "reason": final_reason,
        "violation_category": final_category,
        "deterministic_flags": det_flags,
        "judge_model": judge_model,
        "prompt_version": PROMPT_VERSION,
        "raw_judge_response": raw_response,
    }
