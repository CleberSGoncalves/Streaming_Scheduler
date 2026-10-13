# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import re
import time
import logging
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

import requests

logger = logging.getLogger(__name__)

# -------------------- nomes de meses em PT-BR --------------------
MONTH_NAMES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# ---------- Mapa de índices da tuple -> Nome da coluna no SharePoint ----------
# Tuple (exemplo do Treeview):
# 0: Campeonato
# 1: Partida
# 2: Data (dd/MM/yyyy)
# 3: Horário (HH:mm)
# 4: Esquerda (IGNORAR)
# 5: 10 (IGNORAR)
# 6: Canal de Transmissão
# 7: Url
TUPLE_INDEX_TO_FIELD: Dict[int, str] = {
    0: "Campeonato",
    1: "Partida",
    2: "Data",
    3: "Horário",
    6: "Canal de Transmissão",
    7: "Url",
}

# Cache em memória e IDs padrão para o Microsoft Graph
DEFAULT_SITE_ID = "adgbl.sharepoint.com,a3e49747-9bb6-4c93-9930-dda26c8d1050,34c8fe55-2cfe-4efc-8ce0-2958fd775ee0"
DEFAULT_LIST_ID = "f7e25960-cf15-4ed8-b88c-bf607dc90a0f"

_GRAPH_TOKEN_CACHE: Dict[str, Any] = {"token": None, "expires_at": 0}
_GRAPH_IDS_CACHE: Dict[str, str] = {"site_id": DEFAULT_SITE_ID, "list_id": DEFAULT_LIST_ID}


def _normalizar_texto(txt: str) -> str:
    """Remove acentos, pontuação e espaços extras para comparações seguras."""
    if not txt:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(txt))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r"[^a-zA-Z0-9]", "", sem_acento).lower()


def _normalizar_campeonato(camp: str) -> str:
    """Normaliza o nome do campeonato removendo prefixos como 'CBF - ' para unificar chaves."""
    if not camp:
        return ""
    c = str(camp).strip()
    c = re.sub(r"^cbf\s*[-–—:]*\s*", "", c, flags=re.IGNORECASE)
    return _normalizar_texto(c)


def _deep_normalize_partida(match_name: str) -> tuple:
    """Normaliza nome da partida para tupla ordenada de times canônicos (ex: ('botafogo', 'vasco'))."""
    if not match_name:
        return ("",)
    
    def norm_team(t):
        if not t:
            return ""
        t = str(t).lower()
        nfkd = unicodedata.normalize("NFKD", t)
        t = "".join([c for c in nfkd if not unicodedata.combining(c)])
        t = t.replace("-", " ").replace(".", "").replace("_", " ")

        # 1. Limpeza de prefixos/sufixos e siglas institucionais
        prefixes = [
            r"\besporte clube\b", r"\be\s*c\b", r"\bf\s*c\b", r"\bfutebol clube\b",
            r"\bfc\b", r"\bec\b", r"\bs\s*a\s*f\b", r"\bsaf\b", r"\bclube de regatas\b",
            r"\bsociedade esportiva\b", r"\bassociacao atletica\b",
            r"\bgremio recreativo\b", r"\bgremio esportivo\b",
            r"\bsport club\b", r"\bclube atletico\b", r"\bassociacao\b",
            r"\bsc\b", r"\bse\b", r"\bc\s*r\b", r"\bcr\b", r"\bfr\b", r"\baf\b", r"\bca\b", r"\baa\b"
        ]
        for p in prefixes:
            t = re.sub(p, " ", t)
        t = re.sub(r"\s+", " ", t).strip()

        # Limpeza prévia de siglas de estado no final para clubes de cidade única
        state_strip_exceptions = ["atletico", "athletico", "america", "botafogo", "operario"]
        if not any(exc in t for exc in state_strip_exceptions):
            t = re.sub(r"\s+(mg|sp|rj|rs|pr|sc|ba|go|mt|ce|pe|al|rn|pb|am|pa|se|df|es|ma|pi|to|ro|ac|ap|rr)$", "", t).strip()

        # 2. Mapeamento canônico exato de apelidos e variações dos clubes
        replacements = [
            # Vasco
            (r"\b(vasco da gama|cr vasco da gama|c r vasco da gama|vasco|vascao)\b", "vasco"),
            # Athletico-PR
            (r"\b(athletico paranaense|atletico paranaense|athletico pr|atletico pr|cap|athletico|furacao)\b", "athletico pr"),
            # Atlético-GO
            (r"\b(atletico goianiense|atletico go|acg|dragao)\b", "atletico go"),
            # Atlético-MG (qualquer 'atletico' isolado no Brasileirão/Copa do Brasil mapeia para atletico mg)
            (r"\b(atletico mineiro|atletico mg|cam|galo|atletico)\b", "atletico mg"),
            # Bragantino
            (r"\b(red bull bragantino|rb bragantino|bragantino sp|bragantino|massa bruta)\b", "bragantino"),
            # Corinthians
            (r"\b(corinthians paulista|corinthians sp|corinthians|sccp|timao)\b", "corinthians"),
            # São Paulo
            (r"\b(sao paulo fc|sao paulo sp|sao paulo|spfc|tricolor paulista)\b", "sao paulo"),
            # Palmeiras
            (r"\b(se palmeiras|palmeiras sp|palmeiras|verdao|alviverde)\b", "palmeiras"),
            # Flamengo
            (r"\b(flamengo rj|cr flamengo|flamengo|mengao|fla|mengo)\b", "flamengo"),
            # Fluminense
            (r"\b(fluminense rj|fluminense fc|fluminense|flu|tricolor carioca|tricolor das laranjeiras)\b", "fluminense"),
            # Santos
            (r"\b(santos fc|santos sp|santos|peixe)\b", "santos"),
            # Botafogo-SP vs Botafogo-RJ
            (r"\b(botafogo de ribeirao preto|botafogo sp)\b", "botafogo sp"),
            (r"\b(botafogo pb|botafogo da paraiba)\b", "botafogo pb"),
            (r"\b(botafogo fr|botafogo rj|botafogo|fogao|bota)\b", "botafogo"),
            # Novorizontino (antes de Grêmio)
            (r"\b(gremio novorizontino|novorizontino sp|novorizontino|tigre do vale)\b", "novorizontino"),
            # Grêmio
            (r"\b(gremio fbpa|gremio porto alegrense|gremio rsg|gremio rs|gremio)\b", "gremio"),
            # Inter de Limeira vs Internacional
            (r"\b(internacional de limeira|inter de limeira|inter limeira)\b", "inter limeira"),
            (r"\b(internacional rs|inter de porto alegre|inter rs|internacional|inter|colorado)\b", "internacional"),
            # Cruzeiro
            (r"\b(cruzeiro ec|cruzeiro mg|cruzeiro|raposa)\b", "cruzeiro"),
            # Juventude
            (r"\b(juventude rs|juventude|papo)\b", "juventude"),
            # Fortaleza
            (r"\b(fortaleza ec|fortaleza ce|fortaleza|leao do pici)\b", "fortaleza"),
            # Ceará
            (r"\b(ceara sc|ceara ce|ceara|vozao|vovo)\b", "ceara"),
            # Bahia
            (r"\b(bahia ba|ec bahia|bahia|esquadrao|tricolor de aco)\b", "bahia"),
            # Vitória
            (r"\b(vitoria ba|ec vitoria|vitoria|leao da barra)\b", "vitoria"),
            # Cuiabá
            (r"\b(cuiaba ec|cuiaba mt|cuiaba|dourado)\b", "cuiaba"),
            # Criciúma
            (r"\b(criciuma ec|criciuma sc|criciuma|tigre)\b", "criciuma"),
            # Coritiba
            (r"\b(coritiba fcf|coritiba pr|coritiba|coxa)\b", "coritiba"),
            # Goiás
            (r"\b(goias ec|goias go|goias|esmeraldino)\b", "goias"),
            # Sport
            (r"\b(sport club do recife|sport recife|sport pe|sport|leao da ilha)\b", "sport"),
            # América-MG vs América-RN
            (r"\b(america de natal|america rn)\b", "america rn"),
            (r"\b(america mineiro|america mg|coelho|america)\b", "america mg"),
            # Chapecoense
            (r"\b(chapecoense af|chapecoense sc|chapecoense|chape)\b", "chapecoense"),
            # Mirassol
            (r"\b(mirassol fc|mirassol sp|mirassol|leaozinho)\b", "mirassol"),
            # Operário-PR
            (r"\b(operario ferroviario|operario pr|operario|fantasma)\b", "operario pr"),
            # Vila Nova
            (r"\b(vila nova fc|vila nova go|vila nova|tigrao)\b", "vila nova"),
            # Ponte Preta
            (r"\b(ponte preta sp|a a ponte preta|ponte preta|macaca)\b", "ponte preta"),
            # Guarani
            (r"\b(guarani fc|guarani sp|guarani|bugre)\b", "guarani"),
            # Amazonas
            (r"\b(amazonas fc|amazonas am|amazonas|onca)\b", "amazonas"),
            # Brusque
            (r"\b(brusque fc|brusque sc|brusque|quadricolor)\b", "brusque"),
            # Ituano
            (r"\b(ituano fc|ituano sp|ituano|galo de itu)\b", "ituano"),
            # Paysandu
            (r"\b(paysandu sc|paysandu pa|paysandu|papao)\b", "paysandu"),
            # Remo
            (r"\b(clube do remo|remo pa|remo|leao azul)\b", "remo"),
            # Avaí
            (r"\b(avai fc|avai sc|avai|leao da ilha)\b", "avai"),
            # CRB / CSA
            (r"\b(clube de regatas brasil|crb al|crb|galo da praia)\b", "crb"),
            (r"\b(centro sportivo alagoano|csa al|csa|azulino)\b", "csa"),
            (r"\b(athletic club|athletic mg|athletic)\b", "athletic"),
            (r"\b(ferroviaria sp|ferroviaria|locomotiva)\b", "ferroviaria"),
            (r"\b(volta redonda rj|volta redonda|voltaco)\b", "volta redonda"),
            (r"\b(nautico pe|nautico|timbu)\b", "nautico"),
            (r"\b(figueirense fc|figueirense sc|figueirense|figueira)\b", "figueirense"),
            (r"\b(sampaio correa|sampaio correa ma|bolivia querida)\b", "sampaio correa"),
            (r"\b(confianca se|confianca|dragao do bairro industrial)\b", "confianca"),
            (r"\b(abc fc|abc rn|abc)\b", "abc"),
            (r"\b(londrina ec|londrina pr|londrina|tubarao)\b", "londrina"),
        ]

        for pattern, rep in replacements:
            if re.search(pattern, t):
                t = re.sub(pattern, rep, t)
                break

        return re.sub(r"\s+", " ", t).strip()

    text_work = re.sub(r"\s+[vVxX]\s+", " x ", str(match_name))
    parts = text_work.lower().split(" x ")
    if len(parts) >= 2:
        t1, t2 = norm_team(parts[0]), norm_team(parts[1])
        return tuple(sorted([t1, t2]))
    return (norm_team(match_name),)


def _is_match_duplicate(p_tuple: tuple, d_short: str, existing_match_dates: set) -> bool:
    """Verifica se o confronto já existe na mesma data ou com tolerância de +/- 1 dia."""
    if not p_tuple or p_tuple == ("",) or not d_short:
        return False
    if (p_tuple, d_short) in existing_match_dates:
        return True
    try:
        dt = datetime.strptime(d_short[:10], "%Y-%m-%d")
        d_minus = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        d_plus = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        if (p_tuple, d_minus) in existing_match_dates or (p_tuple, d_plus) in existing_match_dates:
            return True
    except Exception:
        pass
    return False


def _gerar_chave_evento(camp: str, part: str, data_iso: str, hora: str) -> str:
    """Gera chave composta única para o evento (evita duplicação no SharePoint)."""
    c_clean = _normalizar_campeonato(camp)
    p_tuple = _deep_normalize_partida(part)
    p_clean = "x".join([re.sub(r"[^a-zA-Z0-9]", "", t) for t in p_tuple if t])
    if not p_clean:
        p_clean = _normalizar_texto(part)
    d_clean = re.sub(r"[^0-9]", "", data_iso[:10]) if data_iso else ""
    h_clean = re.sub(r"[^0-9]", "", str(hora)) if hora else ""
    return f"{c_clean}_{p_clean}_{d_clean}_{h_clean}"


def _mapear_canal(canal_raw: Any) -> List[str]:
    """Mapeia o canal do scraper para as opções exatas da coluna Choice do SharePoint."""
    if not canal_raw:
        return ["Nenhuma"]
    if isinstance(canal_raw, list):
        return [str(c) for c in canal_raw if str(c).strip()]

    ch = str(canal_raw).strip()
    mapping = {
        "amazon": "Amazon Prime",
        "prime": "Amazon Prime",
        "amazon prime": "Amazon Prime",
        "disney": "Disney Plus",
        "disney+": "Disney Plus",
        "disney plus": "Disney Plus",
        "max": "Max",
        "hbo max": "Max",
        "hbo": "Max",
        "dazn": "dazn",
        "caze": "Cazé TV",
        "cazé": "Cazé TV",
        "cazé tv": "Cazé TV",
        "caze tv": "Cazé TV",
        "cazé tv membros": "Cazé TV Membros",
        "cazé tv ppv": "Cazé TV PPV",
        "tnt": "TNT_SPORTS",
        "tnt sports": "TNT_SPORTS",
        "tnt_sports": "TNT_SPORTS",
        "tnt paytv": "TNT PAYTV",
        "goat": "CANAL GOAT",
        "canal goat": "CANAL GOAT",
        "globo": "Rede Globo",
        "rede globo": "Rede Globo",
        "sportv": "Sport TV",
        "sport tv": "Sport TV",
        "record": "Record",
        "desimpedidos": "Desimpedidos",
        "ge tv": "GE TV",
        "netflix": "Netflix",
        "onefootball": "OneFootball",
        "fifa +": "Fifa +",
    }
    val = mapping.get(ch.lower(), ch)
    return [val]


def _obter_config_sharepoint() -> Dict[str, str]:
    """Recupera credenciais do SharePoint do .env.enc ou .env."""
    try:
        from crypto_utils import get_env_value
        user = get_env_value("SP_USERNAME")
        pwd = get_env_value("SP_PASSWORD")
        tenant = get_env_value("SP_TENANT_ID")
        client_id = get_env_value("SP_CLIENT_ID")
        site_url = get_env_value("SP_SITE_URL")
        list_title = get_env_value("SP_LIST_TITLE")
    except Exception:
        user = pwd = tenant = client_id = site_url = list_title = None

    user = user or os.getenv("SP_USERNAME", "svc.captacao@adgbl.com")
    pwd = pwd or os.getenv("SP_PASSWORD", "Acount@!2026")
    tenant = tenant or os.getenv("SP_TENANT_ID", "b2767241-fab5-454b-8b62-f6324650e316")
    client_id = client_id or os.getenv("SP_CLIENT_ID", "1950a258-227b-4e31-a9cf-717495945fc2")
    site_url = site_url or os.getenv("SP_SITE_URL", "https://adgbl.sharepoint.com/sites/suportecaptacao")
    list_title = list_title or os.getenv("SP_LIST_TITLE", "Programação de eventos - Streaming")

    return {
        "username": user,
        "password": pwd,
        "tenant_id": tenant,
        "client_id": client_id,
        "site_url": site_url,
        "list_title": list_title,
    }


def _graph_request(method: str, url: str, headers: Dict[str, str], json_payload: Any = None, max_retries: int = 5, timeout: int = 30) -> requests.Response:
    """
    Executa chamada HTTP à Graph API com tratamento inteligente de 429 (Rate Limit / Throttling)
    e 503/504 com exponential backoff respeitando o header Retry-After.
    """
    attempt = 0
    resp = None
    while attempt < max_retries:
        attempt += 1
        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                resp = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
            elif method.upper() == "PATCH":
                resp = requests.patch(url, headers=headers, json=json_payload, timeout=timeout)
            else:
                resp = requests.request(method, url, headers=headers, json=json_payload, timeout=timeout)

            if resp.status_code == 429 or resp.status_code in (503, 504):
                retry_after = resp.headers.get("Retry-After")
                wait_time = int(retry_after) if (retry_after and retry_after.isdigit()) else min(2 ** attempt + 1, 30)
                logger.warning(f"[Graph API] Status {resp.status_code} (Throttling/Busy). Aguardando {wait_time}s antes de tentar novamente (tentativa {attempt}/{max_retries})...")
                time.sleep(wait_time)
                continue

            return resp
        except (requests.ConnectionError, requests.Timeout) as e:
            wait_time = min(2 ** attempt + 1, 30)
            logger.warning(f"[Graph API] Erro de conexão/timeout ({e}). Tentativa {attempt}/{max_retries}. Aguardando {wait_time}s...")
            time.sleep(wait_time)
            if attempt >= max_retries:
                raise
    return resp


def _obter_token_graph() -> str:
    """Obtém token de acesso ao Microsoft Graph com cache em memória."""
    global _GRAPH_TOKEN_CACHE
    agora = time.time()

    if _GRAPH_TOKEN_CACHE["token"] and agora < (_GRAPH_TOKEN_CACHE["expires_at"] - 60):
        return _GRAPH_TOKEN_CACHE["token"]

    cfg = _obter_config_sharepoint()
    token_url = f"https://login.microsoftonline.com/{cfg['tenant_id']}/oauth2/v2.0/token"
    payload = {
        "client_id": cfg["client_id"],
        "username": cfg["username"],
        "password": cfg["password"],
        "grant_type": "password",
        "scope": "https://graph.microsoft.com/.default",
    }

    resp = requests.post(token_url, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    expires_in = int(data.get("expires_in", 3599))

    _GRAPH_TOKEN_CACHE["token"] = token
    _GRAPH_TOKEN_CACHE["expires_at"] = agora + expires_in
    logger.info("[SharePoint Direct] Token Microsoft Graph obtido com sucesso.")
    return token


def _obter_site_e_lista_ids(headers: Dict[str, str]) -> Tuple[str, str]:
    """Descobre e armazena em cache o site_id e list_id da lista de eventos."""
    global _GRAPH_IDS_CACHE
    if _GRAPH_IDS_CACHE.get("site_id") and _GRAPH_IDS_CACHE.get("list_id"):
        return _GRAPH_IDS_CACHE["site_id"], _GRAPH_IDS_CACHE["list_id"]

    cfg = _obter_config_sharepoint()
    url_clean = cfg["site_url"].replace("https://", "").replace("http://", "").rstrip("/")
    partes = url_clean.split("/", 1)
    domain = partes[0]
    site_path = f"/{partes[1]}" if len(partes) > 1 else ""

    try:
        r_site = _graph_request("GET", f"https://graph.microsoft.com/v1.0/sites/{domain}:{site_path}", headers=headers, timeout=30)
        r_site.raise_for_status()
        site_id = r_site.json()["id"]

        r_lists = _graph_request("GET", f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers, timeout=30)
        r_lists.raise_for_status()
        list_id = None
        for l in r_lists.json().get("value", []):
            disp = l.get("displayName", "")
            name = l.get("name", "")
            if ("evento" in disp.lower() and "streaming" in disp.lower()) or name == "Programao de eventos  Streaming" or l.get("id") == DEFAULT_LIST_ID:
                list_id = l.get("id")
                break

        if not list_id:
            list_id = DEFAULT_LIST_ID

        _GRAPH_IDS_CACHE["site_id"] = site_id
        _GRAPH_IDS_CACHE["list_id"] = list_id
        logger.info(f"[SharePoint Direct] Conectado ao Site ID: {site_id} | List ID: {list_id}")
        return site_id, list_id
    except Exception as e:
        logger.warning(f"[SharePoint Direct] Falha ao resolver IDs dinamicamente: {e}. Usando IDs padrão.")
        _GRAPH_IDS_CACHE["site_id"] = DEFAULT_SITE_ID
        _GRAPH_IDS_CACHE["list_id"] = DEFAULT_LIST_ID
        return DEFAULT_SITE_ID, DEFAULT_LIST_ID


def _carregar_eventos_existentes(headers: Dict[str, str], site_id: str, list_id: str) -> Tuple[set, set, set]:
    """Carrega os eventos existentes no SharePoint para desduplicação imediata."""
    existing_chaves = set()
    existing_tuples = set()
    existing_match_dates = set()

    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields&$top=100"
    page_count = 0
    max_pages = 10  # Indexa até 1000 itens recentes

    logger.info("[SharePoint Direct] Consultando eventos existentes no SharePoint para desduplicação...")
    while url and page_count < max_pages:
        page_count += 1
        try:
            resp = _graph_request("GET", url, headers=headers, timeout=25)
            if not resp or resp.status_code != 200:
                logger.warning(f"[SharePoint Direct] Erro ao buscar itens página {page_count}: {resp.status_code if resp else 'No response'}")
                break

            data = resp.json()
            items = data.get("value", [])
            for item in items:
                f = item.get("fields", {})
                ch = f.get("ChaveEvento")
                if ch:
                    existing_chaves.add(str(ch).strip())

                c_val = _normalizar_campeonato(f.get("Title"))
                p_raw = f.get("Partida", "")
                p_val = _normalizar_texto(p_raw)
                p_tuple = _deep_normalize_partida(p_raw)
                d_raw = str(f.get("Data", ""))[:10]
                h_val = str(f.get("Hor_x00e1_rio", "")).strip()

                if c_val and p_val and d_raw:
                    existing_tuples.add((c_val, p_val, d_raw, h_val))
                if p_tuple != ("",) and d_raw:
                    existing_match_dates.add((p_tuple, d_raw))

            url = data.get("@odata.nextLink")
        except Exception as e:
            logger.warning(f"[SharePoint Direct] Erro ao carregar página {page_count} de eventos: {e}")
            break

    logger.info(f"[SharePoint Direct] Indexados: {len(existing_chaves)} chaves, {len(existing_match_dates)} confrontos existentes.")
    return existing_chaves, existing_tuples, existing_match_dates


def _post_to_sharepoint_direct(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Envia eventos diretamente para a lista do SharePoint via Microsoft Graph API.
    Realiza verificação rigorosa de duplicidade por ChaveEvento, Jogo+Data (+/- 1 dia) antes de inserir.
    """
    token = _obter_token_graph()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    site_id, list_id = _obter_site_e_lista_ids(headers)

    existing_chaves, existing_tuples, existing_match_dates = _carregar_eventos_existentes(headers, site_id, list_id)

    inserted_count = 0
    skipped_count = 0
    errors = []

    logger.info(f"[SharePoint Direct] Processando {len(events)} evento(s) para inserção direta...")

    for ev in events:
        try:
            camp = str(ev.get("Campeonato", "")).strip()
            part = str(ev.get("Partida", "")).strip()
            dt_raw = str(ev.get("Data", "")).strip()
            hora = str(ev.get("Horário", "")).strip()
            mes = str(ev.get("Mês", "")).strip()
            canal_raw = ev.get("Canal de Transmissão", "")

            if not camp or not part or not dt_raw:
                continue

            # Data ISO para coluna dateOnly no SharePoint:
            data_iso = f"{dt_raw[:10]}T12:00:00Z" if not "T" in dt_raw else (f"{dt_raw[:10]}T12:00:00Z" if "T00:00:00" in dt_raw else dt_raw)
            d_short = dt_raw[:10]

            # Chave e Normalização Canônica
            chave = _gerar_chave_evento(camp, part, data_iso, hora)
            p_tuple = _deep_normalize_partida(part)
            tuple_check = (_normalizar_campeonato(camp), _normalizar_texto(part), d_short, hora)

            # Verificação de duplicidade:
            # 1. Chave exata
            # 2. Tupla exata
            # 3. Confronto idêntico na mesma data ou +/- 1 dia (independente de hora ou prefixo de campeonato)
            is_dup = (
                chave in existing_chaves or
                tuple_check in existing_tuples or
                _is_match_duplicate(p_tuple, d_short, existing_match_dates)
            )

            if is_dup:
                logger.info(f"[SharePoint Direct] Jogo '{part}' ({d_short}) já existe no SharePoint (duplicata evitada). Ignorado.")
                skipped_count += 1
                continue

            # Monta payload do item
            item_payload = {
                "fields": {
                    "Title": camp,
                    "Partida": part,
                    "Data": data_iso,
                    "M_x00ea_s": mes or "Janeiro",
                    "Hor_x00e1_rio": hora,
                    "Transmiss_x00e3_o@odata.type": "Collection(Edm.String)",
                    "Transmiss_x00e3_o": _mapear_canal(canal_raw),
                    "ChaveEvento": chave
                }
            }

            r_ins = _graph_request(
                "POST",
                f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items",
                headers=headers,
                json_payload=item_payload,
                timeout=30
            )

            if r_ins and r_ins.status_code in (200, 201):
                inserted_count += 1
                existing_chaves.add(chave)
                existing_tuples.add(tuple_check)
                if p_tuple != ("",):
                    existing_match_dates.add((p_tuple, d_short))
            elif r_ins and r_ins.status_code == 400 and ("unique" in r_ins.text.lower() or "already has the provided value" in r_ins.text.lower()):
                # O SharePoint rejeitou com restrição de unicidade (item já existe no banco)
                skipped_count += 1
                existing_chaves.add(chave)
                existing_tuples.add(tuple_check)
                if p_tuple != ("",):
                    existing_match_dates.add((p_tuple, d_short))
                logger.info(f"[SharePoint Direct] Evento '{part}' já existia na lista (restrição de unicidade). Ignorado com sucesso.")
            else:
                err_code = r_ins.status_code if r_ins else "No Response"
                err_text = r_ins.text if r_ins else ""
                err_msg = f"Erro {err_code} ao inserir '{part}': {err_text}"
                logger.error(f"[SharePoint Direct] {err_msg}")
                errors.append(err_msg)

        except Exception as e:
            err_msg = f"Exceção ao inserir evento: {e}"
            logger.error(f"[SharePoint Direct] {err_msg}", exc_info=True)
            errors.append(err_msg)

    logger.info(
        f"[SharePoint Direct] Finalizado. Total: {len(events)} | Inseridos: {inserted_count} | Ignorados (já existiam): {skipped_count} | Erros: {len(errors)}"
    )

    return {
        "total": len(events),
        "inserted": inserted_count,
        "skipped_existing": skipped_count,
        "errors": errors,
        "source": "direct_graph_api"
    }


def _tuple_to_item(row: Tuple[Any, ...]) -> Dict[str, Any]:
    if row is None:
        return None
    if len(row) < 8:
        raise ValueError(
            f"Tuple com tamanho inesperado. Esperado >= 8, recebido {len(row)}"
        )

    item: Dict[str, Any] = {}

    # --- Campeonato e Partida (Obrigatórios) ---
    camp = str(row[0]).strip()
    part = str(row[1]).strip()
    
    if not camp or camp.lower() == "null":
        logger.warning("[SharePoint] Campeonato ausente ou 'Null'. Ignorando item.")
        return None
    if not part or part.lower() == "null":
        logger.warning("[SharePoint] Partida ausente ou 'Null'. Ignorando item.")
        return None
        
    item["Campeonato"] = camp
    item["Partida"] = part

    # --- Data (Obrigatório) ---
    data_str = row[2]
    if not (isinstance(data_str, str) and data_str.strip()) or data_str.lower() == "null":
        logger.warning("[SharePoint] Data ausente ou 'Null'. Ignorando item.")
        return None
        
    try:
        dt = datetime.strptime(data_str.strip(), "%d/%m/%Y")
        item["Data"] = dt.strftime("%Y-%m-%d")
        item["Mês"] = MONTH_NAMES_PT[dt.month - 1]
    except Exception as e:
        logger.warning(f"[SharePoint] Data inválida: {data_str!r} ({e}). Ignorando item.")
        return None

    # --- Horário ---
    hora_str = row[3]
    if isinstance(hora_str, str) and hora_str.strip():
        item["Horário"] = hora_str.strip()

    item["Canal de Transmissão"] = row[6]
    item["Url"] = row[7]

    return item


def _post_to_flow(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback: envia os eventos para o fluxo legado do Power Automate."""
    from dotenv import load_dotenv

    load_dotenv(override=False)

    flow_url = os.getenv(
        "PA_FLOW_URL",
        "https://81ec9e132aa1ee3096ed175f87f0ab.44.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/b99a060310be45278e30db42477a44a8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=uMR8-Xb5Q4mcqJS_x_xf3laOqSsvcK4vqLlMlyPRxKY"
    )

    clean_events = []
    for ev in events:
        clean = {k: v for k, v in ev.items() if v not in ("", None)}
        if clean:
            clean_events.append(clean)

    if not clean_events:
        logger.warning("[Flow Fallback] Nenhum evento válido após limpeza")
        return {
            "total": 0,
            "inserted": 0,
            "skipped_existing": 0,
            "errors": ["Eventos vazios após limpeza"],
            "source": "power_automate_fallback"
        }

    payload = {"events": clean_events}

    logger.info(f"[Flow Fallback] Enviando {len(clean_events)} evento(s) para o Power Automate...")

    resp = requests.post(flow_url, json=payload, timeout=120)

    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[Flow Fallback] Erro HTTP ao chamar o Flow ({resp.status_code}): {e}", exc_info=True)
        return {
            "total": len(clean_events),
            "inserted": 0,
            "skipped_existing": 0,
            "errors": [str(e)],
            "status_code": resp.status_code,
            "raw_text": resp.text,
            "source": "power_automate_fallback"
        }

    try:
        data = resp.json()
        if isinstance(data, dict) and "total" in data:
            data["source"] = "power_automate_fallback"
            return data
    except ValueError:
        pass

    return {
        "total": len(clean_events),
        "inserted": len(clean_events),
        "skipped_existing": 0,
        "errors": [],
        "status_code": resp.status_code,
        "source": "power_automate_fallback"
    }


# ---------- Funções públicas para uso no Streaming_Scheduler ----------

def push_events_to_sharepoint(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tenta o envio direto via Microsoft Graph API (mais rápido e com desduplicação imediata).
    Caso ocorra falha total de comunicação, aciona o Power Automate como Fallback.
    """
    if not items:
        logger.info("[SharePoint] Nenhum item recebido para envio.")
        return {"total": 0, "inserted": 0, "skipped_existing": 0, "errors": []}

    # Validação de segurança adicional: bloquear jogos do Brasileirão/Copa do Brasil sem direitos oficiais
    try:
        from Streaming_Scheduler import is_cbf_broadcast_authorized
        items_validos = []
        for it in items:
            c = it.get("Campeonato", "")
            p = it.get("Partida", "")
            ch = it.get("Canal de Transmissão", "")
            if is_cbf_broadcast_authorized(c, p, ch):
                items_validos.append(it)
            else:
                logger.warning(f"[SharePoint Bloqueio] Evento '{p}' ({c}) [{ch}] rejeitado por não possuir direitos oficiais na CBF.")
        items = items_validos
    except Exception as e:
        logger.debug(f"[SharePoint] Verificação CBF rights ignorada: {e}")

    if not items:
        logger.info("[SharePoint] Nenhum item válido após filtragem de direitos CBF.")
        return {"total": 0, "inserted": 0, "skipped_existing": 0, "errors": []}

    # 1. Tentativa Principal: Comunicação Direta via Graph API
    try:
        logger.info("[SharePoint] Iniciando envio direto via Microsoft Graph API...")
        res = _post_to_sharepoint_direct(items)
        
        # Se a chamada ao Graph API processou os itens (mesmo que alguns tenham sido inseridos e outros pulados por duplicidade)
        # nós NÃO devemos acionar o fallback para não duplicar no Power Automate.
        if res and (res.get("inserted", 0) > 0 or res.get("skipped_existing", 0) > 0 or not res.get("errors")):
            return res
        elif res and res.get("errors"):
            logger.warning(f"[SharePoint] Gravação direta falhou com erros: {res.get('errors')}. Acionando Fallback Power Automate...")
    except Exception as e:
        logger.warning(
            f"[SharePoint] Falha na comunicação direta via Graph API ({e}). Acionando Fallback Power Automate...",
            exc_info=True
        )

    # 2. Fallback de Segurança: Power Automate
    logger.info("[SharePoint] Executando envio via Power Automate (Fallback)...")
    return _post_to_flow(items)


def push_event_from_tuple(row: Tuple[Any, ...]) -> Dict[str, Any]:
    """Recebe UMA linha do Treeview (tuple) e envia para o SharePoint."""
    item = _tuple_to_item(row)
    if not item:
        return {"total": 0, "inserted": 0, "skipped_existing": 0, "errors": ["Item inválido ou sem data"]}
    return push_events_to_sharepoint([item])


def push_events_from_tuples(rows: List[Tuple[Any, ...]]) -> Dict[str, Any]:
    """Recebe várias tuples (linhas do Treeview) e envia todas de uma vez para o SharePoint."""
    items = []
    for r in rows:
        if r:
            it = _tuple_to_item(r)
            if it:
                items.append(it)
            
    return push_events_to_sharepoint(items)
