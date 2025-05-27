import os
from valyu import Valyu

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

response = valyu.search("What is machine learning?")

print(response)
