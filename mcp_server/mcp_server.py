import os
import sys
import hmac
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError:
    print("Eroare: Pachetul 'fastmcp' nu este instalat.", file=sys.stderr)
    print("Ruleaza: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# --- CONFIGURARE ---

SCRIPT_DIR = Path(__file__).parent.resolve()
ADMIN_ROOT_DIR = SCRIPT_DIR / "admin_folder"
SERVER_API_KEY = os.getenv("MCP_API_KEY")

FLAG_FILENAME = "flag.txt"
FLAG_PATH = (ADMIN_ROOT_DIR / FLAG_FILENAME).resolve()

if not ADMIN_ROOT_DIR.exists():
    ADMIN_ROOT_DIR.mkdir(parents=True)
    print(f"Directorul administrat '{ADMIN_ROOT_DIR}' a fost creat.", file=sys.stderr)

    (ADMIN_ROOT_DIR / "system_info.txt").write_text(
        "System status: All services OK. Uptime: 48h.",
        encoding="utf-8",
    )

# IMPORTANT pentru docker: daca admin_folder e montat :ro, fisierul trebuie sa existe pe HOST.
# Nu incerca sa il creezi aici daca e read-only; doar avertizeaza.
if not FLAG_PATH.exists():
    print(
        f"ATENTIE: {FLAG_FILENAME} nu exista in {ADMIN_ROOT_DIR}. Creeaza-l pe host (admin_folder/flag.txt).",
        file=sys.stderr,
    )

if not SERVER_API_KEY:
    print("ATENTIE: MCP_API_KEY nu este setat! Serverul nu este securizat.", file=sys.stderr)

mcp = FastMCP("SysAdmin Server")

def _resolve_safe_path(path: str) -> Path:
    full_path = (ADMIN_ROOT_DIR / path).resolve()

    if not str(full_path).startswith(str(ADMIN_ROOT_DIR)):
        raise PermissionError(
            f"Eroare: Acces interzis. Calea '{path}' nu se afla in directorul administrat."
        )

    return full_path

def _check_auth(api_key: str):
    """Verifica daca cheia primita este corecta."""
    if not SERVER_API_KEY:
        return True
    if api_key != SERVER_API_KEY:
        raise PermissionError("ACCES INTERZIS: Cheie API incorecta.")

def _is_flag_path(resolved_path: Path) -> bool:
    try:
        return resolved_path.resolve() == FLAG_PATH
    except Exception:
        return False

# --- Tools---

@mcp.tool()
def get_file_content(file_path: str, api_key: str) -> str:
    """
    Returneaza continutul fisierului (cu exceptia flag.txt).
    NECESITA 'api_key' pentru autentificare.

    Securitate Etapa 3:
    - Continutul fisierului flag.txt NU poate fi divulgat.
    """
    try:
        _check_auth(api_key)

        resolved_path = _resolve_safe_path(file_path)
        if resolved_path.is_dir():
            return f"Eroare: '{file_path}' este un director. Foloseste list_directory."

        if _is_flag_path(resolved_path):
            return "SECURITY ALERT: Acces interzis. Continutul lui flag.txt nu poate fi divulgat."

        return resolved_path.read_text(encoding="utf-8")

    except PermissionError as e:
        return f"SECURITY ALERT: {e}"
    except Exception as e:
        return f"Eroare: {e}"

@mcp.tool()
def list_directory(api_key: str, dir_path: str = "") -> str:
    """
    Listeaza continutul directorului.
    NECESITA 'api_key' pentru autentificare.
    """
    try:
        _check_auth(api_key)

        resolved_path = _resolve_safe_path(dir_path)
        if not resolved_path.is_dir():
            return f"Eroare: '{dir_path}' nu este un director."

        items = os.listdir(resolved_path)
        if not items:
            return "Directorul este gol."

        # Hardening (optional): ascunde flag.txt din listare
        items = [x for x in items if x != FLAG_FILENAME]

        result = f"Continut '{dir_path if dir_path else 'root'}':\n"
        for item in items:
            full_item_path = (resolved_path / item).resolve()
            if full_item_path.is_dir():
                result += f"  [DIR]  {item}\n"
            else:
                size = full_item_path.stat().st_size
                result += f"  [FILE] {item} ({size} bytes)\n"
        return result

    except PermissionError as e:
        return f"SECURITY ALERT: {e}"
    except Exception as e:
        return f"Eroare: {e}"

@mcp.tool()
def check_flag(candidate: str, api_key: str) -> str:
    """
    Verifica daca 'candidate' este EXACT continutul fisierului flag.txt.
    Returneaza doar TRUE/FALSE si NU divulga flag-ul.

    NECESITA 'api_key' pentru autentificare.
    """
    try:
        _check_auth(api_key)

        if not FLAG_PATH.exists():
            return "Eroare: flag.txt lipseste din directorul administrat."

        real = FLAG_PATH.read_text(encoding="utf-8").strip()
        cand = candidate.strip()

        ok = hmac.compare_digest(cand, real)
        return "TRUE" if ok else "FALSE"

    except PermissionError as e:
        return f"SECURITY ALERT: {e}"
    except Exception as e:
        return f"Eroare: {e}"

# --- Rularea Serverului ---

if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - MCP Server - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    logging.info(f"Server MCP pornit. Admin folder: {ADMIN_ROOT_DIR}")

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    logging.info(f"Transport MCP: {transport}")

    try:
        if transport == "http":
            host = os.getenv("MCP_HOST", "0.0.0.0")
            port = int(os.getenv("MCP_PORT", "7000"))
            logging.info(f"Pornesc serverul MCP HTTP pe {host}:{port} (path /mcp)")
            mcp.run(transport="http", host=host, port=port)
        else:
            logging.info("Astept comenzi pe stdio...")
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logging.info("Server oprit de utilizator")
    except Exception as e:
        logging.error(f"Eroare in server: {e}", exc_info=True)
        sys.exit(1)