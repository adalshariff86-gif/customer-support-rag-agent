"""List available Gemini models.

Requires the GEMINI_API_KEY environment variable (or .env) to be set.
"""

import os
import sys

from google import genai


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Fall back to loading from .env via the app settings
        try:
            from app.core.config import settings

            api_key = settings.GEMINI_API_KEY
        except Exception:
            pass

    if not api_key:
        print("Error: GEMINI_API_KEY not set. Add it to your .env or environment.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    for model in client.models.list():
        print(model.name)


if __name__ == "__main__":
    main()
