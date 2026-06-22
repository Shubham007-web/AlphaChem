import os

from dotenv import load_dotenv

# Load OPENAI_API_KEY from the gitignored .env file — never hardcode keys.
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")


def main():
    if not api_key:
        print("OPENAI_API_KEY is not set. Add it to your .env file.")
        return
    print("OpenAI API key loaded from environment.")


if __name__ == "__main__":
    main()
