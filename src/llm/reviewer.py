import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


def review_documentation(review_item):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a software documentation reviewer.

Analyze the following documentation and code change.

Documentation:
{review_item["content"]}

Changed symbols:
{review_item["changed_symbols"]}

Determine:
1. Why the documentation may be outdated.
2. What information is missing or incorrect.
3. A concise suggested documentation update.

Return the answer in this exact format:

Issue:
<explanation>

Suggested update:
<updated documentation>
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        text = response.text.strip()

    except Exception as e:
        print(f"Gemini error: {e}")
        return {
            "issue": "AI review is temporarily unavailable.",
            "suggested_update": "",
        }

    if "Suggested update:" in text:
        issue, suggestion = text.split(
            "Suggested update:",
            1,
        )

        issue = issue.replace("Issue:", "").strip()
        suggestion = suggestion.strip()
    else:
        issue = text
        suggestion = ""

    return {
        "issue": issue,
        "suggested_update": suggestion,
    }