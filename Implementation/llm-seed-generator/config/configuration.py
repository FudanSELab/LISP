import configparser
import os

__all__ = [
    "CFG_PATH", "LLM_OPENAI_KEY",
]

# llm-seed-generator.cfg
CFG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),"llm-seed-generator.cfg")
CONFIG = configparser.ConfigParser()
CONFIG.read(CFG_PATH)

LLM_OPENAI_KEY = CONFIG.get("LLM", "OPENAI_KEY")
os.environ["OPENAI_API_KEY"] = LLM_OPENAI_KEY
