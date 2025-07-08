from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import os
import random

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary(agent_id: str, action_type: str, description: str | None) -> str:
    prompt = f"""
    Summarize the following agent action in 1-2 concise security-aware sentences.

    Agent ID: {agent_id}
    Action Type: {action_type}
    Description: {description or "No description provided."}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt.strip()}],
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI summary generation failed: {e}")
        # Mocked fallback summary if OpenAI quota is exceeded or error occurs
        return f"[MOCK SUMMARY] Agent '{agent_id}' performed '{action_type}'. Please review this behavior manually."

def generate_rule(agent_actions: List[Dict]) -> Dict:
    """
    Generate a smart rule based on recent agent activity using simple heuristics
    (simulating LLM behavior).
    """

    if not agent_actions:
        return {
            "rule": "No agent actions available to generate rule.",
            "condition": {},
            "action": "none"
        }

    action_types = [a["action_type"] for a in agent_actions]
    type_counts = {t: action_types.count(t) for t in set(action_types)}
    most_common_type = max(type_counts, key=type_counts.get)

    for a in agent_actions:
        if a["action_type"] == most_common_type:
            selected = a
            break

    rule_text = f"If an agent performs '{most_common_type}'"
    condition = {"action_type": most_common_type}

    if selected.get("tool_name"):
        condition["tool_name"] = selected["tool_name"]
        rule_text += f" using {selected['tool_name']}"

    rule_text += ", flag as high risk."

    return {
        "rule": rule_text,
        "condition": condition,
        "action": "flag_high_risk"
    }

def generate_smart_rule(agent_id: str, action_type: str, description: str):
    return {
        "id": f"{agent_id}-{action_type}",
        "agent_id": agent_id,
        "action_type": action_type,
        "description": description,
        "condition": f"agent_id == '{agent_id}' and action_type == '{action_type}'",
        "action": "alert",
        "risk_level": "medium",
        "recommendation": "Review this behavior pattern for anomalies."
    }
