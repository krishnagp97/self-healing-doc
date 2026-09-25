import os
import time
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

Documentation section:
{review_item["heading"]}

Current documentation:
{review_item["content"]}

Changed symbols:
{review_item["changed_symbols"]}

Determine:
1. Why the documentation may be outdated.
2. What information is missing or incorrect.
3. Whether the documentation needs to be updated.

If an update is needed, provide the COMPLETE replacement content
for the documentation section.

Important:
- Return only the replacement content under "Suggested update:".
- Do not include the Markdown section heading itself.
- Preserve useful existing information from the documentation.
- Do not invent information that is not supported by the code change.
- If the documentation is already accurate or you cannot confidently
  produce a correct replacement, leave "Suggested update:" empty.

Return the answer in this exact format:

Issue:
<explanation>

Suggested update:
<complete replacement section content, or empty>
"""

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            text = response.text.strip()
            break

        except Exception as e:
            print(f"Gemini error (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "issue": "AI review is temporarily unavailable.",
                    "suggested_update": "",
                }

            time.sleep(2 ** attempt)

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
        "success": True,
        "issue": issue,
        "suggested_update": suggestion,
    }