import json
import os
import time
from google.genai import errors
from dotenv import load_dotenv
from google import genai
from src.llm.candidates import rank_candidates


load_dotenv()


class SemanticLinkerError(Exception):
    """Raised when semantic linking cannot be completed."""


def _build_prompt(section, candidates):
    candidate_text = "\n".join(
        f"- ID: {candidate['id']}\n"
        f"  Symbol: {candidate['name']}\n"
        f"  File: {candidate['file']}"
        for candidate in candidates
    )

    return f"""
You are a software documentation-to-code linker.

Your task is to determine which code symbol or symbols a
Markdown documentation section is describing.

Documentation heading:
{section["heading"]}

Documentation content:
{section["content"]}

Candidate code symbols:
{candidate_text}

Rules:
- Only select symbols from the candidate list.
- Do not invent symbols.
- Select a symbol only when the documentation provides enough
  semantic evidence that it refers to that symbol.
- If the documentation is ambiguous, do not guess.
- A section may refer to more than one symbol.
- Confidence must be between 0 and 1.

Return ONLY valid JSON in this format:

{{
  "matches": [
    {{
      "code_id": "candidate-id",
      "confidence": 0.95,
      "reason": "brief explanation"
    }}
  ]
}}

If there is no confident match:

{{
  "matches": []
}}
"""


def _call_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise SemanticLinkerError(
            "GEMINI_API_KEY is not set"
        )

    client = genai.Client(api_key=api_key)

    model = os.getenv(
        "GEMINI_LINKER_MODEL",
        "gemini-3.6-flash",
    )

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            text = response.text.strip()

            try:
                return json.loads(text)

            except json.JSONDecodeError as exc:
                print(
                    f"Gemini returned invalid JSON "
                    f"(attempt {attempt + 1}/{max_retries}): {exc}"
                )

                if attempt == max_retries - 1:
                    raise SemanticLinkerError(
                        "Gemini returned an invalid semantic linking response."
                    ) from exc

                time.sleep(2 ** attempt)

        except errors.ClientError as exc:
            print(
                f"Gemini semantic linker error "
                f"(attempt {attempt + 1}/{max_retries}): {exc}"
            )

            if exc.code == 429:
                raise SemanticLinkerError(
                    "Gemini quota or rate limit has been exceeded."
                ) from exc

            if attempt == max_retries - 1:
                raise SemanticLinkerError(
                    "Gemini semantic linking is temporarily unavailable."
                ) from exc

            time.sleep(2 ** attempt)

        except Exception as exc:
            print(
                f"Gemini semantic linker error "
                f"(attempt {attempt + 1}/{max_retries}): {exc}"
            )

            if attempt == max_retries - 1:
                raise SemanticLinkerError(
                    "Gemini semantic linking is temporarily unavailable."
                ) from exc

            time.sleep(2 ** attempt)


def semantic_link_sections(sections, chunks):
    """
    Resolve unresolved Markdown sections using Gemini.

    Returns:
        {
            "status": "success",
            "links": [...],
            "unresolved": [...]
        }
    """

    links = []
    unresolved = []

    for section in sections:

        if not chunks:
            unresolved.append(section["id"])
            continue

        candidates = rank_candidates(
            section,
            chunks,
            limit=10,
        )
        if not candidates:
            unresolved.append(section["id"])
            continue

        prompt = _build_prompt(
            section,
            candidates,
        )
        
        result = _call_gemini(prompt)

        matches = result.get("matches", [])

        valid_ids = {
            chunk["id"]
            for chunk in chunks
        }

        section_matched = False

        for match in matches:

            code_id = match.get("code_id")
            confidence = match.get("confidence")

            if code_id not in valid_ids:
                continue

            if not isinstance(confidence, (int, float)):
                continue

            if confidence < 0.85:
                continue

            chunk = next(
                chunk
                for chunk in chunks
                if chunk["id"] == code_id
            )

            links.append({
                "doc_id": section["id"],
                "code_id": code_id,
                "heading": section["heading"],
                "symbol": chunk["name"],
                "confidence": confidence,
                "source": "semantic",
            })

            section_matched = True

        if not section_matched:
            unresolved.append(section["id"])

    return {
        "status": "success",
        "links": links,
        "unresolved": unresolved,
    }