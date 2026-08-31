# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import re
import time
import logging
import unicodedata
from datetime import datetime
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

# Cache em memória para o Microsoft Graph
_GRAPH_TOKEN_CACHE: Dict[str, Any] = {"token": None, "expires_at": 0}
_GRAPH_IDS_CACHE: Dict[str, str] = {"site_id": None, "list_id": None}


def _normalizar_texto(txt: str) -> str:
    """Remove acentos, pontuação e espaços extras para comparações seguras."""
    if not txt:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(txt))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r"[^a-zA-Z0-9]", "", sem_acento).lower()


def _gerar_chave_evento(camp: str, part: str, data_iso: str, hora: str) -> str:
    """Gera chave composta única para o evento (evita duplicação no SharePoint)."""
    c_clean = _normalizar_texto(camp)
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

    # Fallback para variáveis de ambiente locais se não encontradas
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
    if _GRAPH_IDS_CACHE["site_id"] and _GRAPH_IDS_CACHE["list_id"]:
        return _GRAPH_IDS_CACHE["site_id"], _GRAPH_IDS_CACHE["list_id"]

    cfg = _obter_config_sharepoint()
    # Extrai domínio e caminho relativo do site_url
    url_clean = cfg["site_url"].replace("https://", "").replace("http://", "").rstrip("/")
    partes = url_clean.split("/", 1)
    domain = partes[0]
    site_path = f"/{partes[1]}" if len(partes) > 1 else ""

    # 1. Obter Site ID
    r_site = requests.get(f"https://graph.microsoft.com/v1.0/sites/{domain}:{site_path}", headers=headers, timeout=30)
    r_site.raise_for_status()
    site_id = r_site.json()["id"]

    # 2. Obter List ID
    r_lists = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers, timeout=30)
    r_lists.raise_for_status()
    list_id = None
    for l in r_lists.json().get("value", []):
        disp = l.get("displayName", "")
        name = l.get("name", "")
        if ("evento" in disp.lower() and "streaming" in disp.lower()) or name == "Programao de eventos  Streaming" or l.get("id") == "f7e25960-cf15-4ed8-b88c-bf607dc90a0f":
            list_id = l.get("id")
            break

    if not list_id:
        raise ValueError(f"Lista de eventos '{cfg['list_title']}' não encontrada no site SharePoint.")

    _GRAPH_IDS_CACHE["site_id"] = site_id
    _GRAPH_IDS_CACHE["list_id"] = list_id
    logger.info(f"[SharePoint Direct] Conectado ao Site ID: {site_id} | List ID: {list_id}")
    return site_id, list_id


def _post_to_sharepoint_direct(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Envia eventos diretamente para a lista do SharePoint via Microsoft Graph API.
    Realiza verificação de duplicidade por ChaveEvento antes de inserir.
    """
    token = _obter_token_graph()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    site_id, list_id = _obter_site_e_lista_ids(headers)

    # 1. Carrega eventos existentes no SharePoint para desduplicação (por período de datas dos eventos)
    existing_chaves = set()
    existing_tuples = set()
    try:
        datas = [str(ev.get("Data", ""))[:10] for ev in events if ev.get("Data")]
        if datas:
            min_date = min(datas)
            max_date = max(datas)
            filter_str = f"fields/Data ge '{min_date}T00:00:00Z' and fields/Data le '{max_date}T23:59:59Z'"
            url_query = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields&$filter={filter_str}&$top=999"
        else:
            url_query = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields&$top=500"

        logger.info("[SharePoint Direct] Consultando eventos existentes para desduplicação...")
        r_recent = requests.get(url_query, headers=headers, timeout=30)
        if r_recent.status_code == 200:
            for item in r_recent.json().get("value", []):
                f = item.get("fields", {})
                ch = f.get("ChaveEvento")
                if ch:
                    existing_chaves.add(str(ch).strip())
                c_val = _normalizar_texto(f.get("Title"))
                p_val = _normalizar_texto(f.get("Partida"))
                d_val = str(f.get("Data", ""))[:10]
                h_val = str(f.get("Hor_x00e1_rio", "")).strip()
                if c_val and p_val and d_val:
                    existing_tuples.add((c_val, p_val, d_val, h_val))
    except Exception as e:
        logger.warning("[SharePoint Direct] Não foi possível pré-carregar lista existente: %s. A validação de unicidade do SharePoint garantirá a desduplicação.", e)

    inserted_count = 0
    skipped_count = 0
    errors = []

    logger.info("[SharePoint Direct] Processando %d evento(s) para inserção direta...", len(events))

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

            # Data ISO
            data_iso = dt_raw if "T" in dt_raw else f"{dt_raw}T00:00:00Z"
            d_short = dt_raw[:10]

            # Chave do evento
            chave = _gerar_chave_evento(camp, part, data_iso, hora)

            # Verifica se já existe na memória
            tuple_check = (_normalizar_texto(camp), _normalizar_texto(part), d_short, hora)
            if chave in existing_chaves or tuple_check in existing_tuples:
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

            r_ins = requests.post(
                f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items",
                headers=headers,
                json=item_payload,
                timeout=30
            )

            if r_ins.status_code in (200, 201):
                inserted_count += 1
                existing_chaves.add(chave)
                existing_tuples.add(tuple_check)
            elif r_ins.status_code == 400 and ("unique" in r_ins.text.lower() or "already has the provided value" in r_ins.text.lower()):
                # O SharePoint rejeitou com restrição de unicidade (item já existe no banco)
                skipped_count += 1
                existing_chaves.add(chave)
                existing_tuples.add(tuple_check)
                logger.info("[SharePoint Direct] Evento '%s' já existia na lista. Ignorado com sucesso.", part)
            else:
                err_msg = f"Erro {r_ins.status_code} ao inserir '{part}': {r_ins.text}"
                logger.error("[SharePoint Direct] %s", err_msg)
                errors.append(err_msg)

        except Exception as e:
            err_msg = f"Exceção ao inserir evento: {e}"
            logger.error("[SharePoint Direct] %s", err_msg, exc_info=True)
            errors.append(err_msg)


    logger.info(
        "[SharePoint Direct] Finalizado. Total: %d | Inseridos: %d | Ignorados (já existiam): %d | Erros: %d",
        len(events), inserted_count, skipped_count, len(errors)
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
        logger.warning("[SharePoint] Data inválida: %r (%s). Ignorando item.", data_str, e)
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
    import json

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

    logger.info("[Flow Fallback] Enviando %d evento(s) para o Power Automate...", len(clean_events))

    resp = requests.post(flow_url, json=payload, timeout=120)

    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error("[Flow Fallback] Erro HTTP ao chamar o Flow (%s): %s", resp.status_code, e, exc_info=True)
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
        "inserted": None,
        "skipped_existing": None,
        "errors": [],
        "status_code": resp.status_code,
        "source": "power_automate_fallback"
    }


# ---------- Funções públicas para uso no Streaming_Scheduler ----------

def push_events_to_sharepoint(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tenta o envio direto via Microsoft Graph API (mais rápido e com desduplicação imediata).
    Caso ocorra qualquer erro ou exceção, aciona automaticamente o Power Automate como Fallback.
    """
    if not items:
        logger.info("[SharePoint] Nenhum item recebido para envio.")
        return {"total": 0, "inserted": 0, "skipped_existing": 0, "errors": []}

    # 1. Tentativa Principal: Comunicação Direta via Graph API
    try:
        logger.info("[SharePoint] Iniciando envio direto via Microsoft Graph API...")
        res = _post_to_sharepoint_direct(items)
        # Se não houve erros fatais, retorna o resultado direto
        if res and not (res.get("inserted") == 0 and res.get("skipped_existing") == 0 and res.get("errors")):
            return res
        elif res and res.get("errors"):
            logger.warning("[SharePoint] Gravação direta apresentou erros: %s. Acionando Fallback Power Automate...", res.get("errors"))
    except Exception as e:
        logger.warning(
            "[SharePoint] Falha na comunicação direta via Graph API (%s). Acionando Fallback Power Automate...",
            e,
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
