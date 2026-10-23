from dotenv import load_dotenv

load_dotenv()

from ask_ai.llm import ask_llm, clean_command
from ask_ai.prompts import COMMAND_PROMPT

print(clean_command(ask_llm(COMMAND_PROMPT, "list all files including hidden ones")))