# -*- coding: utf-8 -*-
"""
google_sheets_client.py - Integração e sincronização direta com Google Sheets via Google Apps Script Web App.
Responsável por alimentar em paralelo a planilha do Google Sheets com todos os eventos
de streaming, aplicando desmembramento de linhas individuais por canal e proteção anti-duplicação rigorosa.
"""

import os
import re
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

import requests

logger = logging.getLogger("GoogleSheetsClient")

DEFAULT_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxzWKi1dNiGUiF15Ysl_69Pe2dt2vUpe1UBQ9xadPenmnsH68VOk6W1ZMwhRQkRpkBX/exec"
GS_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gsheets_events_cache.json")

MONTH_NAMES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

def is_cbf_broadcast_authorized(camp: str, part: str, canal: str) -> bool:
    """Verifica direitos oficiais CBF através de Streaming_Scheduler."""
    try:
        from Streaming_Scheduler import is_cbf_broadcast_authorized as _auth
        return _auth(camp, part, canal)
    except Exception:
        return True

PVID_MAP = {
    "amazon prime": "Prime Video - PV3687",
    "cazé tv": "CAZETV - PV3623",
    "caze tv": "CAZETV - PV3623",
    "netflix": "Netflix - PV3679",
    "disney plus": "Disney Plus - PV3703",
    "max": "Max oscar - PV3690",
    "ge tv": "GE TV3 (NFL) - PV3725",
    "tnt_sports": "TNT_SPORTS2 - PV3744",
    "tnt sports": "TNT_SPORTS2 - PV3744",
    "tnt paytv": "TNT - 316",
    "sport tv": "SportTV- PV 266",
    "sportv": "SportTV- PV 266",
    "record": "Record - 58",
    "gaúcha": "Gaucha - PV3796",
    "gaucha": "Gaucha - PV3796",
    "gaúcha esportes": "Gaucha - PV3796",
    "gaucha esportes": "Gaucha - PV3796",
    "itatiaia": "Itatiaia PV 3614",
    "desimpedidos": "Desimpedidos  ao vivo- PV3697",
    "outro": "Gaucha - PV3796",
}


def _get_webapp_url() -> str:
    """Retorna a URL do Web App configurada nas variáveis de ambiente ou o padrão."""
    from crypto_utils import get_env_value
    try:
        url = get_env_value("GSHEETS_WEBAPP_URL")
        if url and url.strip():
            return url.strip()
    except Exception:
        pass
    return os.getenv("GSHEETS_WEBAPP_URL", DEFAULT_WEBAPP_URL).strip()


def _obter_pvid_canal(canal: str) -> str:
    """Mapeia o canal para o PVID TV BOX padrão correspondente."""
    c_lower = str(canal or "").strip().lower()
    for k, v in PVID_MAP.items():
        if k in c_lower:
            return v
    return f"{canal.strip()} - PVBOX" if canal and canal.strip() else "PVBOX"


def _obter_responsavel_canal(canal: str) -> str:
    """Retorna o responsável padrão pelo canal."""
    return "Cleber BL01 e Backup"


def _carregar_cache_gsheets() -> List[Dict[str, Any]]:
    """Carrega eventos existentes armazenados no cache local."""
    if os.path.exists(GS_CACHE_FILE):
        try:
            with open(GS_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning(f"[Google Sheets Cache] Erro ao ler cache local: {e}")
    return []


def _salvar_cache_gsheets(items: List[Dict[str, Any]]) -> None:
    """Salva itens no cache local de forma cumulativa e segura."""
    try:
        existing = _carregar_cache_gsheets()
        # Mescla garantindo unicidade por (partida, data, canal)
        seen = set()
        merged = []

        for it in existing + items:
            p = str(it.get("partida", "")).strip().lower()
            d = str(it.get("data", ""))[:10].strip()
            c = str(it.get("canal", "")).strip().lower()
            key = (p, d, c)
            if key not in seen:
                seen.add(key)
                merged.append(it)

        with open(GS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[Google Sheets Cache] Erro ao salvar cache local: {e}")


def _parse_date_to_dmy(date_val: Any) -> Tuple[str, str, str]:
    """
    Converte qualquer formato de data (YYYY-MM-DD, ISO, DD/MM/YYYY) para:
    - dmy_str: 'DD/MM/YYYY'
    - iso_short: 'YYYY-MM-DD'
    - mes_pt: 'Novembro' (ou o mês correspondente)
    """
    s = str(date_val or "").strip()
    if not s:
        now = datetime.now()
        return now.strftime("%d/%m/%Y"), now.strftime("%Y-%m-%d"), MONTH_NAMES_PT[now.month - 1]

    # Remove horário caso venha em formato ISO '2026-11-23T12:00:00Z'
    s_date = s.split("T")[0].split(" ")[0].strip()

    dt = None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            dt = datetime.strptime(s_date, fmt)
            break
        except Exception:
            pass

    if not dt:
        now = datetime.now()
        return s_date, now.strftime("%Y-%m-%d"), MONTH_NAMES_PT[now.month - 1]

    dmy = dt.strftime("%d/%m/%Y")
    iso = dt.strftime("%Y-%m-%d")
    mes = MONTH_NAMES_PT[dt.month - 1]
    return dmy, iso, mes


def _carregar_eventos_existentes_gsheets(webapp_url: str) -> Tuple[set, set, List[Dict[str, Any]]]:
    """
    Consulta os eventos já cadastrados no Google Sheets (via GET na Web App ou cache local)
    para alimentar o Dedup Guard.
    Retorna: (existing_channel_matches, existing_tuples, loaded_items)
    """
    from sharepoint_client import _deep_normalize_partida, _normalizar_texto

    existing_matches = set()
    existing_tuples = set()
    loaded_items = []

    try:
        logger.info("[Google Sheets Direct] Consultando eventos existentes na planilha...")
        resp = requests.get(webapp_url, timeout=25)
        if resp.status_code == 200:
            loaded_items = resp.json()
            if isinstance(loaded_items, list) and loaded_items:
                _salvar_cache_gsheets(loaded_items)
        else:
            logger.warning(f"[Google Sheets Direct] GET retornou HTTP {resp.status_code}. Usando cache local...")
    except Exception as e:
        logger.warning(f"[Google Sheets Direct] Falha na consulta HTTP ({e}). Usando cache local...")

    # Sempre mescla com o cache local
    cached = _carregar_cache_gsheets()
    all_known = loaded_items if loaded_items else cached

    for it in all_known:
        p_raw = str(it.get("partida", "")).strip()
        p_tuple = _deep_normalize_partida(p_raw)
        p_norm = _normalizar_texto(p_raw)
        _, iso_d, _ = _parse_date_to_dmy(it.get("data"))
        c_norm = _normalizar_texto(it.get("canal", ""))

        if p_tuple != ("",) and iso_d:
            existing_matches.add((p_tuple, iso_d, c_norm))
        if p_norm and iso_d:
            existing_tuples.add((p_norm, iso_d, c_norm))

    return existing_matches, existing_tuples, all_known


def push_events_to_google_sheets(items: List[Dict[str, Any]], webapp_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Envia eventos para a planilha do Google Sheets via Web App com desmembramento de canais
    (estritamente 1 linha por canal individual) e blindagem contra duplicações.
    """
    if not items:
        return {"total": 0, "inserted": 0, "skipped_existing": 0, "errors": [], "source": "google_sheets"}

    from sharepoint_client import (
        _mapear_canal,
        _normalizar_texto,
        _deep_normalize_partida,
        _obter_titulo_oficial_campeonato,
    )

    url = (webapp_url or _get_webapp_url()).strip()
    existing_matches, existing_tuples, _ = _carregar_eventos_existentes_gsheets(url)

    itens_para_inserir = []
    skipped_count = 0
    errors = []

    logger.info(f"[Google Sheets] Processando {len(items)} evento(s) para sincronização...")

    for ev in items:
        try:
            camp_raw = str(ev.get("Campeonato") or ev.get("campeonato") or "").strip()
            part_raw = str(ev.get("Partida") or ev.get("partida") or "").strip()
            dt_raw = str(ev.get("Data") or ev.get("data") or "").strip()
            hora = str(ev.get("Horário") or ev.get("horario") or "").strip()
            canal_raw = ev.get("Canal de Transmissão") or ev.get("canal") or ""

            if not camp_raw or not part_raw or not dt_raw:
                continue

            camp_oficial = _obter_titulo_oficial_campeonato(camp_raw)
            part_norm = re.sub(r"\s+[vVxX]\s+", " x ", part_raw).strip()
            p_tuple = _deep_normalize_partida(part_norm)
            p_text_norm = _normalizar_texto(part_norm)
            dmy_str, iso_d, mes = _parse_date_to_dmy(dt_raw)

            # Tolerância de datas vizinhas (+/- 1 dia)
            d_ant, d_pos = "", ""
            try:
                dt_obj = datetime.strptime(iso_d, "%Y-%m-%d")
                d_ant = (dt_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                d_pos = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")
            except Exception:
                pass

            # Desmembra canais: 1 linha por canal individual
            canais_alvo = _mapear_canal(canal_raw)
            if not canais_alvo:
                canais_alvo = ["Nenhuma"]

            for canal_nome in canais_alvo:
                ch_norm = _normalizar_texto(canal_nome)

                # Validação de direitos CBF
                try:
                    if not is_cbf_broadcast_authorized(camp_oficial, part_norm, canal_nome):
                        logger.warning(f"[Google Sheets Bloqueio] '{part_norm}' ({camp_oficial}) [{canal_nome}] sem direitos CBF. Ignorando.")
                        continue
                except Exception:
                    pass

                # Dedup Guard: verifica se o confronto já existe na data para o mesmo canal
                match_key = (p_tuple, iso_d, ch_norm)
                tuple_key = (p_text_norm, iso_d, ch_norm)

                if match_key in existing_matches or tuple_key in existing_tuples:
                    logger.info(f"[Google Sheets Dedup] '{part_norm}' ({iso_d}) no canal '{canal_nome}' já existe no Sheets. Ignorado.")
                    skipped_count += 1
                    continue

                if d_ant and (p_tuple, d_ant, ch_norm) in existing_matches:
                    logger.info(f"[Google Sheets Dedup] '{part_norm}' já consta no dia anterior ({d_ant}) [{canal_nome}]. Ignorado.")
                    skipped_count += 1
                    continue

                if d_pos and (p_tuple, d_pos, ch_norm) in existing_matches:
                    logger.info(f"[Google Sheets Dedup] '{part_norm}' já consta no dia seguinte ({d_pos}) [{canal_nome}]. Ignorado.")
                    skipped_count += 1
                    continue

                # Cria o registro formatado exatamente como a planilha espera
                row_dict = {
                    "anexos": str(ev.get("anexos", "") or ""),
                    "mes": mes,
                    "data": dmy_str,
                    "horario": hora,
                    "campeonato": camp_oficial,
                    "partida": part_norm,
                    "responsavel": str(ev.get("responsavel") or _obter_responsavel_canal(canal_nome)),
                    "canal": canal_nome,
                    "pvid": str(ev.get("pvid") or _obter_pvid_canal(canal_nome)),
                    "status_entrega": str(ev.get("status_entrega") or "Pendente"),
                    "programado": str(ev.get("programado") or "NÃO")
                }
                itens_para_inserir.append(row_dict)

                # Marca para evitar duplicatas dentro do mesmo lote
                existing_matches.add(match_key)
                existing_tuples.add(tuple_key)

        except Exception as e:
            logger.error(f"[Google Sheets] Erro ao preparar item '{ev}': {e}", exc_info=True)
            errors.append(str(e))

    if not itens_para_inserir:
        logger.info(f"[Google Sheets Dedup] Todos os itens já existem na planilha ({skipped_count} ignorados).")
        return {
            "total": len(items),
            "inserted": 0,
            "skipped_existing": skipped_count,
            "errors": errors,
            "source": "google_sheets"
        }

    # Envia em lotes de até 50 itens para garantir execução ágil no Google Apps Script
    batch_size = 50
    inserted_total = 0

    for i in range(0, len(itens_para_inserir), batch_size):
        batch = itens_para_inserir[i:i + batch_size]
        try:
            logger.info(f"[Google Sheets] Enviando lote {i // batch_size + 1} ({len(batch)} itens) para o Apps Script...")
            resp = requests.post(url, json=batch, timeout=60, allow_redirects=True)
            if resp.status_code in (200, 201):
                try:
                    res_json = resp.json()
                    ins = res_json.get("inseridos", len(batch))
                    inserted_total += ins
                except Exception:
                    inserted_total += len(batch)
            else:
                logger.error(f"[Google Sheets] Erro HTTP no envio: {resp.status_code} - {resp.text[:200]}")
                errors.append(f"HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"[Google Sheets] Exceção ao enviar lote: {e}", exc_info=True)
            errors.append(str(e))

    # Atualiza o cache local com os itens recém-inseridos
    if inserted_total > 0:
        _salvar_cache_gsheets(itens_para_inserir)

    logger.info(f"[Google Sheets] Sincronização concluída: {inserted_total} inseridos, {skipped_count} já existiam.")
    return {
        "total": len(items),
        "inserted": inserted_total,
        "skipped_existing": skipped_count,
        "errors": errors,
        "source": "google_sheets"
    }
