import json

def extract_first_json_object(text: str) -> str:
    """
    If the model returns:
      Sure! { ...json... }
    we recover the first top-level JSON object.
    """
    if not text:
        raise ValueError("Empty LLM response")

    s = text.strip()

    # Fast path: already valid JSON
    try:
        json.loads(s)
        return s
    except Exception:
        pass

    # Find first '{' and then balance braces
    start = s.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start:i+1]
                json.loads(candidate)  # validate
                return candidate

    raise ValueError("Unbalanced JSON braces in response")
