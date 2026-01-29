from openai import OpenAI
import os
from typing import Optional

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def generate_recovery_tip(
    muscle_group: str,
    intensity: str = "intense",
    max_words: int = 50
) -> str:
    """
    Generate a short, actionable recovery tip using Groq API.
    
    Args:
        muscle_group: e.g., "Chest", "Quadriceps"
        intensity: "intense", "moderate", "light"
        max_words: Max length of tip
    
    Returns:
        str: Recovery tip (fallback if API fails)
    """
    prompt = f"""
You are a certified sports recovery specialist.
Give ONE short, highly actionable recovery tip for the {muscle_group} muscle group 
after a {intensity} workout. 
Focus on practical steps the user can take immediately.
Keep it under {max_words} words.
Be specific, motivational, and evidence-based.
Output ONLY the tip text — no introduction, no quotes, no extra words.
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,              
            max_tokens=80,                
            top_p=0.9
        )

        tip = response.choices[0].message.content.strip()
        
        
        words = tip.split()
        if len(words) > max_words:
            tip = " ".join(words[:max_words]) + "..."

        return tip

    except Exception as e:
        return (
            f"Prioritize rest for {muscle_group}. "
            f"Hydrate well, do light stretching, and eat protein-rich food within 2 hours."
        )