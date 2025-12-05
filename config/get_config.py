import yaml
from box import Box # Importul tău corectat
import os

# Calea către rădăcina proiectului
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(BASE_DIR, 'config', 'config.yml')

# --- MODIFICAREA ESTE AICI ---
# Forțăm deschiderea fișierului cu encodare UTF-8
with open(config_path, 'r', encoding='utf-8') as f:
    cfg_data = yaml.safe_load(f)

# Convertim dicționarul în obiect
cfg = Box(cfg_data)