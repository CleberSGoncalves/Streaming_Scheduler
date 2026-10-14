import sys
import os
import xml.etree.ElementTree as ET
import base64
from cryptography.fernet import Fernet, InvalidToken

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_app_path(rel_path):
    if not rel_path:
        return get_app_dir()
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(get_app_dir(), rel_path)

# === Criptografia Fernet ===
def carregar_env_criptografado(caminho=None):
    """
    Carrega um .env criptografado e retorna um dicionário com os valores descriptografados
    """
    if caminho is None:
        caminho = get_app_path(".env.enc")
    else:
        caminho = get_app_path(caminho)
    env_dict = {}
    try:
        with open(caminho, "r") as file:
            for line in file:
                if "=" in line:
                    chave, valor_cripto = line.strip().split("=", 1)
                    try:
                        valor_descriptografado = descriptografar(valor_cripto)
                        env_dict[chave] = valor_descriptografado
                    except Exception:
                        pass  # ignora linhas que não são criptografadas
    except FileNotFoundError:
        print(f"[ERRO] Arquivo {caminho} não encontrado")
    return env_dict

def gerar_chave(caminho=None):
    """Gera e salva uma nova chave de criptografia em 'secret.key'."""
    if caminho is None:
        caminho = get_app_path("secret.key")
    else:
        caminho = get_app_path(caminho)
    key = Fernet.generate_key()
    with open(caminho, "wb") as f:
        f.write(key)

def carregar_chave(caminho=None):
    """Carrega a chave de criptografia do arquivo 'secret.key'."""
    if caminho is None:
        caminho = get_app_path("secret.key")
    else:
        caminho = get_app_path(caminho)
    return open(caminho, "rb").read()

def criptografar(texto):
    """Criptografa uma string com Fernet."""
    fernet = Fernet(carregar_chave())
    return fernet.encrypt(texto.encode()).decode()

def descriptografar(texto):
    """Descriptografa uma string criptografada com Fernet, ou retorna o texto original se não for válido."""
    try:
        # Testa se é uma string Fernet válida (começa com 'gAAAA' e é base64)
        if not texto or not texto.startswith("gAAAA"):
            return texto  # já é texto plano

        fernet = Fernet(carregar_chave())
        return fernet.decrypt(texto.encode()).decode()
    except InvalidToken:
        return texto  # retorna o valor original se não for possível descriptografar
    except Exception as e:
        print(f"[ERRO] ao descriptografar: {e}")
        return texto
# === .env.enc ===

def get_env_value(chave, caminho=None):
    """
    Retorna o valor descriptografado da chave fornecida do arquivo .env.enc
    """
    if caminho is None:
        caminho = get_app_path(".env.enc")
    else:
        caminho = get_app_path(caminho)
    try:
        with open(caminho, "r") as file:
            for line in file:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    if k == chave:
                        return descriptografar(v)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo {caminho} não encontrado")
    except Exception as e:
        print(f"[ERRO] ao ler {chave}: {str(e)}")
    return None

# === config.xml ===

def get_config_value(tag, caminho=None):
    """
    Retorna o valor descriptografado de uma tag do config.xml.
    Exemplo: get_config_value("usuario_prime")
    """
    if caminho is None:
        caminho = get_app_path("config.xml")
    else:
        caminho = get_app_path(caminho)
    try:
        tree = ET.parse(caminho)
        root = tree.getroot()
        elem = root.find(tag)
        if elem is not None and elem.text:
            return descriptografar(elem.text)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo {caminho} não encontrado")
    except Exception as e:
        print(f"[ERRO] ao ler tag '{tag}' no config.xml: {str(e)}")
    return None

# === auth.xml ===

def get_auth_value(tag, caminho=None):
    """
    Retorna o valor descriptografado de uma tag do auth.xml.
    Exemplo: get_auth_value("email")
    """
    if caminho is None:
        caminho = get_app_path("auth.xml")
    else:
        caminho = get_app_path(caminho)
    try:
        tree = ET.parse(caminho)
        root = tree.getroot()
        elem = root.find(tag)
        if elem is not None and elem.text:
            return descriptografar(elem.text)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo {caminho} não encontrado")
    except Exception as e:
        print(f"[ERRO] ao ler tag '{tag}' no auth.xml: {str(e)}")
    return None
