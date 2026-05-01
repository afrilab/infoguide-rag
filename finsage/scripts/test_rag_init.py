import sys
import yaml

sys.path.insert(0, "/cta/users/teoman.arabul/finsage/src")

from utils.ragManager import RAGManager

CONFIG_PATH = "/cta/users/teoman.arabul/finsage/config/production.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

print("[INFO] Creating RAGManager...")
rag = RAGManager(config)
print("[INFO] RAGManager created successfully")
