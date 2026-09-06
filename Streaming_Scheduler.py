# === ChatGPT injected prelude (non-intrusive) ===
# Generated: 2025-09-24T16:41:23.015658
# Features:
# - Rotating logs
# - Thread-safe Tkinter calls from worker threads
# - Auto FAQ tab
# - Robust date parsing & Treeview date normalization (fix '2026' issue)
# - Global excepthook to log uncaught exceptions
# - TimePopup safe patch to allow any minute (e.g., 12:13) and avoid m_scale error

import sys, threading, logging, re, os, time, requests, subprocess, shutil, csv, psutil, json
import pypdfium2 as pdfium
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

threadingTimer = None

global monitoramento_ativo


last_daily_run = None
monitoramento_ativo = False


# ---- Rotating logs ----
if not logging.getLogger().handlers:
    _fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s",
                             datefmt="%Y-%m-%d %H:%M:%S")
    _rot = RotatingFileHandler("log.txt", maxBytes=5_000_000, backupCount=7, encoding="utf-8")
    _rot.setFormatter(_fmt)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(_rot)

# ---- Thread-safe Tk wrappers ----
_TS_ROOT = None
import queue
import gc
_ui_queue = queue.Queue()
_UI_QUEUE_RUNNING = False

def _process_ui_queue():
    while True:
        try:
            task = _ui_queue.get_nowait()
            task()
        except queue.Empty:
            break
    if _TS_ROOT:
        _TS_ROOT.after(100, _process_ui_queue)

def _wrap_ui_func(func):
    def _inner(*args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)
        
        # worker thread: use queue
        holder = {'val': None, 'exc': None}
        ev = threading.Event()
        
        def _task():
            try:
                holder['val'] = func(*args, **kwargs)
            except Exception as e:
                holder['exc'] = e
            finally:
                ev.set()
        
        _ui_queue.put(_task)
        # We still wait because many calls (like get) expect a return value
        if not ev.wait(timeout=5.0):
            logging.warning("UI task %s timed out", getattr(func, "__name__", str(func)))
            return None
        if holder['exc']:
            raise holder['exc']
        return holder['val']
    return _inner

def install_threadsafe_ui(root):
    global _TS_ROOT, _UI_QUEUE_RUNNING
    _TS_ROOT = root
    if not _UI_QUEUE_RUNNING:
        _UI_QUEUE_RUNNING = True
        _process_ui_queue()
    try:
        import tkinter as tk
        import tkinter.ttk as ttk
        import tkinter.messagebox as mb
        # Wrap BaseWidget.configure
        try:
            tk.BaseWidget.configure = _wrap_ui_func(tk.BaseWidget.configure)
            tk.BaseWidget.config = tk.BaseWidget.configure
        except Exception as e:
            logging.debug("wrap BaseWidget.configure failed: %s", e)
        # Wrap common ttk.Treeview ops
        try:
            ttk.Treeview.insert = _wrap_ui_func(ttk.Treeview.insert)
            ttk.Treeview.delete = _wrap_ui_func(ttk.Treeview.delete)
            ttk.Treeview.item   = _wrap_ui_func(ttk.Treeview.item)
        except Exception as e:
            logging.debug("wrap Treeview ops failed: %s", e)
        # Wrap Text insert/delete
        try:
            tk.Text.insert = _wrap_ui_func(tk.Text.insert)
            tk.Text.delete = _wrap_ui_func(tk.Text.delete)
        except Exception as e:
            logging.debug("wrap Text failed: %s", e)
        # Wrap IntVar/StringVar etc.
        try:
            tk.Variable.set = _wrap_ui_func(tk.Variable.set)
            tk.Variable.get = _wrap_ui_func(tk.Variable.get)
        except Exception as e:
            logging.debug("wrap Variable failed: %s", e)
        # Wrap messageboxes
        for name in ('showinfo','showwarning','showerror','askyesno','askokcancel','askquestion','askretrycancel','askyesnocancel'):
            if hasattr(mb, name):
                setattr(mb, name, _wrap_ui_func(getattr(mb, name)))
    except Exception as e:
        logging.exception("install_threadsafe_ui failed: %s", e)

# Auto-install on Tk()
try:
    import tkinter as _tk_auto
    _orig_Tk_init = _tk_auto.Tk.__init__
    def _patched_Tk_init(self, *a, **kw):
        _orig_Tk_init(self, *a, **kw)
        try:
            install_threadsafe_ui(self)
        except Exception as e:
            logging.debug("auto-install thread-safe ui failed: %s", e)
    _tk_auto.Tk.__init__ = _patched_Tk_init
except Exception as e:
    logging.debug("Tk not available during import: %s", e)

# ---- FAQ tab injection ----
_FAQ_ATTEMPTS = 0
def _add_faq_tab_if_possible(root):
    global _FAQ_ATTEMPTS
    try:
        import tkinter as tk
        import tkinter.ttk as ttk
        def _find_notebook(w):
            try:
                for ch in w.winfo_children():
                    try:
                        if isinstance(ch, ttk.Notebook):
                            return ch
                    except Exception:
                        pass
                    nb = _find_notebook(ch); 
                    if nb: return nb
            except Exception: pass
            return None
        nb = _find_notebook(root)
        if nb is None:
            _FAQ_ATTEMPTS += 1
            if _FAQ_ATTEMPTS < 50:
                root.after(300, lambda: _add_faq_tab_if_possible(root))
            else:
                logging.info("FAQ: Notebook não encontrado; ignorado.")
            return
        faq = ttk.Frame(nb)
        text = tk.Text(faq, wrap="word", height=30, width=120)
        scroll = ttk.Scrollbar(faq, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        faq.rowconfigure(0, weight=1); faq.columnconfigure(0, weight=1)
        _FAQ_TEXT = """📌 **FAQ — Streaming Scheduler / Monitor de Qualidade (Completo)**

**Streaming (aba principal)**
- Busca eventos nas plataformas selecionadas (Prime etc.), preenche a grade, exporta/atualiza e pode enviar por e‑mail.
- Botões **Esquerdo/Direito** alternam o navegador a usar.
- *Auto Email as* agenda o horário diário de envio. *Auto Busca* agenda coleta automática.
- *Somente relatório*: executa a coleta/geração sem abrir navegadores extras.

**Acessos**
- Configura credenciais e parâmetros (SMTP, diretórios, números de arquivos a varrer, etc.).
- Arquivos sensíveis (.env, config.xml, auth.xml) não são versionados por segurança.

**Logs**
- Mostra erros/avisos. Este build usa **logs rotativos** (`log.txt` ~5 MB, 7 backups). Exceções não capturadas também caem aqui.

**FAQ**
- Esta aba.

**Proteções deste build**
- **UI thread-safe**: qualquer chamada de threads para widgets é redirecionada à thread principal do Tk.
- **Normalização de datas**: ao inserir linhas na grade, a coluna *Data* é analisada e **corrigida** (evita pular para 2026 quando o cartão é ambíguo).
- **Editor de Horário**: permite minutos livres (ex.: 12:13) e evita o erro de `m_scale` inexistente.

**Dicas**
- Marque *Wake the computer* no Agendador do Windows para executar enquanto o PC está ocioso.
- Use `.venv` e `requirements.txt`.
- Verifique o `log.txt` ao investigar qualquer comportamento estranho.
"""
        try:
            text.insert("1.0", _FAQ_TEXT)
            text.configure(state="disabled")
        except Exception as e:
            logging.debug("FAQ text insert failed: %s", e)
        try:
            nb.add(faq, text="FAQ")
        except Exception as e:
            logging.debug("FAQ tab add failed: %s", e)
        logging.info("FAQ: aba adicionada.")
    except Exception as e:
        logging.exception("FAQ: erro ao montar aba: %s", e)

try:
    import tkinter as _tk_faq
    _orig_Tk_init_faq = _tk_faq.Tk.__init__
    def _patched_Tk_init_faq(self, *a, **kw):
        _orig_Tk_init_faq(self, *a, **kw)
        try:
            self.after(350, lambda: _add_faq_tab_if_possible(self))
        except Exception as e:
            logging.debug("FAQ schedule failed: %s", e)
    _tk_faq.Tk.__init__ = _patched_Tk_init_faq
except Exception as e:
    logging.debug("FAQ Tk patch failed: %s", e)

# ---- Date parsing + normalization for Treeview.insert ----
from datetime import datetime, timedelta
_MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
           "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

def _try_int(x):
    try: return int(x)
    except: return None

def parse_event_date(texto_data: str, *, referencia: datetime|None=None, ended: bool=False) -> datetime:
    ref = referencia or datetime.now()
    t = (texto_data or "").strip()

    m = re.search(r"[A-Za-z]{3},?\s+([A-Za-z]{3})\s+(\d{1,2})(?:\s+(\d{4}))?", t)
    if m:
        mon = _MONTHS.get(m.group(1).lower())
        day = _try_int(m.group(2))
        year = _try_int(m.group(3)) or ref.year
        try:
            dt = datetime(year, mon, day)
            if not ended and (ref - dt).days > 60:
                dt = datetime(year+1, mon, day)
            return dt
        except Exception:
            pass

    m = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", t)
    if m:
        a, b, y = m.group(1), m.group(2), m.group(3)
        year = _try_int(y)
        year = (2000+year) if (year is not None and year < 100) else (year or ref.year)
        d1, m1 = _try_int(a), _try_int(b)
        try:
            dt = datetime(year, m1, d1)    # DD/MM
        except ValueError:
            dt = datetime(year, d1, m1)    # MM/DD
        if not ended and (ref - dt).days > 60:
            dt = datetime(dt.year+1, dt.month, dt.day)
        return dt

    # 🇧🇷 Prioridade para Hoje/Amanhã se não houver data numérica completa
    low = t.lower()
    if "amanh" in low:
        return ref + timedelta(days=1)
    if "hoje" in low:
        return ref

    return ref

def clamp_far_future(dt: datetime, max_days=365) -> datetime:
    ref = datetime.now()
    try:
        if (dt - ref).days > max_days:
            return datetime(ref.year, dt.month, dt.day)
        return dt
    except Exception:
        return ref

try:
    import tkinter.ttk as _ttk_norm
    _orig_tv_insert = _ttk_norm.Treeview.insert
    def _tv_insert_norm(self, parent, index, iid=None, **kw):
        vals = kw.get('values')
        if isinstance(vals, (list, tuple)) and len(vals) >= 3:
            try:
                lst = list(vals)
                lst[2] = clamp_far_future(parse_event_date(str(lst[2]))).strftime("%d/%m/%Y")
                kw['values'] = tuple(lst)
            except Exception as e:
                logging.debug("normalize date failed: %s", e)
        return _orig_tv_insert(self, parent, index, iid=iid, **kw)
    _ttk_norm.Treeview.insert = _tv_insert_norm
    logging.info("Normalization active: Treeview.insert (date idx=2).")
except Exception as e:
    logging.debug("Could not install Treeview normalization: %s", e)

# ---- Global excepthook ----
def _global_ex_hook(exc_type, exc, tb):
    logging.exception("UNCAUGHT: %s", exc, exc_info=(exc_type, exc, tb))
sys.excepthook = _global_ex_hook

# ---- TimePopup compatibility patch (minutes free + no m_scale required) ----
def _patch_timepopup_later(root):
    try:
        g = globals()
        TimePopup = g.get("TimePopup")
        if TimePopup is None:
            root.after(500, lambda: _patch_timepopup_later(root))
            return
        def _safe_current_hhmm(self):
            h = None; m = None
            if hasattr(self, "h_scale"):
                try: h = int(float(self.h_scale.get()))
                except Exception: pass
            if hasattr(self, "m_scale"):
                try: m = int(float(self.m_scale.get()))
                except Exception: pass
            if (m is None) and hasattr(self, "m_entry"):
                try: m = int(str(self.m_entry.get()).strip() or "0")
                except Exception: m = 0
            if (h is None) and hasattr(self, "h_entry"):
                try: h = int(str(self.h_entry.get()).strip() or "0")
                except Exception: h = 0
            if (m is None) and hasattr(self, "minute_var"):
                try: m = int(self.minute_var.get())
                except Exception: m = 0
            if (h is None) and hasattr(self, "hour_var"):
                try: h = int(self.hour_var.get())
                except Exception: h = 0
            h = max(0, min(23, 0 if h is None else h))
            m = max(0, min(59, 0 if m is None else m))
            return f"{h:02d}:{m:02d}"
        def _safe_snap_minute(self, value):
            try: v = int(round(float(value)))
            except Exception: v = 0
            return max(0, min(59, v))  # 1 em 1 minuto
        try: setattr(TimePopup, "_current_hhmm_from_scales", _safe_current_hhmm)
        except Exception: pass
        try: setattr(TimePopup, "_snap_minute", _safe_snap_minute)
        except Exception: pass
        logging.info("TimePopup patch aplicado (minutos livres; sem m_scale obrigatório).")
    except Exception as e:
        logging.exception("TimePopup patch error: %s", e)

try:
    import tkinter as _tk_tp
    _orig_Tk_init_tp = _tk_tp.Tk.__init__
    def _patched_Tk_init_tp(self, *a, **kw):
        _orig_Tk_init_tp(self, *a, **kw)
        try:
            self.after(400, lambda: _patch_timepopup_later(self))
        except Exception as e:
            logging.debug("TimePopup schedule failed: %s", e)
    _tk_tp.Tk.__init__ = _patched_Tk_init_tp
except Exception as e:
    logging.debug("Tk not available for TimePopup patch: %s", e)

# === end prelude ===



from tkinter import *
from tkinter import ttk
import requests
from tkinter import messagebox
import tkinter.font as tkFont
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions 
import time
import traceback
import sys, os
import platform
import socket,shutil
from selenium.common.exceptions import StaleElementReferenceException
import csv
import re
from datetime import datetime, timedelta,timezone
from datetime import date
from threading import Timer
import threading
from shareplum import Site 
from requests_ntlm import HttpNtlmAuth
import csv, sys
import pandas as pd
from tkcalendar import DateEntry
from datetime import datetime
import subprocess
from tkinter import messagebox
import signal
import psutil
import tkinter.filedialog
from amazoncaptcha import AmazonCaptcha
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import pygetwindow as gw
import xml.etree.ElementTree as ET
from update import  Update
import yt_dlp
from googleapiclient.discovery import build
from crypto_utils import criptografar,carregar_env_criptografado,descriptografar,get_config_value,get_auth_value
import hashlib

thread_em_execucao = False
_lock_envio_email = threading.Lock()
_ultimo_hash_enviado = None
_ultima_janela_envio = datetime.min
_COOLDOWN_MIN = 5  # minutos
_eventos_iniciados = set()

# Globais de UI (Combobox)
options_plat = []
checkbox_states_plat = {}
combo_plat = None
menu_plat = None
checkbox_vars_plat = {}

options_camp = []
checkbox_states_camp = {}
combo_camp = None
menu_camp = None
checkbox_vars_camp = {}

def update_combobox_text_plat():
    global options_plat, checkbox_states_plat, combo_plat
    if 'options_plat' not in globals() or 'combo_plat' not in globals(): return
    selected_options = [opt for opt in options_plat if checkbox_states_plat.get(opt)]
    combo_plat.set(", ".join(selected_options) if selected_options else "Selecione...")

def toggle_checkbox_plat(option, var):
    global checkbox_states_plat
    checkbox_states_plat[option] = var.get()
    update_combobox_text_plat()

def show_checkbox_menu_plat():
    global menu_plat, combo_plat
    menu_plat.tk_popup(combo_plat.winfo_rootx(), combo_plat.winfo_rooty() + combo_plat.winfo_height())

def update_combobox_text_camp():
    global options_camp, checkbox_states_camp, combo_camp
    if 'options_camp' not in globals() or 'combo_camp' not in globals(): return
    selected_options = [opt for opt in options_camp if checkbox_states_camp.get(opt)]
    combo_camp.set(", ".join(selected_options) if selected_options else "Selecione...")

def toggle_checkbox_camp(option, var):
    global checkbox_states_camp
    checkbox_states_camp[option] = var.get()
    update_combobox_text_camp()

def show_checkbox_menu_camp():
    global menu_camp, combo_camp
    menu_camp.tk_popup(combo_camp.winfo_rootx(), combo_camp.winfo_rooty() + combo_camp.winfo_height())

class App:

    logging.basicConfig(
    filename="log.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
    
)

    def __init__(self, root):
       
       
        global checkbox7
        global checkbox8
        global checkbox9
        global checkbox10
        global button_update
        global tree
        global tree2
        global driverchrome
        global refreshlabel
        global refresh_entry
        global threadingTimer
        global entry_data
        global user_entry_prime
        global pass_entry_prime
        global user_entry_dazn
        global pass_entry_dazn
        global combo
        global checkbox_Camp1
        global checkbox_Camp2
        global thread_app_run
        global progresso
        global label_toolbar
        global label_toolbarprocess
        global email_entry
        global entry_email2
        global checkbox_ema
        global checkbox_grid
        global checkbox_busca
        global label_version
        global button_update
        global tempo_inicio
        global opcoesCamp
        global checkbox_states_camp
        global checkbox_states_plat
        global botao_getlista
        global botao_enviaremail
        global botao_abrir
        global botao_limpartree
        global botao_salvar
        global button_atualizacao
        global button_chrome1
        global button_add
        global button_chrome2
        global button_delete
        global thread_em_execucao
        global checkbox_vars_plat
        global checkbox_vars_camp
        global driverchrome1
        global driverchrome2
        global combo_plat
        driverchrome1 = None
        driverchrome2 = None

        # Carregar variáveis do .env
        env = carregar_env_criptografado()
        YOUTUBE_API_KEY = env.get("YOUTUBE_API_KEY", "")

        # Carregar a chave de API do YouTube

        thread_em_execucao = False

        tempo_inicio = time.time() 
        #setting title
        root.title("Streaming_Scheduler")
        #setting window size
        width=1200
        height=500
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)
        root.protocol("WM_DELETE_WINDOW", event_closedwindow)
        
        nb =  ttk.Notebook(root)
        nb.place(x=0,y=0,width=1200,height=500)

        tb1 = Frame(nb)
        nb.add(tb1,text="Streaming")
        criar_aba_erros(nb)
        refresh_label=Label(tb1)
        ft = tkFont.Font(family='Times',size=10)
        refresh_label["font"] = 'Helvetica 8 bold'
        refresh_label["fg"] = "#333333"
        refresh_label["justify"] = "center"
        refresh_label["text"] = "Refresh(seg):"
        refresh_label.place(x=30,y=20,width=80,height=10)
        
        label = Label(tb1, text="Digite a data de inicio:")
        label.configure(font= 'Helvetica 8 bold')
        label.place(x=130,y=12,width=130,height=30)

        label = Label(tb1, text="Atualizar tabela:")
        label.configure(font= 'Helvetica 8 bold')
        label.place(x=345,y=12,width=130,height=30)

        label = Label(tb1, text="Enviar E-mail:")
        label.configure(font= 'Helvetica 8 bold')
        label.place(x=550,y=12,width=130,height=30)

        button_chrome1=Button(tb1)
        button_chrome1=Button(tb1)
        button_chrome1=Button(tb1)
        button_chrome1["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        button_chrome1["font"] = 'Helvetica 8 bold'
        button_chrome1["fg"] = "black"
        button_chrome1["justify"] = "center"
        button_chrome1["text"] = "Esquerdo"
        button_chrome1.place(x=880,y=50,width=70,height=30)
        button_chrome1["command"] = lambda: verificar_chrome_debug("9222")

        button_chrome2=Button(tb1)
        button_chrome2=Button(tb1)
        button_chrome2=Button(tb1)
        button_chrome2["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        button_chrome2["font"] = 'Helvetica 8 bold'
        button_chrome2["fg"] = "black"
        button_chrome2["justify"] = "center"
        button_chrome2["text"] = "Direito"
        button_chrome2.place(x=962,y=50,width=70,height=30)
        button_chrome2["command"] = lambda: verificar_chrome_debug("9224")
        
        button_atualizacao=Button(tb1)
        button_atualizacao["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        button_atualizacao["font"] = 'Helvetica 8 bold'
        button_atualizacao["fg"] = "blue"
        button_atualizacao["justify"] = "center"
        button_atualizacao["text"] = "Atualizar"
        button_atualizacao.place(x=1090,y=50,width=70,height=30)        
        button_atualizacao["command"] = checar_update

        label = Label(tb1, text="Versão: ")
        label.configure(font= 'Helvetica 8 bold')
        label.place(x=1090,y=12,width=50,height=30)
        
        label_version = Label(tb1, text="")
        label_version.configure(font= 'Helvetica 8 bold')
        label_version.place(x=1130,y=12,width=40,height=30)

        refresh_entry=Entry(tb1)     
        refresh_entry["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times',size=10)
        refresh_entry["font"] 
        refresh_entry["fg"] = "#333333"
        refresh_entry["justify"] = "center"
        refresh_entry["text"] = "refresh"
        refresh_entry.insert(END,'20')
        refresh_entry.place(x=45,y=48,width=30,height=25)

        entry_data = Entry(tb1, width=10)
        entry_data.configure(font= 'Helvetica 8 bold')
        entry_data.bind("<KeyRelease>", lambda event: formatar_data(entry_data, event)) # Adiciona o evento KeyRelease
  
        
        data_atual = datetime.now()

        # Formatando a data com zeros à esquerda
        data_formatada = data_atual.strftime("%d/%m/%Y")


        entry_data.insert(0,data_formatada)

        entry_data.place(x=160,y=48,width=60,height=30)

        
        
        # Opções do Combobox (Plataformas)
        global options_plat, checkbox_states_plat, combo_plat, menu_plat, checkbox_vars_plat
        options_plat = ["Amazon Prime", "Disney", "Cazé TV", "Dazn", "Max", "CBF"]
        # checkbox_states_plat deve persistir se carregado do XML, senão inicializa True
        if 'checkbox_states_plat' not in globals() or not checkbox_states_plat:
            checkbox_states_plat = {opt: True for opt in options_plat}

        # Estilo personalizado para os checkboxes (com ícone ✓)
        style = ttk.Style()
        style.configure("TCheckbutton", font=('Arial', 10))

        # Cria o Combobox (apenas como gatilho para o menu)
        combo_plat = ttk.Combobox(tb1, state="readonly")
        combo_plat.place(x=290, y=48, width=150, height=30)
        combo_plat.set("Selecione plataformas")  # Texto inicial

# Cria um Menu suspenso com Checkboxes
        menu_plat = Menu(tb1, tearoff=0)
        checkbox_vars_plat = {}

        for option in options_plat:
            var = BooleanVar(value=False)  # ou False, se quiser todos desmarcados inicialmente
            checkbox_vars_plat[option] = var
            menu_plat.add_checkbutton(
                label=option,
                command=lambda opt=option, v=var: toggle_checkbox_plat(opt, v),
                variable=var,
                onvalue=True,
                offvalue=False,
                indicatoron=True,
                selectcolor='green'
            )
# Associa o clique do Combobox ao menu
        combo_plat.bind("<Button-1>", lambda e: show_checkbox_menu_plat())


        botao_getlista = Button(tb1, text="Buscar eventos", command=get_eventos)
        botao_getlista["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=8)
        botao_getlista["font"] = 'Helvetica 8 bold'
        botao_getlista["fg"] = "black"
        botao_getlista["justify"] = "center"
        botao_getlista.place(x=450,y=48,width=100,height=30)

        valor_inicial = StringVar()
        valor_inicial.set("binhole@gmail.com;cleber.goncalves@kantaribopemedia.com;suportecaptacao@ibopemedia.kantar.com") 

        email_entry=Entry(tb1,textvariable=valor_inicial)     
        email_entry["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times',size=10)
        email_entry["font"] 
        email_entry["fg"] = "#333333"
        email_entry["justify"] = "center"      
        email_entry.place(x=580,y=50,width=250,height=25)


        botao_limpartree = Button(tb1, text="Limpar", command=limpar_treeview)
        botao_limpartree["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=8)
        botao_limpartree["font"] = 'Helvetica 8 bold'
        botao_limpartree["fg"] = "black"
        botao_limpartree["justify"] = "center"
        botao_limpartree.place(x=450,y=80,width=80,height=30)

        botao_enviaremail = Button(tb1, text="Enviar", command=lambda: enviar_email(forcar=True))
        botao_enviaremail["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=8)
        botao_enviaremail["font"] = 'Helvetica 8 bold'
        botao_enviaremail["fg"] = "black"
        botao_enviaremail["justify"] = "center"
        botao_enviaremail.place(x=580,y=80,width=60,height=30)

        checkbox_ema = IntVar(value=1) 
        
        checkbox_Email=Checkbutton(tb1,variable=checkbox_ema)
        checkbox_Email["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        checkbox_Email["font"] = 'Helvetica 8 bold'
        checkbox_Email["fg"] = "black"
        checkbox_Email["justify"] = "center"
        checkbox_Email["text"] = "Auto Email as:"
        checkbox_Email.place(x=632,y=75,width=150,height=30)

        checkbox_grid = IntVar(value=1) 
        
        checkbox_BuscaAUto=Checkbutton(tb1,variable=checkbox_grid)
        checkbox_BuscaAUto["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        checkbox_BuscaAUto["font"] = 'Helvetica 8 bold'
        checkbox_BuscaAUto["fg"] = "black"
        checkbox_BuscaAUto["justify"] = "center"
        checkbox_BuscaAUto["text"] = "Auto Busca Lista"
        checkbox_BuscaAUto.place(x=640,y=95,width=150,height=30)
        # checkbox_Email.select()

        checkbox_busca = IntVar(value=0) 
        
        checkbox_BuscaAUto=Checkbutton(tb1,variable=checkbox_busca)
        checkbox_BuscaAUto["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        checkbox_BuscaAUto["font"] = 'Helvetica 8 bold'
        checkbox_BuscaAUto["fg"] = "black"
        checkbox_BuscaAUto["justify"] = "center"
        checkbox_BuscaAUto["text"] = "somente relatorio"
        checkbox_BuscaAUto.place(x=750,y=95,width=150,height=30)
        # checkbox_Email.select()
        

        entry_var_email = StringVar()
        entry_var_email.set("09:00")
        entry_email2 = Entry(tb1, textvariable=entry_var_email, width=20)
        # Validação em tempo real
        entry_var_email.trace_add("write", lambda *args: validar_hora_minuto(entry_var_email.get()))
        entry_email2.place(x=765,y=80,width=50,height=20)
        entry_email2.bind("<KeyRelease>", on_horario_email_alterado)

       

                       
        button_update=Button(tb1)
        button_update["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        button_update["font"] = 'Helvetica 8 bold'
        button_update["fg"] = "green"
        button_update["justify"] = "center"
        button_update["text"] = "Start"
        button_update.place(x=10,y=80,width=100,height=30)
        button_update["command"] = update_command

        botao_abrir = Button(tb1, text="Abrir", command=load_csv_new)
        botao_abrir["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=5)
        botao_abrir["font"] = 'Helvetica 8 bold'
        botao_abrir["fg"] = "black"
        botao_abrir["justify"] = "center"
        botao_abrir.place(x=135,y=80,width=50,height=30)

        botao_salvar = Button(tb1, text="Salvar", command= salvar)
        botao_salvar["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=5)
        botao_salvar["font"] = 'Helvetica 8 bold'
        botao_salvar["fg"] = "black"
        botao_salvar["justify"] = "center"
        botao_salvar.place(x=187,y=80,width=50,height=30)


        # Opções do Combobox (Campeonatos)
        global options_camp, checkbox_states_camp, combo_camp, menu_camp, checkbox_vars_camp
        options_camp = ["Brasileirão serie A", "Brasileirão serie B", "Copa do Brasil", "Copa do Mundo", "Mundial de Clubes FIFA", "Campeonato Paulista", "CONMEBOL Libertadores", "CONMEBOL Sudamericana"]
        if 'checkbox_states_camp' not in globals() or not checkbox_states_camp:
            checkbox_states_camp = {opt: True for opt in options_camp}

        # Cria o Combobox (apenas como gatilho para o menu)
        combo_camp = ttk.Combobox(tb1, state="readonly")
        combo_camp.place(x=290, y=80, width=150, height=30)
        combo_camp.set("Selecione Campeonatos")  # Texto inicial

# Cria um Menu suspenso com Checkboxes
        menu_camp = Menu(tb1, tearoff=0)
        checkbox_vars_camp = {}

        for option in options_camp:
            var = BooleanVar(value=True)  # Inicia marcado por padrão
            checkbox_vars_camp[option] = var
            menu_camp.add_checkbutton(
                label=option,
                variable=var,
                onvalue=True,
                offvalue=False,
                command=lambda opt=option, v=var: toggle_checkbox_camp(opt, v),
                indicatoron=True,
                selectcolor='green'
            )
# Associa o clique do Combobox ao menu
        combo_camp.bind("<Button-1>", lambda e: show_checkbox_menu_camp())
# Cria o combobox na posição desejada (x=270, y=80)
      
        

         # Add a Treeview widget
        tree = ttk.Treeview(tb1, columns=("Campeonato", "Partida", "Data", "Horário","Navegador","Min antes para ação","Canal de Transmissão","Url"), show='headings', height=13)
        scrollbarV = Scrollbar(root, orient="vertical", command=tree.yview)
        scrollbarV.pack(side="right", fill="y")
        tree.bind("<Double-1>", lambda event: onDoubleClick(tree,event))
        tree.configure(yscrollcommand=scrollbarV.set)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=('Helvetica bold', 8), foreground="#a132d0")
        style.configure("Treeview", foreground='black')
        style.configure("Treeview.Heading",background='#22405a', foreground='white') 

        minwidth = tree.column('#0', option='minwidth')

        
    
        tree.column("#1", anchor=CENTER,width=minwidth)
        tree.heading("#1", text="Campeonato")       
        tree.column("#2", anchor=CENTER,width=minwidth)
        tree.heading("#2", text="Evento")
        tree.column("#3", anchor=CENTER,width=minwidth)
        tree.heading("#3", text="Data", command=lambda: sort_by_date(tree, "#3"))
        tree.column("#4", anchor=CENTER,width=minwidth)
        tree.heading("#4", text="Horario")
        tree.column("#5", anchor=CENTER,width=minwidth)
        tree.heading("#5", text="Navegador")
        tree.column("#6", anchor=CENTER,width=minwidth)
        tree.heading("#6", text="Min antes para ação")
        tree.column("#7", anchor=CENTER,width=minwidth)
        tree.heading("#7", text="Plataforma")
        tree.column("#8", anchor=CENTER,width=minwidth)
        tree.heading("#8", text="Url")      
        tree.place(x=960,y=90,width=250,height=20)
        # tree.bind('<ButtonRelease-1>', selectItem)
        
        button_delete=Button(tb1)
        button_delete["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=25)
        button_delete["font"] = 'Helvetica 18 bold'
        button_delete["fg"] = "blue"
        button_delete["justify"] = "center"
        button_delete["text"] = "+"
        button_delete.place(x=62, y=345, width=45, height=25)

        button_delete["command"] = add

        button_add=Button(tb1)
        button_add["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=25)
        button_add["font"] = 'Helvetica 18 bold'
        button_add["fg"] = "red"
        button_add["justify"] = "center"
        button_add["text"] = "-"
        button_add.place(x=40,y=120,width=30,height=20)
        button_add["command"] = delete

        
        toolbar = Frame(tb1, bg="#2c3e50", height=5) 

         # Criando a barra de progresso dentro da toolbar
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure("blue.Horizontal.TProgressbar", 
                troughcolor='white',        # Cor de fundo da trilha
                bordercolor='gray',         # Cor da borda
                background='#1E90FF',       # Cor principal da barra (azul DodgerBlue)
                lightcolor='#1E90FF',       # Cor de luz da barra
                darkcolor='#1E90FF',        # Cor de sombra da barra
                thickness=20)               # Define a espessura da barra
       
        label_toolbar = Label(toolbar,
            bg="#2c3e50",       # mesmo fundo da toolbar para integração visual
            fg="#ecf0f1",       # cor do texto (clara para contraste)
            font=("Helvetica", 9, "bold")
        )
        label_toolbar.pack(side=LEFT, padx=10, pady=10)

    
        progresso = ttk.Progressbar(toolbar, 
                               style="blue.Horizontal.TProgressbar",
                               orient="horizontal", 
                               length=100, 
                               mode="determinate")
   
        progresso.pack(side=RIGHT, padx=10, pady=10)
        progresso.pack_forget()

        label_toolbarprocess = Label(toolbar,
            bg="#2c3e50",       # mesmo fundo da toolbar para integração visual
            fg="#ecf0f1",       # cor do texto (clara para contraste)
            font=("Helvetica", 9, "bold")
        )
        label_toolbarprocess.pack(side=RIGHT, padx=15, pady=10)
      
        toolbar.pack(side=BOTTOM, fill=X)
        
        criar_aba_acessos(nb)
        criar_aba_campeonatos(nb)
        
        def onDoubleClick(tree, event):
            # Fecha popup anterior (se houver)
            try:
                tree.entryPopup.destroy()
            except AttributeError:
                pass

            rowid = tree.identify_row(event.y)
            column = tree.identify_column(event.x)
            if not rowid:
                return

            # Info da célula clicada
            x, y, width, height = tree.bbox(rowid, column)
            col_index = int(column[1:]) - 1  # 0-based
            atual = tree.item(rowid, 'values')[col_index]

            # Posição do popup
            abs_x = tree.winfo_rootx() + x
            abs_y = tree.winfo_rooty() + y + height // 2

            # 0:Campeonato | 1:Partida | 2:Data | 3:Horário | 4:Navegador | 5:Min antes | 6:Plataforma | 7:Url
            if col_index == 2:
                DatePopup(tree, rowid, col_index, atual, abs_x, abs_y)
            elif col_index == 3:
                TimePopup(tree, rowid, col_index, atual, abs_x, abs_y)
            elif col_index == 4:
                OptionPopup(tree, rowid, col_index, atual, abs_x, abs_y,
                            options=("Esquerda", "Direita"))
            elif col_index == 5:
                MinutesPopup(tree, rowid, col_index, atual, abs_x, abs_y,
                            min_value=0, max_value=120, step=1)  # ajuste o range se quiser
            elif col_index == 6:
                OptionPopup(tree, rowid, col_index, atual, abs_x, abs_y,
                            options=("Amazon Prime", "Disney", "Cazé TV", "Dazn", "Paramount","Max"))
            else:
                entryPopup = EntryPopup(tree, rowid, col_index, atual)
                entryPopup.place(x=x, y=y + height // 2, width=width, height=height, anchor='w')

        
class EntryPopup(ttk.Entry):
    def __init__(self, parent, iid, column, text, **kw):
        ttk.Style().configure('pad.TEntry', padding='1 1 1 1')
        super().__init__(parent, style='pad.TEntry', **kw)
        self.tv = parent
        self.iid = iid
        self.column = column

        self.insert(0, text) 
        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        # self['selectbackground'] = '#1BA1E2'
        self['exportselection'] = False

        self.focus_force()
        self.select_all()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())


    def on_return(self, event):
        rowid = self.tv.focus()
        vals = self.tv.item(rowid, 'values')
        vals = list(vals)
        vals[self.column] = self.get()
        self.tv.item(rowid, values=vals)
        self.destroy()


    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'

def on_horario_email_alterado(event=None):
    global monitoramento_ativo
    monitoramento_ativo = False
    logging.info("Horário alterado — reagendando automaticamente")
    update_command()  # recria o schedule


def _set_cell_value(tv, rowid, col_index, value):
    vals = list(tv.item(rowid, 'values'))
    vals[col_index] = value
    tv.item(rowid, values=vals)

class DatePopup(Toplevel):
    """Popup com calendário (dd/MM/yyyy)."""
    def __init__(self, tv, rowid, column, initial, abs_x, abs_y):
        super().__init__(tv)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.tv, self.rowid, self.column = tv, rowid, column



        self.cal = DateEntry(self, date_pattern="dd/MM/yyyy", locale="pt_BR", width=12)
        # Tenta posicionar a data inicial
        try:
            dt = datetime.strptime(str(initial).strip(), "%d/%m/%Y")
            self.cal.set_date(dt)
        except Exception:
            pass

        self.cal.pack(padx=4, pady=4)
        self.cal.bind("<Return>", self._ok)
        self.cal.bind("<<DateEntrySelected>>", lambda e: self.after(0, self._ok))
        self.bind("<Escape>", lambda e: self.destroy())

        self.geometry(f"+{abs_x}+{abs_y}")
        self.cal.focus_set()

    def _ok(self, event=None):
        value = self.cal.get()
        _set_cell_value(self.tv, self.rowid, self.column, value)
        self.after(0, self.destroy)


class TimePopup(Toplevel):
    """Popup para hora/minuto (HH:MM) com sliders (Scale) + caixa de texto HH:MM.
       Fecha só no OK/Enter (ou Cancelar/Esc)."""
    def __init__(self, tv, rowid, column, initial, abs_x, abs_y, *, minute_step=5):
        super().__init__(tv)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        self.tv, self.rowid, self.column = tv, rowid, column
        self.minute_step = max(1, int(minute_step))
        self._updating = False  # evita loops de atualização bidirecional

        # valores iniciais
        try:
            ini = str(initial).strip()
            hh, mm = ini.split(":")
            hh, mm = int(hh), int(mm)
        except Exception:
            hh, mm = 0, 0

        frm = Frame(self)
        frm.pack(padx=10, pady=10)

        # Pré-visualização
        self.preview = Label(frm, text=f"{hh:02d}:{mm:02d}", font=("Segoe UI", 16, "bold"))
        self.preview.grid(row=0, column=0, columnspan=4, pady=(0, 8), sticky="w")

        # Caixa de texto HH:MM
        Label(frm, text="HH:MM").grid(row=1, column=0, sticky="w")
        self.time_var = StringVar(value=f"{hh:02d}:{mm:02d}")
        self.entry_time = ttk.Entry(frm, textvariable=self.time_var, width=7, justify="center")
        self.entry_time.grid(row=1, column=1, sticky="w")
        # Atualiza sliders quando digitar / sair do campo
        self.entry_time.bind("<KeyRelease>", self._on_time_entry_change)
        self.entry_time.bind("<FocusOut>", self._on_time_entry_change)
        self.entry_time.bind("<Return>", self._ok)

        # Slider de Hora
        Label(frm, text="Hora").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.h_scale = ttk.Scale(frm, from_=0, to=23, orient=HORIZONTAL, command=self._on_slide)
        self.h_scale.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(8, 0))
        self.h_scale.set(hh)

        # Slider de Minuto
        Label(frm, text="Minuto").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.m_scale = ttk.Scale(frm, from_=0, to=59, orient=HORIZONTAL, command=self._on_slide)
        self.m_scale.grid(row=3, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(8, 0))
        self.m_scale.set(mm)

        # Marcas (opcional)
        Label(frm, text="0      15      30      45", font=("Segoe UI", 8)).grid(row=4, column=1, columnspan=3, sticky="ew")

        # Botões
        btn_ok = ttk.Button(frm, text="OK", command=self._ok)
        btn_cancel = ttk.Button(frm, text="Cancelar", command=self.destroy)
        btn_ok.grid(row=5, column=2, pady=(10, 0), sticky="e", padx=(0, 6))
        btn_cancel.grid(row=5, column=3, pady=(10, 0), sticky="e")

        # Teclado
        self.bind("<Return>", self._ok)
        self.bind("<Escape>", lambda e: self.destroy())

        # Scroll do mouse para ajuste fino
        for w in (self.h_scale, self.m_scale):
            w.bind("<MouseWheel>", self._on_wheel)     # Windows
            w.bind("<Button-4>", self._on_wheel_up)    # Linux
            w.bind("<Button-5>", self._on_wheel_down)  # Linux

        frm.grid_columnconfigure(1, weight=1)
        self.geometry(f"+{abs_x}+{abs_y}")
        self._refresh_preview()

    # ---------- Helpers ----------
    def _snap_minute(self, v):
        step = self.minute_step
        v = int(round(float(v)))
        if step > 1:
            v = (round(v / step) * step) % 60
        return max(0, min(59, v))

    def _current_hhmm_from_scales(self):
        h = int(round(float(self.h_scale.get())))
        m = self._snap_minute(self.m_scale.get())
        # alinhar visualmente o minute ao step
        if abs(m - self.m_scale.get()) >= 0.5:
            self.m_scale.set(m)
        return f"{h:02d}:{m:02d}"

    def _refresh_preview(self):
        self.preview.config(text=self._current_hhmm_from_scales())
        # atualiza a entry sem loop
        if not self._updating:
            self._updating = True
            self.time_var.set(self._current_hhmm_from_scales())
            self._updating = False

    def _parse_time_text(self, text):
        import re
        txt = str(text).strip()
        m = re.match(r'^(\d{1,2}):(\d{1,2})$', txt)
        if not m:
            return None
        h = int(m.group(1))
        m_ = int(m.group(2))
        if not (0 <= h <= 23 and 0 <= m_ <= 59):
            return None
        # ajusta ao passo de minuto
        m_ = self._snap_minute(m_)
        return h, m_

    # ---------- Callbacks ----------
    def _on_slide(self, _evt=None):
        if self._updating:
            return
        self._refresh_preview()

    def _on_time_entry_change(self, _evt=None):
        if self._updating:
            return
        parsed = self._parse_time_text(self.time_var.get())
        if parsed is None:
            # entrada inválida: apenas não sincroniza; preview mantém último válido
            return
        h, m = parsed
        self._updating = True
        self.h_scale.set(h)
        self.m_scale.set(m)
        self._updating = False
        self._refresh_preview()

    def _on_wheel(self, evt):
        self._nudge(evt.widget, 1 if evt.delta > 0 else -1)

    def _on_wheel_up(self, evt):
        self._nudge(evt.widget, +1)

    def _on_wheel_down(self, evt):
        self._nudge(evt.widget, -1)

    def _nudge(self, widget, delta):
        if widget is self.h_scale:
            val = max(0, min(23, int(round(float(self.h_scale.get()))) + delta))
            self.h_scale.set(val)
        else:
            cur = int(round(float(self.m_scale.get())))
            step = self.minute_step
            val = (cur + (delta * step)) % 60
            self.m_scale.set(val)
        self._refresh_preview()

    def _ok(self, event=None):
        # tenta usar o que está na caixa; se inválido, usa os sliders
        parsed = self._parse_time_text(self.time_var.get())
        if parsed is None:
            value = self._current_hhmm_from_scales()
        else:
            h, m = parsed
            value = f"{h:02d}:{m:02d}"

        vals = list(self.tv.item(self.rowid, 'values'))
        vals[self.column] = value
        self.tv.item(self.rowid, values=vals)
        self.after(0, self.destroy)

class OptionPopup(Toplevel):
    """Popup com Combobox de opções fixas (ex.: Esquerda/Direita)."""
    def __init__(self, tv, rowid, column, initial, abs_x, abs_y, options=("Esquerda", "Direita")):
        super().__init__(tv)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.tv, self.rowid, self.column = tv, rowid, column

        frm = Frame(self)
        frm.pack(padx=6, pady=6)

        self.cbo = ttk.Combobox(frm, values=list(options), state="readonly", width=14)
        if str(initial) in options:
            self.cbo.set(str(initial))
        else:
            self.cbo.current(0)
        self.cbo.pack(side=LEFT, padx=2)

        ok = ttk.Button(frm, text="OK", command=self._ok)
        ok.pack(side=LEFT, padx=6)

        self.cbo.bind("<<ComboboxSelected>>", self._ok)
        self.bind("<Return>", self._ok)
        self.bind("<Escape>", lambda e: self.destroy())

        self.geometry(f"+{abs_x}+{abs_y}")
        self.cbo.focus_set()

    def _ok(self, event=None):
        value = self.cbo.get()
        _set_cell_value(self.tv, self.rowid, self.column, value)
        self.destroy()

class MinutesPopup(Toplevel):
    """Popup com slider + caixa de texto para 'Min antes para ação'."""
    def __init__(self, tv, rowid, column, initial, abs_x, abs_y,
                 *, min_value=0, max_value=120, step=1):
        super().__init__(tv)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        self.tv, self.rowid, self.column = tv, rowid, column
        self.min_value = int(min_value)
        self.max_value = int(max_value)
        self.step = max(1, int(step))
        self._updating = False

        # valor inicial
        try:
            initial_int = int(str(initial).strip())
        except Exception:
            initial_int = 0
        initial_int = max(self.min_value, min(self.max_value, initial_int))

        frm = Frame(self)
        frm.pack(padx=10, pady=10)

        Label(frm, text="Minutos antes da ação").grid(row=0, column=0, columnspan=3, sticky="w")
        self.preview = Label(frm, text=f"{initial_int} min", font=("Segoe UI", 14, "bold"))
        self.preview.grid(row=1, column=0, columnspan=3, pady=(0, 6), sticky="w")

        # Caixa de texto (minutos)
        Label(frm, text="Min:").grid(row=2, column=0, sticky="w")
        self.min_var = StringVar(value=str(initial_int))
        self.entry_min = ttk.Entry(frm, textvariable=self.min_var, width=6, justify="center")
        self.entry_min.grid(row=2, column=1, sticky="w")
        self.entry_min.bind("<KeyRelease>", self._on_entry_change)
        self.entry_min.bind("<FocusOut>", self._on_entry_change)
        self.entry_min.bind("<Return>", self._ok)

        # Slider
        self.scale = ttk.Scale(frm, from_=self.min_value, to=self.max_value,
                               orient=HORIZONTAL, command=self._on_slide)
        self.scale.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.scale.set(initial_int)

        # Botões
        btn_ok = ttk.Button(frm, text="OK", command=self._ok)
        btn_cancel = ttk.Button(frm, text="Cancelar", command=self.destroy)
        btn_ok.grid(row=4, column=1, pady=(10, 0), sticky="e", padx=(0, 6))
        btn_cancel.grid(row=4, column=2, pady=(10, 0), sticky="e")

        # Teclado
        self.bind("<Return>", self._ok)
        self.bind("<Escape>", lambda e: self.destroy())

        # Ajuste fino com roda do mouse
        self.scale.bind("<MouseWheel>", self._on_wheel)     # Windows
        self.scale.bind("<Button-4>", lambda e: self._nudge(+self.step))  # Linux
        self.scale.bind("<Button-5>", lambda e: self._nudge(-self.step))  # Linux

        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=0)
        frm.grid_columnconfigure(2, weight=0)

        self.geometry(f"+{abs_x}+{abs_y}")
        self._refresh_preview()

    # ---------- Helpers ----------
    def _snap(self, v):
        v = int(round(float(v)))
        if self.step > 1:
            v = round(v / self.step) * self.step
        return max(self.min_value, min(self.max_value, int(v)))

    def _current_value_from_slider(self):
        return self._snap(self.scale.get())

    def _refresh_preview(self):
        if not self._updating:
            self.preview.config(text=f"{self._current_value_from_slider()} min")
            # sincroniza entry com slider
            self._updating = True
            self.min_var.set(str(self._current_value_from_slider()))
            self._updating = False

    # ---------- Callbacks ----------
    def _on_slide(self, _evt=None):
        if self._updating:
            return
        self._refresh_preview()

    def _on_entry_change(self, _evt=None):
        if self._updating:
            return
        txt = str(self.min_var.get()).strip()
        if not txt.isdigit():
            return
        val = self._snap(int(txt))
        self._updating = True
        self.scale.set(val)
        self._updating = False
        self._refresh_preview()

    def _nudge(self, delta):
        cur = self._current_value_from_slider()
        self.scale.set(self._snap(cur + delta))
        self._refresh_preview()

    def _on_wheel(self, evt):
        self._nudge(self.step if evt.delta > 0 else -self.step)

    def _ok(self, event=None):
        # prioriza o que está na caixa (se for número); senão usa o slider
        txt = str(self.min_var.get()).strip()
        if txt.isdigit():
            value = str(self._snap(int(txt)))
        else:
            value = str(self._current_value_from_slider())

        vals = list(self.tv.item(self.rowid, 'values'))
        vals[self.column] = value
        self.tv.item(self.rowid, values=vals)
        self.after(0, self.destroy)

# === ABA DE ERROS COM FILTRO POR DATA E TIPO ===
def criar_aba_erros(notebook):
    import os
    import csv
    import re
    from datetime import datetime
    from tkinter import messagebox


    aba_erros = Frame(notebook)
    notebook.add(aba_erros, text='Logs')

    aba_erros.grid_rowconfigure(1, weight=1)
    aba_erros.grid_columnconfigure(0, weight=1)

    Label(aba_erros, text="Tipo de Erro:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
    tipo_var = StringVar()
    tipo_combo = ttk.Combobox(aba_erros, textvariable=tipo_var, values=["", "ERROR", "WARNING", "INFO"], width=10)
    tipo_combo.grid(row=0, column=1, padx=5, pady=5)

    Label(aba_erros, text="Data Início:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
    entrada_inicio = DateEntry(aba_erros, width=12, date_pattern="dd/MM/yyyy", locale="pt_BR")
    entrada_inicio.set_date(datetime.now())
    entrada_inicio.grid(row=0, column=3, padx=5, pady=5)

    Label(aba_erros, text="Data Fim:").grid(row=0, column=4, padx=5, pady=5, sticky=W)
    entrada_fim = DateEntry(aba_erros, width=12, date_pattern="dd/MM/yyyy", locale="pt_BR")
    entrada_fim.set_date(datetime.now())
    entrada_fim.grid(row=0, column=5, padx=5, pady=5)

    style = ttk.Style()
    style.configure("Treeview", font=('Helvetica', 9))
    style.configure("Treeview.Heading", font=('Helvetica', 9, 'bold'))

    tree_log = ttk.Treeview(aba_erros, columns=("data", "nivel", "linha", "mensagem"), show="headings", height=18)
    tree_log.heading("data", text="Data/Hora")
    tree_log.heading("nivel", text="Tipo")
    tree_log.heading("linha", text="Linha")
    tree_log.heading("mensagem", text="Mensagem")
    tree_log.column("data", width=150)
    tree_log.column("nivel", width=80)
    tree_log.column("linha", width=60, anchor=CENTER)
    tree_log.column("mensagem", width=660)
    tree_log.grid(row=1, column=0, columnspan=7, padx=10, pady=10, sticky="nsew")

    tree_log.tag_configure("ERROR", background="#ffcccc")
    tree_log.tag_configure("WARNING", background="#fff7cc")
    tree_log.tag_configure("INFO", background="#ccffcc")

    def onDoubleClick(tree, event):
        # Fecha popup anterior (se houver)
        try:
            tree.entryPopup.destroy()
        except AttributeError:
            pass

        rowid = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not rowid:
            return

        # Info da célula clicada
        x, y, width, height = tree.bbox(rowid, column)
        col_index = int(column[1:]) - 1  # 0-based
        atual = tree.item(rowid, 'values')[col_index]

        # Coordenadas absolutas p/ posicionar os popups ao lado da célula
        abs_x = tree.winfo_rootx() + x
        abs_y = tree.winfo_rooty() + y + height // 2

        # 0:Campeonato | 1:Partida | 2:Data | 3:Horário | 4:Navegador | ...
        if col_index == 2:
            DatePopup(tree, rowid, col_index, atual, abs_x, abs_y)
        elif col_index == 3:
            TimePopup(tree, rowid, col_index, atual, abs_x, abs_y)
        elif col_index == 4:
            OptionPopup(tree, rowid, col_index, atual, abs_x, abs_y, options=("Esquerda", "Direita"))
        else:
            entryPopup = EntryPopup(tree, rowid, col_index, atual)
            entryPopup.place(x=x, y=y + height // 2, width=width, height=height, anchor='w')
            
    def extrair_linha_erro(mensagem):
        """
        Extrai o número da linha da mensagem de erro, se presente.
        Suporta formatos como 'line 123' ou 'arquivo.py 123'.
        """
        match = re.search(r"\bline (\d+)", mensagem, re.IGNORECASE)
        if match:
            return match.group(1)
    
        match = re.search(r"\b\w+\.py[: ]+(\d+)", mensagem)
        if match:
            return match.group(1)
    
        return ""
    def aplicar_filtro():
        tree_log.delete(*tree_log.get_children())

        tipo = tipo_var.get().strip().upper()
        inicio = entrada_inicio.get().strip()
        fim = entrada_fim.get().strip()

        try:
            dt_inicio = datetime.strptime(inicio, "%d/%m/%Y") if inicio else None
            dt_fim = datetime.strptime(fim, "%d/%m/%Y") if fim else None
        except ValueError:
            messagebox.showerror("Erro de Formato", "As datas devem estar no formato dd/mm/yyyy")
            return

        if not os.path.exists("log.txt"):
            messagebox.showinfo("Arquivo Não Encontrado", "O arquivo 'log.txt' não foi encontrado.")
            return

        try:
            with open("log.txt", "r", encoding="latin-1") as f:
                linhas_processadas = []

                for linha in f:
                    try:
                        partes = linha.split(" - ", 2)
                        if len(partes) < 3:
                            continue
                        datahora = datetime.strptime(partes[0].strip(), "%Y-%m-%d %H:%M:%S")
                        nivel = partes[1].strip().upper()
                        mensagem = partes[2].strip()

                        if tipo and tipo != nivel:
                            continue
                        if dt_inicio and datahora.date() < dt_inicio.date():
                            continue
                        if dt_fim and datahora.date() > dt_fim.date():
                            continue

                        linha_num = extrair_linha_erro(mensagem)
                        mensagem_limpa = re.sub(r"(\w+\.py\s*)?line \d+|[\w/\\]+\.py \d+", "", mensagem, flags=re.IGNORECASE).strip()
                        linhas_processadas.append((datahora, nivel, linha_num, mensagem_limpa))
                    except Exception:
                        continue

                linhas_processadas.sort(reverse=True)

                for datahora, nivel, linha_num, mensagem in linhas_processadas:
                    tag = nivel if nivel in ["ERROR", "WARNING", "INFO"] else ""
                    tree_log.insert(
                        "", "end",
                        values=(datahora.strftime("%d/%m/%Y %H:%M:%S"), nivel, linha_num, mensagem),
                        tags=(tag,)
                    )
        except Exception as e:
            messagebox.showerror("Erro ao Ler Log", f"Ocorreu um erro ao ler o arquivo de log:\n{str(e)}")

    def limpar_logs():
        if os.path.exists("log.txt"):
            with open("log.txt", "w") as f:
                f.write("")
            aplicar_filtro()
            messagebox.showinfo("Limpar Logs", "O arquivo de log foi limpo com sucesso.")
        else:
            messagebox.showwarning("Aviso", "O arquivo log.txt não existe.")

    def exportar_logs():
        if not tree_log.get_children():
            messagebox.showwarning("Aviso", "Nenhum erro para exportar.")
            return
        try:
            with open("erros_exportados.csv", "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Data/Hora", "Tipo", "Linha", "Mensagem"])
                for item in tree_log.get_children():
                    writer.writerow(tree_log.item(item)["values"])
            messagebox.showinfo("Exportado", "Erros exportados para 'erros_exportados.csv'.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    Button(aba_erros, text="Filtrar", command=aplicar_filtro).grid(row=0, column=6, padx=5, pady=5)
    Button(aba_erros, text="🧹 Limpar Logs", command=limpar_logs).grid(row=2, column=0, padx=5, pady=10, sticky="w")
    Button(aba_erros, text="📤 Exportar", command=exportar_logs).grid(row=2, column=6, padx=5, pady=10, sticky="e")

    aplicar_filtro()

def criar_aba_acessos(notebook):
    frame = ttk.Frame(notebook, padding=20)
    notebook.add(frame, text="Acessos")

    # LabelFrame com borda e título
    lf = ttk.LabelFrame(frame, text="Cadastrar/Atualizar Credenciais", padding=(20, 15))
    lf.pack(fill="both", expand=True)

    # Campos em pares: (label, tag_xml, arquivo_fonte)
    pares = [
        (("Usuário Prime", "usuario_prime", "config.xml"), ("Senha Prime", "senha_prime", "config.xml")),
        (("Usuário Disney", "usuario_disney", "config.xml"), ("Senha Disney", "senha_disney", "config.xml")),
        (("Usuário DAZN", "usuario_dazn", "config.xml"), ("Senha DAZN", "senha_dazn", "config.xml")),
        (("Usuário Paramount", "usuario_paramount", "config.xml"), ("Senha Paramount", "senha_paramount", "config.xml")),
        (("Usuário Max", "usuario_max", "config.xml"), ("Senha Max", "senha_max", "config.xml")),
        (("E-mail SMTP (Gmail)", "email", "auth.xml"), ("Senha SMTP (App Password)", "senha", "auth.xml")),
    ]

    entrys = []
    campos_info = [] # List of (tag, file)

    for i, ((l1, c1, f1), (l2, c2, f2)) in enumerate(pares):
        # Coluna 0: Primeiro campo do par
        ttk.Label(lf, text=l1 + ":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
        e1 = ttk.Entry(lf, width=30)
        e1.grid(row=i, column=1, sticky="w", padx=8, pady=6)
        
        # Pre-fill
        val1 = get_config_value(c1, f1) if f1 == "config.xml" else get_auth_value(c1, f1)
        if val1: e1.insert(0, val1)
        
        entrys.append(e1)
        campos_info.append((c1, f1))

        # Coluna 2: Segundo campo do par (geralmente senha)
        ttk.Label(lf, text=l2 + ":").grid(row=i, column=2, sticky="e", padx=8, pady=6)
        e2 = ttk.Entry(lf, width=30, show="*" if "Senha" in l2 else "")
        e2.grid(row=i, column=3, sticky="w", padx=8, pady=6)
        
        # Pre-fill
        val2 = get_config_value(c2, f2) if f2 == "config.xml" else get_auth_value(c2, f2)
        if val2: e2.insert(0, val2)
        
        entrys.append(e2)
        campos_info.append((c2, f2))

    # Botão de salvar centralizado
    btn_salvar = ttk.Button(lf, text="💾 Salvar Dados", command=lambda: salvar_novos_acessos(entrys, campos_info))
    btn_salvar.grid(row=len(pares), column=0, columnspan=4, pady=25)

    # Ativar tema moderno
    style = ttk.Style()
    style.theme_use("clam")
    
        
def salvar_novos_acessos(entrys, campos_info):
    """
    Salva os dados nos respectivos arquivos (config.xml ou auth.xml)
    campos_info: lista de (tag, filename)
    """
    files_to_save = set(f for _, f in campos_info)
    
    try:
        # Dicionário para gerenciar os Trees dos arquivos
        trees = {}
        for fname in files_to_save:
            if os.path.exists(fname):
                trees[fname] = ET.parse(fname)
            else:
                # Cria arquivo novo se não existir
                root_tag = 'auth' if fname == 'auth.xml' else 'config'
                root = ET.Element(root_tag)
                trees[fname] = ET.ElementTree(root)

        # Atualiza valores
        for i, (campo, fname) in enumerate(campos_info):
            novo_valor = entrys[i].get().strip()
            if novo_valor:
                root = trees[fname].getroot()
                elem = root.find(campo)
                if elem is None:
                    elem = ET.SubElement(root, campo)
                elem.text = criptografar(novo_valor)

        # Grava os arquivos
        for fname, tree in trees.items():
            tree.write(fname, encoding="utf-8", xml_declaration=True)

        messagebox.showinfo("Sucesso", "Credenciais atualizadas com sucesso.")

    except Exception as e:
        logging.error(f"Falha ao atualizar credenciais: {e}")
        messagebox.showerror("Erro", f"Falha ao atualizar os dados: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ABA DE CAMPEONATOS DINÂMICOS
# ─────────────────────────────────────────────────────────────────────────────

CAMPEONATOS_CONFIG_FILE = "campeonatos_config.json"

PLATAFORMAS_DISPONIVEIS = [
    "Amazon Prime",
    "Disney",
    "Max",
    "Dazn",
    "Cazé TV",
]

def _camp_config_path():
    """Retorna o caminho do arquivo de configuração de campeonatos."""
    return os.path.join(os.getcwd(), CAMPEONATOS_CONFIG_FILE)


def carregar_campeonatos_config():
    """Lê campeonatos_config.json e retorna lista de dicts."""
    path = _camp_config_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logging.error(f"[CampConfig] Erro ao carregar config: {e}")
        return []


def salvar_campeonatos_config(lista):
    """Salva lista de campeonatos em campeonatos_config.json."""
    path = _camp_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"[CampConfig] Erro ao salvar config: {e}")
        raise


def criar_aba_campeonatos(notebook):
    """Cria a aba 'Campeonatos' no notebook para cadastro dinâmico."""
    import tkinter.font as tkFont
    from tkinter import messagebox, ttk

    frame = ttk.Frame(notebook, padding=10)
    notebook.add(frame, text="⚽ Campeonatos")

    # ── Título ────────────────────────────────────────────────────────────────
    ttk.Label(
        frame,
        text="Campeonatos Extras",
        font=("Helvetica", 11, "bold"),
    ).pack(anchor="w", pady=(0, 2))

    ttk.Label(
        frame,
        text=(
            "Cadastre aqui campeonatos adicionais para as plataformas suportadas. "
            "Eles serão buscados automaticamente junto com os demais ao clicar em 'Buscar Eventos'."
        ),
        wraplength=1100,
        foreground="#555",
    ).pack(anchor="w", pady=(0, 8))

    # ── Grid (Treeview) ───────────────────────────────────────────────────────
    cols = ("campeonato", "plataforma", "url", "ativo")
    col_headers = ("Campeonato", "Plataforma", "URL", "Ativo")
    col_widths   = (220, 130, 580, 60)

    tv_frame = ttk.Frame(frame)
    tv_frame.pack(fill="both", expand=True)

    tv = ttk.Treeview(tv_frame, columns=cols, show="headings", height=10)
    for col, hdr, w in zip(cols, col_headers, col_widths):
        tv.heading(col, text=hdr)
        tv.column(col, width=w, anchor="w" if col != "ativo" else "center")

    vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)
    tv.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # ── Funções internas ──────────────────────────────────────────────────────

    def _reload_tv():
        """Recarrega o treeview a partir do JSON."""
        for item in tv.get_children():
            tv.delete(item)
        for camp in carregar_campeonatos_config():
            ativo_str = "✅" if camp.get("ativo", True) else "❌"
            tv.insert(
                "",
                "end",
                values=(
                    camp.get("campeonato", ""),
                    camp.get("plataforma", ""),
                    camp.get("url", ""),
                    ativo_str,
                ),
            )

    def _abrir_formulario(titulo, valores_iniciais=None):
        """
        Abre janela de formulário para adicionar/editar.
        Retorna dict com dados ou None se o usuário cancelou.
        """
        result = {}
        win = Toplevel(notebook)
        win.title(titulo)
        win.resizable(False, False)
        win.grab_set()

        # Calcula posição central
        win.update_idletasks()
        pw = notebook.winfo_toplevel()
        x = pw.winfo_x() + pw.winfo_width()  // 2 - 300
        y = pw.winfo_y() + pw.winfo_height() // 2 - 140
        win.geometry(f"600x280+{x}+{y}")

        padx_lbl = 10
        pady_row = 8

        # Campeonato
        ttk.Label(win, text="Campeonato:").grid(row=0, column=0, sticky="e", padx=padx_lbl, pady=pady_row)
        e_camp = ttk.Entry(win, width=45)
        e_camp.grid(row=0, column=1, columnspan=2, sticky="w", padx=padx_lbl, pady=pady_row)

        # Plataforma
        ttk.Label(win, text="Plataforma:").grid(row=1, column=0, sticky="e", padx=padx_lbl, pady=pady_row)
        plat_var = StringVar(value=PLATAFORMAS_DISPONIVEIS[0])
        cb_plat = ttk.Combobox(win, textvariable=plat_var, values=PLATAFORMAS_DISPONIVEIS, state="readonly", width=25)
        cb_plat.grid(row=1, column=1, sticky="w", padx=padx_lbl, pady=pady_row)

        # URL
        ttk.Label(win, text="URL:").grid(row=2, column=0, sticky="e", padx=padx_lbl, pady=pady_row)
        e_url = ttk.Entry(win, width=60)
        e_url.grid(row=2, column=1, columnspan=2, sticky="w", padx=padx_lbl, pady=pady_row)

        # Ativo
        ativo_var = BooleanVar(value=True)
        ttk.Checkbutton(win, text="Ativo (buscar eventos)", variable=ativo_var).grid(
            row=3, column=1, sticky="w", padx=padx_lbl, pady=pady_row
        )

        # Preenche valores iniciais (modo edição)
        if valores_iniciais:
            e_camp.insert(0, valores_iniciais.get("campeonato", ""))
            plat_var.set(valores_iniciais.get("plataforma", PLATAFORMAS_DISPONIVEIS[0]))
            e_url.insert(0, valores_iniciais.get("url", ""))
            ativo_var.set(valores_iniciais.get("ativo", True))

        def _confirmar():
            nome = e_camp.get().strip()
            url  = e_url.get().strip()
            if not nome:
                messagebox.showwarning("Atenção", "Informe o nome do campeonato.", parent=win)
                return
            if not url:
                messagebox.showwarning("Atenção", "Informe a URL do campeonato.", parent=win)
                return
            result["campeonato"] = nome
            result["plataforma"] = plat_var.get()
            result["url"]        = url
            result["ativo"]      = ativo_var.get()
            win.destroy()

        def _cancelar():
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=15)
        ttk.Button(btn_frame, text="✅ Confirmar", command=_confirmar).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="❌ Cancelar",  command=_cancelar).pack(side="left", padx=10)

        win.wait_window()
        return result if result else None

    def _adicionar():
        dados = _abrir_formulario("Adicionar Campeonato")
        if not dados:
            return
        lista = carregar_campeonatos_config()
        lista.append(dados)
        salvar_campeonatos_config(lista)
        _reload_tv()
        messagebox.showinfo("Sucesso", f"Campeonato '{dados['campeonato']}' adicionado!")

    def _editar():
        sel = tv.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um campeonato para editar.")
            return
        idx = tv.index(sel[0])
        lista = carregar_campeonatos_config()
        if idx >= len(lista):
            return
        dados = _abrir_formulario("Editar Campeonato", valores_iniciais=lista[idx])
        if not dados:
            return
        lista[idx] = dados
        salvar_campeonatos_config(lista)
        _reload_tv()
        messagebox.showinfo("Sucesso", f"Campeonato '{dados['campeonato']}' atualizado!")

    def _remover():
        sel = tv.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um campeonato para remover.")
            return
        idx = tv.index(sel[0])
        lista = carregar_campeonatos_config()
        if idx >= len(lista):
            return
        nome = lista[idx].get("campeonato", "?")
        if not messagebox.askyesno("Confirmar", f"Remover '{nome}'?"):
            return
        lista.pop(idx)
        salvar_campeonatos_config(lista)
        _reload_tv()

    def _toggle_ativo():
        sel = tv.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um campeonato.")
            return
        idx = tv.index(sel[0])
        lista = carregar_campeonatos_config()
        if idx >= len(lista):
            return
        lista[idx]["ativo"] = not lista[idx].get("ativo", True)
        salvar_campeonatos_config(lista)
        _reload_tv()

    # ── Barra de botões ───────────────────────────────────────────────────────
    btn_bar = ttk.Frame(frame)
    btn_bar.pack(fill="x", pady=(8, 0))

    ttk.Button(btn_bar, text="➕ Adicionar",    command=_adicionar).pack(side="left", padx=4)
    ttk.Button(btn_bar, text="✏️ Editar",       command=_editar).pack(side="left",   padx=4)
    ttk.Button(btn_bar, text="🗑️ Remover",      command=_remover).pack(side="left",  padx=4)
    ttk.Button(btn_bar, text="🔄 Ativar/Pausar", command=_toggle_ativo).pack(side="left", padx=4)

    ttk.Label(
        btn_bar,
        text="💡 Dica: Adicione a URL exata da página de eventos do campeonato na plataforma.",
        foreground="#777",
        font=("Helvetica", 8),
    ).pack(side="right", padx=8)

    # Carga inicial
    _reload_tv()



class _QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

import re
import unicodedata

SEP_RE = re.compile(r"\s*(?:\||-|–|—|·|•|/|\[|\]|\(|\))\s*")
BRASILEIRAO_RE = re.compile(r"brasileir[aã]o\s*(\d{4})", re.I)
COPA_MUNDO_RE = re.compile(r"copa do mundo\s*(fifa)?\s*(\d{4})", re.I)
RODADA_RE = re.compile(r"(\d{1,2})\s*(?:ª|a)?\s*rodad[ao]\b", re.I)
PAULISTA_RE = re.compile(r"(campeonato\s+paulista|paulist[aã]o)\s*(\d{4})?", re.I)

def norm(txt: str) -> str:
    if not txt:
        return ""
    t = unicodedata.normalize("NFKD", txt)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower().strip()
    t = re.sub(r"^\s*ao vivo[:\- ]*\s*", "", t)
    t = re.sub(r"\s+", " ", t)
    return t

def parse_youtube_title(raw_title: str, raw_desc: str = ""):
    """
    Analisa título/descrição do YouTube e identifica:
    - Brasileirão
    - Copa do Mundo FIFA
    - Campeonato Paulista
    - Ano
    - Rodada (SEPARADA, não entra no nome do campeonato)
    """

    t = norm(raw_title)
    d = norm(raw_desc)
    tokens = SEP_RE.split(t) + [t]

    year = None
    rodada = None

    is_brasileirao = False
    is_copa_mundo = False
    is_paulista = False

    # =========================
    # BRASILEIRÃO
    # =========================
    for tok in tokens:
        m = BRASILEIRAO_RE.search(tok)
        if m:
            is_brasileirao = True
            year = m.group(1)
            break

    # =========================
    # COPA DO MUNDO FIFA
    # =========================
    if not is_brasileirao:
        for tok in tokens:
            m = COPA_MUNDO_RE.search(tok)
            if m:
                is_copa_mundo = True
                year = m.group(2)
                break

    # =========================
    # PAULISTÃO
    # =========================
    for tok in tokens:
        m = PAULISTA_RE.search(tok)
        if m:
            is_paulista = True
            if m.lastindex and m.group(2):
                year = m.group(2)
            break

    # =========================
    # RODADA
    # =========================
    for tok in tokens:
        r = RODADA_RE.search(tok)
        if r:
            rodada = int(r.group(1))
            break

    if rodada is None:
        r = RODADA_RE.search(t)
        if r:
            rodada = int(r.group(1))

    # =========================
    # FALLBACK NA DESCRIÇÃO
    # =========================
    if d:
        if not is_brasileirao:
            m = BRASILEIRAO_RE.search(d)
            if m:
                is_brasileirao = True
                year = m.group(1)

        if not is_copa_mundo:
            m = COPA_MUNDO_RE.search(d)
            if m:
                is_copa_mundo = True
                year = m.group(2)

        if not is_paulista:
            m = PAULISTA_RE.search(d)
            if m:
                is_paulista = True
                if m.lastindex and m.group(2):
                    year = m.group(2)

        if rodada is None:
            r = RODADA_RE.search(d)
            if r:
                rodada = int(r.group(1))

    return {
        "is_brasileirao": is_brasileirao,
        "is_copa_mundo": is_copa_mundo,
        "is_paulista": is_paulista,
        "year": year,
        "rodada": rodada
    }

def normalizar_titulo_evento(txt: str) -> str:
    if not txt:
        return ""
    txt = txt.strip().lower()
    # capitaliza cada palavra
    return " ".join(p.capitalize() for p in txt.split())

def obter_eventos_futuros(canal_url):
    """
    Retorna lista de tuplas: [(champ, titulo, url, dd/mm/YYYY, HH:MM)]
    Só considera lives/vídeos futuros do Brasileirão 2025.
    """
    from datetime import datetime, timezone
    import yt_dlp, logging

    eventos_futuros = []
    seen = set()

    # Obtendo data inicial da UI para filtro
    try:
        data_inicio_str = entry_data.get()
        data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
    except:
        data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        # 1) Listagem rápida do canal
        ydl_opts_list = {
            'quiet': True, 'no_warnings': True, 'skip_download': True,
            'extract_flat': True, 'playlistend': 40, 'ignoreerrors': True,
            'logger': _QuietLogger(),
        }
        with yt_dlp.YoutubeDL(ydl_opts_list) as ydll:
            info = ydll.extract_info(canal_url, download=False) or {}

        for entry in (info.get('entries') or []):
            vid_url = (
                entry.get('url')
                or entry.get('webpage_url')
                or (f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') else None)
            )
            if not vid_url or vid_url in seen:
                continue
            seen.add(vid_url)

            # 2) Metadados completos do vídeo (sem download)
            ydl_opts_video = {
                'quiet': True, 'no_warnings': True, 'skip_download': True,
                'ignore_no_formats_error': True, 'extractor_retries': 2,
                'logger': _QuietLogger(),
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts_video) as ydv:
                    vinfo = ydv.extract_info(vid_url, download=False) or {}
            except Exception:
                continue

            # Título "limpo"
            titulo_full = (vinfo.get('title') or entry.get('title') or '').strip()
            titulo_raw = titulo_full.replace('AO VIVO: ', '').split('|')[0].strip()
            titulo = normalizar_titulo_evento(titulo_raw)

            # ======= Detecção Brasileirão/rodada (usando título + descrição do vinfo) =======
            descricao = (vinfo.get('description') or '').strip()
            info_champ = parse_youtube_title(titulo_full, descricao)

            # =========================
            # FILTRO DE CAMPEONATO
            # =========================
            if not (
                (info_champ.get("is_brasileirao") and info_champ.get("year") == "2026") or
                info_champ.get("is_copa_mundo") or
                (info_champ.get("is_paulista") and info_champ.get("year") == "2026")
            ):
                continue
            # =========================
            # NOME DO CAMPEONATO
            # =========================
            if info_champ.get("is_copa_mundo"):
                champ = (
                    f'COPA DO MUNDO FIFA {info_champ["year"]}'
                    if info_champ.get("year")
                    else 'COPA DO MUNDO FIFA'
                )

            elif info_champ.get("is_paulista"):
                champ = (
                    f'PAULISTÃO {info_champ["year"]}'
                    if info_champ.get("year")
                    else 'PAULISTÃO'
                )

            else:
                champ = f'BRASILEIRAO {info_champ["year"]}'

            # ======= Timestamp (UTC) -> local =======
            ts = (vinfo.get('scheduled_start_time') or
                  vinfo.get('release_timestamp') or
                  vinfo.get('timestamp'))

            if not ts:
                ds = vinfo.get('release_date') or vinfo.get('upload_date')
                if ds and len(ds) == 8:
                    try:
                        ts = int(datetime.strptime(ds, '%Y%m%d').replace(tzinfo=timezone.utc).timestamp())
                    except Exception:
                        ts = None
            if not ts:
                continue

            try:
                dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except Exception:
                continue

            # só futuros (ou lives marcadas como "is_upcoming")
            live_status = vinfo.get('live_status')
            dt_local = dt_utc.astimezone()
            
            # FILTRO DE DATA UI
            if dt_local.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() < data_inicio_obj.timestamp():
                continue

            if live_status != 'is_upcoming' and dt_utc <= datetime.now(timezone.utc):
                continue
            eventos_futuros.append((
                champ,
                titulo,
                vid_url,
                dt_local.strftime('%d/%m/%Y'),
                dt_local.strftime('%H:%M')
            ))

        # opcional: ordenar por data/hora
        # eventos_futuros.sort(key=lambda x: (x[3], x[4]))

        return eventos_futuros

    except Exception as e:
        logging.error(f"Erro ocorrido na coleta do YouTube: {e}")
        try:
            habilita_botoes()
        except Exception:
            pass
        return None

def _to_bool(v):
    # aceita: "true"/"false", "1"/"0", True/False, 1/0, None
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def carrega_config_xml():
    try:
        dados = ler_arquivo_xml("config.xml")
        if not dados:
            return

        # =========================
        # ENTRIES
        # =========================
        email_entry.delete(0, END)
        refresh_entry.delete(0, END)
        entry_email2.delete(0, END)

        email_entry.insert(END, dados.get("emails", ""))
        refresh_entry.insert(END, dados.get("refresh", ""))
        entry_email2.insert(END, dados.get("hora_automatico", ""))

        # =========================
        # CHECKBOXES PRINCIPAIS
        # =========================
        checkbox_ema.set(1 if _to_bool(dados.get("check_automatico_Email")) else 0)
        checkbox_grid.set(1 if _to_bool(dados.get("check_automatico_Evento")) else 0)
        checkbox_busca.set(1 if _to_bool(dados.get("somente_relatorio")) else 0)

        # =========================
        # PLATAFORMAS (XML → UI)
        # =========================
        mapa_plataformas = {
            "Amazon Prime": "plataforma_prime",
            "Disney": "plataforma_disney",
            "Cazé TV": "plataforma_caze",
            "Dazn": "plataforma_dazn",
            "Max": "plataforma_max",
            "CBF": "plataforma_cbf",
        }

        for nome_ui, chave_xml in mapa_plataformas.items():
            ativo = _to_bool(dados.get(chave_xml))
            if nome_ui in checkbox_vars_plat:
                checkbox_vars_plat[nome_ui].set(ativo)
            if nome_ui in checkbox_states_plat:
                checkbox_states_plat[nome_ui] = ativo

        update_combobox_text_plat()

        # =========================
        # CAMPEONATOS (XML → UI)
        # =========================
        camp_saved = dados.get("camp_configs", {})
        for camp_name, val_str in camp_saved.items():
            ativo_camp = _to_bool(val_str)
            if camp_name in checkbox_vars_camp:
                checkbox_vars_camp[camp_name].set(ativo_camp)
                checkbox_states_camp[camp_name] = ativo_camp
        
        update_combobox_text_camp()

    except Exception as e:
        logging.exception(f"Erro ao carregar config.xml: {e}")

def update_combobox_text_plat():
    selecionadas = [
        nome for nome, var in checkbox_vars_plat.items()
        if var.get()
    ]
    if selecionadas:
        combo_plat.set(", ".join(selecionadas))
    else:
        combo_plat.set("Selecione plataformas")

def is_selected_camp(option):
    return checkbox_states_camp.get(option, False)

def is_selected_plat(option):
    var = checkbox_vars_plat.get(option)
    return var.get() if var else False
    
def ler_arquivo_xml(nome_arquivo):
    try:
        # Carregar e analisar o arquivo XML
        tree = ET.parse(nome_arquivo)
        root = tree.getroot()

        # Extrair usuário e senha
        def safe_find(tag, default=""):
            elem = root.find(tag)
            return elem.text if elem is not None else default

        usuario_prime = descriptografar(safe_find("usuario_prime"))
        senha_prime = descriptografar(safe_find("senha_prime"))
        usuario_disney = descriptografar(safe_find("usuario_disney"))
        senha_disney = descriptografar(safe_find("senha_disney"))
        usuario_max = descriptografar(safe_find("usuario_max"))
        senha_max = descriptografar(safe_find("senha_max"))
        
        emails = safe_find("emails")
        refresh = safe_find("refresh", "20")
        hora_automatico = safe_find("hora_automatico", "08:00")
        check_automatico_Email = safe_find("check_automatico_Email", "false")
        check_automatico_Evento = safe_find("check_automatico_Evento", "false")
        somente_relatorio = safe_find("somente_relatorio", "false")
        
        plataforma_dazn = safe_find("plataforma_dazn", "false")
        plataforma_prime = safe_find("plataforma_prime", "false")
        plataforma_disney = safe_find("plataforma_disney", "false")
        plataforma_max = safe_find("plataforma_max", "false")
        plataforma_caze = safe_find("plataforma_caze", "false")
        plataforma_cbf = safe_find("plataforma_cbf", "false")
        
        # Campeonatos
        camp_configs = {}
        options_camp = ["Brasileirão serie A", "Brasileirão serie B", "Copa do Brasil", "Copa do Mundo", "Mundial de Clubes FIFA", "Campeonato Paulista", "CONMEBOL Libertadores", "CONMEBOL Sudamericana"]
        for opt in options_camp:
            tag_name = "camp_" + opt.lower().replace(" ", "_").replace("ã", "a").replace("õ", "o")
            camp_configs[opt] = safe_find(tag_name, "true")

        # Retornar os dados como um dicionário
        return {
            "usuario_prime": usuario_prime,
            "senha_prime": senha_prime,
            "usuario_disney": usuario_disney,
            "senha_disney": senha_disney,
            "usuario_max": usuario_max,
            "senha_max": senha_max,
            "emails": emails,
            "refresh": refresh,
            "hora_automatico": hora_automatico,
            "check_automatico_Email": check_automatico_Email,
            "check_automatico_Evento": check_automatico_Evento,
            "somente_relatorio": somente_relatorio,
            "plataforma_dazn": plataforma_dazn,
            "plataforma_prime": plataforma_prime,
            "plataforma_disney": plataforma_disney,
            "plataforma_max": plataforma_max,
            "plataforma_caze": plataforma_caze,
            "plataforma_cbf": plataforma_cbf,
            "camp_configs": camp_configs
        }
    except FileNotFoundError:

        text=f"Arquivo '{nome_arquivo}' não encontrado."
        pass
        return None
    except ET.ParseError:
        text="Erro ao analisar o XML. Verifique o formato do arquivo."
        pass
        return None
    except Exception as e: 
        logging.error(f"Erro ocorrido: {e}")
        habilita_botoes()
        return {}

def criar_arquivo_xml(nome_arquivo, emails, refresh, hora_automatico, check_automatico_Email, check_automatico_Evento, somente_relatorio):
    # Se o arquivo existir, carregamos
    if os.path.exists(nome_arquivo):
        tree = ET.parse(nome_arquivo)
        root = tree.getroot()
    else:
        root = ET.Element("credenciais")
        tree = ET.ElementTree(root)

    def set_tag(tag, value):
        elem = root.find(tag)
        if elem is None:
            elem = ET.SubElement(root, tag)
        elem.text = value

    # Atualiza ou cria apenas os campos necessários
    set_tag("emails", emails)
    set_tag("refresh", refresh)
    set_tag("hora_automatico", hora_automatico)
    set_tag("check_automatico_Email", check_automatico_Email)
    set_tag("check_automatico_Evento", check_automatico_Evento)
    set_tag("somente_relatorio", somente_relatorio)

    # Plataformas (Força sincronização com checkbox_vars_plat)
    for plat in ["Dazn", "Amazon Prime", "Cazé TV", "Disney", "Max", "CBF"]:
        chave = "plataforma_" + plat.lower().replace(" ", "_").replace("cazé", "caze")
        val = "true" if is_selected_plat(plat) else "false"
        set_tag(chave, val)

    # Campeonatos
    options_camp = ["Brasileirão serie A", "Brasileirão serie B", "Copa do Brasil", "Copa do Mundo", "Mundial de Clubes FIFA", "Campeonato Paulista", "CONMEBOL Libertadores", "CONMEBOL Sudamericana"]
    for opt in options_camp:
        tag_name = "camp_" + opt.lower().replace(" ", "_").replace("ã", "a").replace("õ", "o")
        val = "true" if is_selected_camp(opt) else "false"
        set_tag(tag_name, val)

    # Salva no mesmo arquivo
    tree.write(nome_arquivo, encoding="utf-8", xml_declaration=True)
    logging.info(f"Arquivo XML '{nome_arquivo}' atualizado com sucesso!")

def validar_hora_minuto(texto):
    """ Verifica se o texto inserido está no formato HH:MM """
    global _ultima_janela_envio
    padrao = r"^(?:[01]\d|2[0-3]):[0-5]\d$"  # Permite 00:00 a 23:59
    if re.match(padrao, texto):
        entry_email2.config(bg="lightgreen")  # Verde se for válido
        # Se o usuário alterou o horário, resetamos a última janela para permitir teste imediato
        _ultima_janela_envio = datetime.min
    else:
        entry_email2.config(bg="lightcoral")  # Vermelho se for inválido




def tarefa_diaria():
    global thread_em_execucao
    if thread_em_execucao:
        logging.info("[INFO] Já está em execução. Ignorado.")
        return
    thread_em_execucao = True
    try:
        
        # =====================================================
        # MODO SOMENTE RELATORIO
        # =====================================================
        if checkbox_busca.get():
            logging.info("[MODO] Somente relatório ativo")

            try:
                preparar_chrome_esquerda_para_relatorio()
            except Exception as e:
                logging.error(f"[RELATORIO] Falha ao preparar Chrome: {e}")     
                return
        
        desabilita_botoes()
        logging.info(f"Executando atividades agendadas. {datetime.now()}")
        try:
            label_toolbar.config(text=f"Atividades agendadas em execução: {datetime.now().strftime('%H:%M:%S')}")
        except Exception:
            pass

        # Só limpa quando realmente for buscar de novo
        if checkbox_grid.get():
            limpar_treeview()
            run_busca_eventos(ignorar_trava=True)

        # Envia relatório com o que houver na grade
        if checkbox_ema.get():
            if tree.get_children():
                enviar_email()
                preencher_sharepoint()
            else:
                logging.warning("Tentativa de envio de e-mail sem dados no treeview")
                try:
                    label_toolbar.config(text="Nenhum dado encontrado para enviar.")
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Erro em tarefa_diaria: {str(e)}", exc_info=True)
    finally:
        habilita_botoes()
        thread_em_execucao = False

colunas_excluidas = ["Navegador", "Usuario", "Senha"]

def preencher_sharepoint():
    from sharepoint_client import push_events_from_tuples

    # Garante padronização canônica e remoção de duplicatas antes de enviar ao SharePoint
    try:
        padronizar_nomes_grid(tree)
        remover_duplicatas(tree)
    except Exception:
        pass

    # Filtro de segurança para evitar NoneType
    rows = [tree.item(iid, "values") for iid in tree.get_children()]
    rows = [r for r in rows if r and len(r) >= 8]

    if not rows:
        logging.warning("Não há linhas válidas no grid para enviar ao SharePoint.")
        try:
            label_toolbar.config(text="Não há linhas válidas no grid para enviar ao SharePoint.")
        except Exception:
            pass
        return

    try:
        result = push_events_from_tuples(rows)
    except Exception as e:
        logging.exception("Erro em preencher_sharepoint (push_events_from_tuples)")
        try:
            label_toolbar.config(text=f"Erro no SharePoint: {e}")
        except Exception:
            pass
        return

    origem = "Direto (Graph API)" if result.get("source") == "direct_graph_api" else "Power Automate (Fallback)"
    msg = (
        f"SharePoint ({origem}):\n"
        f"  Total: {result.get('total')}\n"
        f"  Inseridos: {result.get('inserted')}\n"
        f"  Já existiam: {result.get('skipped_existing')}\n"
        f"  Erros: {len(result.get('errors', []))}"
    )
    logging.info(msg)
    try:
        label_toolbar.config(text=f"SharePoint ({origem}): Inseridos: {result.get('inserted')}, Já existiam: {result.get('skipped_existing')}")
    except Exception:
        pass


def extrair_dados_treeview(tree):
    """
    Extrai os dados do Treeview e monta um e-mail HTML completo com tabela estilizada,
    compatível com clientes de e-mail como Outlook e Gmail.
    """
    colunas = [col for col in tree["columns"] if col not in colunas_excluidas]

    # Cabeçalhos da tabela
    cabecalhos_html = ""
    for col in colunas:
        cabecalhos_html += (
            f"<th style='padding: 10px 14px; background-color: #2e7d32; color: #ffffff; "
            f"font-family: Arial, sans-serif; font-size: 13px; font-weight: bold; "
            f"text-align: center; border: 1px solid #1b5e20; white-space: nowrap;'>"
            f"{tree.heading(col)['text']}</th>"
        )

    # Linhas da tabela
    linhas_html = ""
    for i, item in enumerate(tree.get_children()):
        cor_fundo = "#f1f8e9" if i % 2 == 0 else "#ffffff"
        linhas_html += f"<tr style='background-color: {cor_fundo};'>"
        for col in colunas:
            valor = tree.set(item, col)
            # Se parecer URL, torna clicável
            if valor.startswith("http://") or valor.startswith("https://"):
                valor_celula = (
                    f"<a href='{valor}' style='color: #1565c0; text-decoration: underline;'>{valor}</a>"
                )
            else:
                valor_celula = valor
            linhas_html += (
                f"<td style='padding: 8px 12px; font-family: Arial, sans-serif; font-size: 12px; "
                f"color: #212121; border: 1px solid #c8e6c9; vertical-align: middle;'>"
                f"{valor_celula}</td>"
            )
        linhas_html += "</tr>"

    from datetime import datetime
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Relatório de Eventos - Streaming</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color: #f5f5f5; padding: 30px 0;">
    <tr>
      <td align="center">
        <table width="900" cellpadding="0" cellspacing="0" border="0"
               style="background-color: #ffffff; border-radius: 8px;
                      box-shadow: 0 2px 8px rgba(0,0,0,0.12); overflow: hidden;">

          <!-- Cabeçalho -->
          <tr>
            <td style="background-color: #1b5e20; padding: 24px 30px;">
              <h1 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: bold;
                          font-family: Arial, sans-serif;">
                📺 Relatório dos Próximos Eventos no Streaming
              </h1>
              <p style="margin: 6px 0 0 0; color: #a5d6a7; font-size: 13px;">
                Gerado automaticamente em {data_geracao}
              </p>
            </td>
          </tr>

          <!-- Tabela de dados -->
          <tr>
            <td style="padding: 20px 20px 10px 20px; overflow-x: auto;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="border-collapse: collapse; min-width: 600px;">
                <thead>
                  <tr style="background-color: #2e7d32;">
                    {cabecalhos_html}
                  </tr>
                </thead>
                <tbody>
                  {linhas_html}
                </tbody>
              </table>
            </td>
          </tr>

          <!-- Rodapé -->
          <tr>
            <td style="background-color: #e8f5e9; padding: 14px 30px; border-top: 1px solid #c8e6c9;">
              <p style="margin: 0; font-size: 11px; color: #555555; font-family: Arial, sans-serif;">
                Este e-mail foi gerado automaticamente pelo <strong>Streaming Scheduler</strong>.
                Não responda a esta mensagem.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return html

def validar_emails(email_text):
    """ Separa e valida os e-mails digitados no Entry. """
    emails = [email.strip() for email in email_text.split(";")]  # Separar por ";"
    padrao = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    emails_validos = [email for email in emails if re.match(padrao, email)]
    emails_invalidos = [email for email in emails if not re.match(padrao, email)]

    if emails_invalidos:
        email_entry.config(bg="lightcoral")  # Vermelho se houver e-mails inválidos
        text=f"E-mails inválidos: {', '.join(emails_invalidos)}"
        return None
    else:
        email_entry.config(bg="lightgreen")  # Verde se todos forem válidos
        text="Todos os e-mails são válidos!"
        return emails
    

def load_auth():
    """
    Carrega as credenciais do arquivo auth.xml
    Retorna um dicionário com 'email' e 'senha' ou None se o arquivo não existir
    """
    cwd = os.path.realpath('.')
    file = "auth.xml"
    auth_file = os.path.join(cwd,file)
  
    
    try:
       
        tree = ET.parse(auth_file)
        root = tree.getroot()
        return {
    'email': descriptografar(root.find('email').text),
    'senha': descriptografar(root.find('senha').text)
}
    except Exception as e:
        logging.error(f"Erro ao ler auth.xml: {str(e)}")
        habilita_botoes()
        return None

def save_auth(email, senha):
    """
    Salva as credenciais no arquivo auth.xml com criptografia
    """
    try:
        auth = ET.Element('auth')
        ET.SubElement(auth, 'email').text = criptografar(email)
        ET.SubElement(auth, 'senha').text = criptografar(senha)

        with open('auth.xml', 'wb') as f:
            tree = ET.ElementTree(auth)
            tree.write(f, encoding='utf-8', xml_declaration=True)

        os.chmod('auth.xml', 0o600)  # Segurança em Unix
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar auth.xml: {str(e)}")
        habilita_botoes()
        return False
    

def _hash_corpo(corpo: str) -> str:
    return hashlib.sha256(corpo.encode("utf-8", errors="ignore")).hexdigest()

def enviar_email(forcar: bool = False):
    """
    Envia o e-mail com o conteúdo do Treeview.
    - Automático (forcar=False): envia no máximo 1x por dia (idempotência diária) e respeita cooldown.
    - Manual (forcar=True): envia sempre, ignorando cooldown e idempotência diária.
      Ainda assim, após enviar, atualiza os marcadores para que o automático não duplique no mesmo dia.
    """
    import smtplib
    import logging
    from datetime import datetime, timedelta, date
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    global _ultimo_hash_enviado, _ultima_janela_envio

    # Evita concorrência (já existe em seu código como Lock global)
    if not _lock_envio_email.acquire(blocking=False):
        logging.info("Envio de e-mail já em andamento. Ignorado.")
        return

    try:
        agora = datetime.now()

        # Validação de destinatários
        try:
            destinatarios = validar_emails(email_entry.get())
        except Exception:
            destinatarios = []
        if not destinatarios:
            try:
                 label_toolbar.config(text="Nenhum e-mail válido fornecido.")
            except Exception:
                pass
            logging.info("Nenhum e-mail válido fornecido; envio ignorado.")
            return

        # Extrai conteúdo do Treeview (em HTML no seu projeto)
        corpo_email = extrair_dados_treeview(tree)
        if not corpo_email or not str(corpo_email).strip():
            try:
                 label_toolbar.config(text="Nenhum conteúdo para enviar.")
            except Exception:
                pass
            logging.info("Nenhum conteúdo para enviar; envio ignorado.")
            return

        # Cooldown somente para o automático
        if not forcar:
            try:
                if (agora - _ultima_janela_envio) < timedelta(minutes=_COOLDOWN_MIN):
                    logging.info("Dentro do cooldown; envio automático ignorado.")
                    return
            except Exception:
                # Se variável ainda não estiver inicializada corretamente, segue fluxo
                pass

        # Idempotência DIÁRIA: inclui a data no hash para bloquear apenas dentro do mesmo dia
        # (No modo manual, calculamos do mesmo jeito para atualizar o marcador após envio.)
        hash_atual = _hash_corpo(f"{date.today().isoformat()}|{corpo_email}")

        if not forcar and _ultimo_hash_enviado == hash_atual:
            logging.info("Conteúdo idêntico já enviado hoje; envio automático ignorado.")
            return

        # Monta a mensagem
        try:
            credenciais = load_auth()  # seu método de leitura de auth
        except Exception as e:
            logging.error(f"Falha ao carregar credenciais de e-mail: {e}")
            try:
                 label_toolbar.config(text="Falha ao carregar credenciais de e-mail.")
            except Exception:
                pass
            return

        config = {
            "remetente": credenciais["email"],
            "senha": credenciais["senha"],
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "timeout": 30,
            "assunto": "Relatório dos próximos eventos no streaming",
        }

        msg = MIMEMultipart()
        msg["From"] = config["remetente"]
        msg["To"] = ", ".join(destinatarios)
        msg["Subject"] = config["assunto"]
        msg.attach(MIMEText(corpo_email, "html"))

        # Envia:
        # - Manual: sempre envia (forcar=True).
        # - Automático: envia somente se a flag da UI (checkbox_ema) estiver ligada.
        if forcar or checkbox_ema.get():
            try:
                with smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=config["timeout"]) as servidor:
                    servidor.starttls()
                    servidor.login(config["remetente"], config["senha"])
                    servidor.sendmail(config["remetente"], destinatarios, msg.as_string())
            except smtplib.SMTPException as e:
                logging.error(f"Erro SMTP ao enviar e-mail: {e}")
                
                label_toolbar.config(text=f"Erro SMTP ao enviar e-mail: {e}")
                return
        else:
            # Automático desativado — não envia e apenas informa
            logging.info("Envio automático desativado (checkbox).")
            try:
                 label_toolbar.config(text="Envio automático desativado (checkbox desligado).")
            except Exception:
                pass
            return

        # Sucesso
        try:
            data_hora = agora.strftime("%d/%m/%Y %H:%M:%S")
            label_toolbar.config(text=f"E-mail enviado com sucesso em: {data_hora}")
        except Exception:
            pass
        logging.info(f"E-mail enviado para: {', '.join(destinatarios)}")

        # Atualiza controles para bloquear reenvio automático no mesmo dia
        _ultima_janela_envio = agora
        _ultimo_hash_enviado = hash_atual

    except Exception as e:
        logging.exception(f"Erro inesperado em enviar_email: {e}")
        try:
             text=f"Erro inesperado ao enviar e-mail: {e}"
        except Exception:
            pass
    finally:
        try:
            _lock_envio_email.release()
        except Exception:
            pass
        try:
            habilita_botoes()
        except Exception:
            pass
        
def limpar_arquivo_periodicamente(arquivo):
    """Executa uma thread que verifica e limpa o arquivo a cada 5 dias."""

    def verificar_e_limpar():
  # Aguarda 24 horas antes de verificar novamente
        while True:
            if os.path.exists(arquivo):
                ultima_modificacao = datetime.fromtimestamp(os.path.getmtime(arquivo))
                if datetime.now() - ultima_modificacao >= timedelta(days=15):
                    with open(arquivo, "w") as f:
                        f.write("")  # Limpa o arquivo
                    text=f"O arquivo '{arquivo}' foi limpo em: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} "
             
            else:
                with open(arquivo, "w") as f:
                    f.write("")  # Cria o arquivo vazio
                text=f"O arquivo '{arquivo}' não existia, então foi criado e limpo!"

            time.sleep(24 * 60 * 60)  # Aguarda 24 horas antes de verificar novamente

    # Criando a thread que roda em segundo plano
    thread = threading.Thread(target=verificar_e_limpar, daemon=True)
    thread.start()

def get_eventos():
    
    desabilita_botoes()
    iniciar_thread(run_busca_eventos)
    
def fechar_instancia(nome_programa):
    for processo in psutil.process_iter(attrs=["name", "pid"]):
        if processo.info["name"] == nome_programa:
            text=f"Fechando instância existente de {nome_programa} (PID: {processo.info['pid']})..."
            psutil.Process(processo.info["pid"]).terminate()  # Finaliza o processo
            time.sleep(2)  # Aguarda para garantir que o processo foi encerrado


def _abrir_chrome(porta: str, profile_dir: str) -> None:
    try:
        os.makedirs(profile_dir, exist_ok=True)
        chrome_path = shutil.which("chrome") or shutil.which("chrome.exe")
        if not chrome_path:
            c1 = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            c2 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            c3 = os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\%USERNAME%\AppData\Local"),
                              "Google", "Chrome", "Application", "chrome.exe")
            chrome_path = c1 if os.path.exists(c1) else (c2 if os.path.exists(c2) else c3)

        subprocess.Popen([
            chrome_path,
            "--remote-debugging-address=127.0.0.1",     # <<< adição
            f"--remote-debugging-port={porta}",
            f"--user-data-dir={profile_dir}",
            "--profile-directory=Default",
            "--disable-features=SkipProfilePicker",
            "--no-first-run", "--no-default-browser-check"
        ])
    except Exception as e:
        logging.error(f"Falha ao abrir Chrome na porta {porta}: {e}")

def fechar_chrome_por_porta(porta_debug):
    """Finaliza apenas a instância do Chrome rodando na porta de depuração especificada."""
    import psutil
    target = f"--remote-debugging-port={porta_debug}"
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline') or []
                if any(target in arg for arg in cmdline):
                    logging.info(f"Finalizando Chrome na porta {porta_debug} (PID: {proc.info['pid']})")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue



def verificar_chrome_debug(porta_debug: str) -> bool:
    """
    Verifica se há Chrome DevTools na porta:
      - Se já houver DevTools: retorna True.
      - Se não houver DevTools: abre (9222/9224) e espera alguns segundos.
      - Retorna True somente quando /json/version trouxer webSocketDebuggerUrl.
    """
    import socket, json, time, logging

    def set_label(msg: str):
        try:
            label_toolbar.after(0, lambda: label_toolbar.config(text=msg))
        except Exception:
            pass

    def devtools_ok(porta: int, t_conn=0.5, t_read=0.8) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=t_conn) as s:
                s.settimeout(t_read)
                s.sendall(
                    f"GET /json/version HTTP/1.1\r\nHost: 127.0.0.1:{porta}\r\nConnection: close\r\n\r\n".encode("ascii")
                )
                data = s.recv(8192)
            head, _, body = data.partition(b"\r\n\r\n")
            if b" 200 " not in head:
                return False
            j = json.loads(body.decode("utf-8", "ignore") or "{}")
            return isinstance(j, dict) and "webSocketDebuggerUrl" in j
        except Exception:
            return False

    # normaliza porta
    try:
        porta = int(str(porta_debug).strip())
    except Exception:
        porta = 9222

    # 1) já está pronto?
    if devtools_ok(porta):
        set_label(f"Chrome já em depuração na porta {porta}.")
        return True

    # 2) não está pronto -> abrir e aguardar
    set_label(f"Iniciando Chrome em depuração na porta {porta}…")
    try:
        if porta == 9222:
            update_chrome1()
        elif porta == 9224:
            update_chrome2()
        else:
            logging.error(f"Porta não suportada: {porta}")
            set_label(f"Porta {porta} não suportada.")
            return False
    except Exception as e:
        logging.error(f"Falha ao iniciar Chrome na porta {porta}: {e}")
        set_label(f"Falha ao iniciar Chrome na porta {porta}.")
        return False

    # 3) espera curta até o DevTools responder
    deadline = time.time() + 10  # ~10s
    while time.time() < deadline:
        if devtools_ok(porta):
            set_label(f"Chrome pronto na porta {porta}.")
            return True
        time.sleep(0.25)

    logging.error(f"Chrome não subiu DevTools na porta {porta} a tempo.")
    set_label(f"Chrome não subiu DevTools na porta {porta}.")
    return False

    

def deep_normalize_match(match_name):
    """
    Normaliza nomes de jogos de forma profunda para detectar duplicatas como
    'Vasco x São Paulo' vs 'Vasco da Gama x São Paulo FC'.
    Suporta variações de acentos, sufixos (E.C, F.C, S.A.F), siglas e nomes curtos/longos.
    """
    import unicodedata
    import re
    
    def norm_team(t):
        if not t: return ""
        t = str(t).lower()
        nfkd = unicodedata.normalize('NFD', t)
        t = "".join(c for c in nfkd if unicodedata.category(c) != 'Mn')
        t = t.replace("-", " ").replace(".", " ").replace("_", " ")
        
        # 1. Limpeza de prefixos/sufixos e siglas institucionais
        prefixes = [
            r"\besporte clube\b", r"\be c\b", r"\bf c\b", r"\bfutebol clube\b",
            r"\bfc\b", r"\bec\b", r"\bsaf\b", r"\bclube de regatas\b",
            r"\bsociedade esportiva\b", r"\bassociacao atletica\b",
            r"\bgremio recreativo\b", r"\bgremio esportivo\b",
            r"\bsport club\b", r"\bclube atletico\b", r"\bassociacao\b",
            r"\bsc\b", r"\bse\b", r"\bcr\b", r"\bfr\b", r"\baf\b", r"\bca\b", r"\baa\b"
        ]
        for p in prefixes:
            t = re.sub(p, " ", t)
        t = re.sub(r"\s+", " ", t).strip()

        # 2. Mapeamento canônico exato de apelidos e variações dos clubes
        replacements = [
            # Vasco
            (r"\b(vasco da gama|cr vasco da gama|vasco)\b", "vasco"),
            # Athletico-PR
            (r"\b(athletico paranaense|atletico paranaense|athletico pr|atletico pr|cap|athletico)\b", "athletico pr"),
            # Atlético-MG
            (r"\b(atletico mineiro|atletico mg|cam|galo)\b", "atletico mg"),
            # Atlético-GO
            (r"\b(atletico goianiense|atletico go|acg|dragao)\b", "atletico go"),
            # Bragantino
            (r"\b(red bull bragantino|rb bragantino|bragantino|massa bruta)\b", "bragantino"),
            # Corinthians
            (r"\b(corinthians paulista|corinthians|sccp|timao)\b", "corinthians"),
            # São Paulo
            (r"\b(sao paulo|spfc)\b", "sao paulo"),
            # Palmeiras
            (r"\b(palmeiras|verdao)\b", "palmeiras"),
            # Flamengo
            (r"\b(flamengo rj|flamengo|mengao|fla)\b", "flamengo"),
            # Fluminense
            (r"\b(fluminense rj|fluminense|flu)\b", "fluminense"),
            # Botafogo-SP vs Botafogo-RJ
            (r"\b(botafogo de ribeirao preto|botafogo sp)\b", "botafogo sp"),
            (r"\b(botafogo fr|botafogo rj|botafogo|fogao|bota)\b", "botafogo"),
            # Novorizontino (antes de Grêmio)
            (r"\b(gremio novorizontino|novorizontino sp|novorizontino)\b", "novorizontino"),
            # Grêmio
            (r"\b(gremio fbpa|gremio porto alegrense|gremio rsg|gremio)\b", "gremio"),
            # Inter de Limeira vs Internacional
            (r"\b(internacional de limeira|inter de limeira|inter limeira)\b", "inter limeira"),
            (r"\b(internacional rs|inter de porto alegre|inter rs|internacional|inter)\b", "internacional"),
            # Cruzeiro
            (r"\b(cruzeiro mg|cruzeiro)\b", "cruzeiro"),
            # Juventude
            (r"\b(juventude rs|juventude)\b", "juventude"),
            # Fortaleza
            (r"\b(fortaleza ce|fortaleza)\b", "fortaleza"),
            # Ceará
            (r"\b(ceara ce|ceara|vozao)\b", "ceara"),
            # Bahia
            (r"\b(bahia ba|bahia|esquadrao)\b", "bahia"),
            # Vitória
            (r"\b(vitoria ba|vitoria|leao da barra)\b", "vitoria"),
            # Cuiabá
            (r"\b(cuiaba mt|cuiaba|dourado)\b", "cuiaba"),
            # Criciúma
            (r"\b(criciuma sc|criciuma|tigre)\b", "criciuma"),
            # Coritiba
            (r"\b(coritiba fcf|coritiba pr|coritiba|coxa)\b", "coritiba"),
            # Goiás
            (r"\b(goias go|goias|esmeraldino)\b", "goias"),
            # Sport
            (r"\b(sport club do recife|sport recife|sport pe|sport|leao da ilha)\b", "sport"),
            # América-MG vs América-RN
            (r"\b(america de natal|america rn)\b", "america rn"),
            (r"\b(america mineiro|america mg|coelho)\b", "america mg"),
            # Chapecoense
            (r"\b(chapecoense af|chapecoense sc|chapecoense|chape)\b", "chapecoense"),
            # Mirassol
            (r"\b(mirassol sp|mirassol)\b", "mirassol"),
            # Operário-PR
            (r"\b(operario ferroviario|operario pr|operario)\b", "operario pr"),
            # Vila Nova
            (r"\b(vila nova go|vila nova|tigrao)\b", "vila nova"),
            # Ponte Preta
            (r"\b(ponte preta sp|ponte preta|macaca)\b", "ponte preta"),
            # Guarani
            (r"\b(guarani sp|guarani|bugre)\b", "guarani"),
            # Amazonas
            (r"\b(amazonas am|amazonas|onca)\b", "amazonas"),
            # Brusque
            (r"\b(brusque sc|brusque|quadricolor)\b", "brusque"),
            # Ituano
            (r"\b(ituano sp|ituano|galo de itu)\b", "ituano"),
            # Paysandu
            (r"\b(paysandu pa|paysandu|papao)\b", "paysandu"),
            # Remo
            (r"\b(clube do remo|remo pa|remo|leao azul)\b", "remo"),
            # Avaí
            (r"\b(avai sc|avai|leao da ilha)\b", "avai"),
            # CRB / CSA
            (r"\b(clube de regatas brasil|crb al|crb|galo da praia)\b", "crb"),
            (r"\b(centro sportivo alagoano|csa al|csa|azulino)\b", "csa"),
        ]

        for pattern, rep in replacements:
            if re.search(pattern, t):
                t = re.sub(pattern, rep, t)
                break

        return re.sub(r"\s+", " ", t).strip()

    # Garante que o separador seja ' x ' minúsculo para o split
    text_work = re.sub(r'\s+[vVxX]\s+', ' x ', str(match_name))
    parts = text_work.lower().split(" x ")
    
    if len(parts) >= 2:
        t1, t2 = norm_team(parts[0]), norm_team(parts[1])
        # Retorna uma tupla ordenada para garantir que 'A x B' == 'B x A'
        return tuple(sorted([t1, t2]))
    return (norm_team(match_name),)

def canonical_team_name(t):
    if not t: return ""
    original = t.strip()
    
    # Normalização básica para comparação
    t_lower = t.lower()
    t_lower = "".join(c for c in unicodedata.normalize('NFD', t_lower) if unicodedata.category(c) != 'Mn')
    t_lower = t_lower.replace("-", " ").replace(".", " ").replace("_", " ")

    # Remove prefixos inúteis e siglas
    prefixes = [
        r"\besporte clube\b", r"\be c\b", r"\bf c\b", r"\bfutebol clube\b",
        r"\bfc\b", r"\bec\b", r"\bsaf\b", r"\bclube de regatas\b",
        r"\bsociedade esportiva\b", r"\bassociacao atletica\b",
        r"\bgremio recreativo\b", r"\bgremio esportivo\b",
        r"\bsport club\b", r"\bclube atletico\b", r"\bassociacao\b",
        r"\bsc\b", r"\bse\b", r"\bcr\b", r"\bfr\b", r"\baf\b", r"\bca\b", r"\baa\b"
    ]
    t_clean = t_lower
    for p in prefixes:
        t_clean = re.sub(p, " ", t_clean)
    t_clean = re.sub(r'\s+', ' ', t_clean).strip()
    
    # Dicionário de padronização (Formato Bonito Canônico)
    canonical_map = [
        (r"\b(vasco da gama|cr vasco da gama|vasco)\b", "Vasco da Gama"),
        (r"\b(athletico paranaense|atletico paranaense|athletico pr|atletico pr|cap|athletico)\b", "Athletico-PR"),
        (r"\b(atletico mineiro|atletico mg|cam|galo)\b", "Atlético-MG"),
        (r"\b(atletico goianiense|atletico go|acg|dragao)\b", "Atlético-GO"),
        (r"\b(red bull bragantino|rb bragantino|bragantino|massa bruta)\b", "Red Bull Bragantino"),
        (r"\b(corinthians paulista|corinthians|sccp|timao)\b", "Corinthians"),
        (r"\b(sao paulo|spfc)\b", "São Paulo"),
        (r"\b(palmeiras|verdao)\b", "Palmeiras"),
        (r"\b(flamengo rj|flamengo|mengao|fla)\b", "Flamengo"),
        (r"\b(fluminense rj|fluminense|flu)\b", "Fluminense"),
        (r"\b(botafogo de ribeirao preto|botafogo sp)\b", "Botafogo-SP"),
        (r"\b(botafogo fr|botafogo rj|botafogo|fogao|bota)\b", "Botafogo"),
        (r"\b(gremio novorizontino|novorizontino sp|novorizontino)\b", "Novorizontino"),
        (r"\b(gremio fbpa|gremio porto alegrense|gremio rsg|gremio)\b", "Grêmio"),
        (r"\b(internacional de limeira|inter de limeira|inter limeira)\b", "Inter de Limeira"),
        (r"\b(internacional rs|inter de porto alegre|inter rs|internacional|inter)\b", "Internacional"),
        (r"\b(cruzeiro mg|cruzeiro)\b", "Cruzeiro"),
        (r"\b(juventude rs|juventude)\b", "Juventude"),
        (r"\b(fortaleza ce|fortaleza)\b", "Fortaleza"),
        (r"\b(ceara ce|ceara|vozao)\b", "Ceará"),
        (r"\b(bahia ba|bahia|esquadrao)\b", "Bahia"),
        (r"\b(vitoria ba|vitoria|leao da barra)\b", "Vitória"),
        (r"\b(cuiaba mt|cuiaba|dourado)\b", "Cuiabá"),
        (r"\b(criciuma sc|criciuma|tigre)\b", "Criciúma"),
        (r"\b(coritiba fcf|coritiba pr|coritiba|coxa)\b", "Coritiba"),
        (r"\b(goias go|goias|esmeraldino)\b", "Goiás"),
        (r"\b(sport club do recife|sport recife|sport pe|sport|leao da ilha)\b", "Sport"),
        (r"\b(america de natal|america rn)\b", "América-RN"),
        (r"\b(america mineiro|america mg|coelho)\b", "América-MG"),
        (r"\b(chapecoense af|chapecoense sc|chapecoense|chape)\b", "Chapecoense"),
        (r"\b(mirassol sp|mirassol)\b", "Mirassol"),
        (r"\b(operario ferroviario|operario pr|operario)\b", "Operário-PR"),
        (r"\b(vila nova go|vila nova|tigrao)\b", "Vila Nova"),
        (r"\b(ponte preta sp|ponte preta|macaca)\b", "Ponte Preta"),
        (r"\b(guarani sp|guarani|bugre)\b", "Guarani"),
        (r"\b(amazonas am|amazonas|onca)\b", "Amazonas"),
        (r"\b(brusque sc|brusque|quadricolor)\b", "Brusque"),
        (r"\b(ituano sp|ituano|galo de itu)\b", "Ituano"),
        (r"\b(paysandu pa|paysandu|papao)\b", "Paysandu"),
        (r"\b(clube do remo|remo pa|remo|leao azul)\b", "Remo"),
        (r"\b(avai sc|avai|leao da ilha)\b", "Avaí"),
        (r"\b(clube de regatas brasil|crb al|crb|galo da praia)\b", "CRB"),
        (r"\b(centro sportivo alagoano|csa al|csa|azulino)\b", "CSA"),
    ]
    
    # Aplica o mapa para achar o nome bonito
    for pattern, pretty_name in canonical_map:
        if re.search(pattern, t_clean):
            return pretty_name
            
    # Se não achar no mapa, retorna o original formatado como Título
    return original.title()

def prettify_match_name(match_name):
    """
    Recebe um nome de partida possivelmente bagunçado (ex: 'Atlético MG x Juventude')
    e converte para um padrão visual único (ex: 'Atlético-MG x Juventude').
    Isso previne que o SharePoint gere chaves duplicadas (ChaveEvento) devido a variações no nome!
    """
    text_work = re.sub(r'\s+[vVxX]\s+', ' x ', match_name)
    parts = text_work.split(" x ")
    if len(parts) >= 2:
        t1, t2 = canonical_team_name(parts[0]), canonical_team_name(parts[1])
        return f"{t1} x {t2}"
    return canonical_team_name(match_name)

def padronizar_nomes_grid(tree):
    """
    Varre todo o grid e substitui os nomes de partidas pelos nomes canônicos e bonitos.
    Deve ser chamada antes do SharePoint ou da remoção de duplicatas.
    """
    try:
        for item in tree.get_children():
            values = list(tree.item(item, 'values'))
            if len(values) > 1:
                nome_original = str(values[1])
                nome_bonito = prettify_match_name(nome_original)
                if nome_original != nome_bonito:
                    values[1] = nome_bonito
                    tree.item(item, values=values)
    except Exception as e:
        import logging
        logging.error(f"Erro em padronizar_nomes_grid: {e}")

def is_match_already_in_tree(jogo_nome, data_str):
    """
    Verifica se um jogo já existe no Treeview para a mesma data usando match fuzzy.
    """
    if not tree: return False
    
    jogo_norm = deep_normalize_match(jogo_nome)
    
    try:
        for item in tree.get_children():
            values = tree.item(item, "values")
            if len(values) > 2:
                # Compara Jogo (idx 1) e Data (idx 2)
                # Compara Jogo (idx 1) e Data (idx 2) usando normalização profunda
                if deep_normalize_match(str(values[1])) == jogo_norm and str(values[2]) == data_str:
                    return True
    except Exception:
        pass
    return False

def get_latest_cbf_url(comp_type):
    """
    Busca dinamicamente o link mais recente da Tabela Detalhada no site da CBF usando Selenium headless.
    """
    if comp_type == "BSA":
        url = "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/2026"
    elif comp_type == "CDB":
        url = "https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/2026"
    else:
        return None

    logging.info(f"[CBF] Buscando URL dinâmica para {comp_type} em {url}...")
    
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(6) # Aguarda renderização Next.js/React dos links
        
        links = driver.find_elements(By.TAG_NAME, "a")
        for a in links:
            try:
                href = a.get_attribute("href")
                if href and ("Tabela_Detalhada" in href or "tabela_detalhada" in href) and href.endswith(".pdf"):
                    logging.info(f"[CBF] URL dinâmica encontrada para {comp_type}: {href}")
                    return href
            except:
                pass
    except Exception as e:
        logging.error(f"[CBF] Erro ao buscar URL dinâmica da CBF ({comp_type}) usando Selenium: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
                
    # Fallback para URLs atualizadas se a busca falhar ou der erro
    fallbacks = {
        "BSA": "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/Tabela_Detalhada_BSA_2026_06_07_db8090e380.pdf",
        "CDB": "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/Tabela_Detalhada_Copa_do_Brasil_2026_08_07_8dfc6382ed.pdf"
    }
    logging.info(f"[CBF] Usando fallback para {comp_type}: {fallbacks.get(comp_type)}")
    return fallbacks.get(comp_type)

def run_eventos_cbf():
    """
    Nova lógica consolidada para extração via PDF da CBF.
    Utiliza URLs diretas para máxima velocidade ("preenche em segundos").
    """
    logging.info("Iniciando run_eventos_cbf...")
    try:
        label_toolbarprocess.config(text="Atualização CBF (PDF)")
        progresso["value"] = 0
        progresso.pack(side=RIGHT, padx=10, pady=5)
        
        camps_to_process = []
        if is_selected_camp("Brasileirão serie A"):
            url_bsa = get_latest_cbf_url("BSA")
            camps_to_process.append({
                "nome": "Brasileirão Série A",
                "url_pdf": url_bsa
            })
        if is_selected_camp("Copa do Brasil"):
            url_cdb = get_latest_cbf_url("CDB")
            camps_to_process.append({
                "nome": "Copa do Brasil",
                "url_pdf": url_cdb
            })

        if not camps_to_process:
            return

        for camp_info in camps_to_process:
            progresso["value"] += 20
            label_toolbarprocess.config(text=f"Baixando PDF: {camp_info['nome']}")
            
            try:
                # Download ultrarrápido via requests
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                resp = requests.get(camp_info['url_pdf'], headers=headers, verify=False, timeout=15)
                
                if resp.status_code != 200 or len(resp.content) < 5000:
                    logging.warning(f"PDF {camp_info['nome']} indisponível ou inválido (Status: {resp.status_code}, Tamanho: {len(resp.content)})")
                    continue

                pdf_path = f"temp_{camp_info['nome'].replace(' ', '_')}.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(resp.content)
                
                # Parsing do PDF usando o parser já validado
                extracted = parse_cbf_pdf(pdf_path, camp_info['nome'])
                logging.info(f"PDF {camp_info['nome']} extraiu {len(extracted)} jogos totais.")
                
                # Obtendo data inicial da UI para filtro
                try:
                    data_inicio_str = entry_data.get()
                    data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
                except:
                    data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                var_navegador = "Esquerda"
                cont_inseridos = 0
                for ev in extracted:
                    # 🔥 REGRA: Diminuir 1 hora de todos os jogos da CBF (PDF) e ajustar a data se mudar de dia
                    data_ajustada = ev['Data']
                    hora_ajustada = ev['Hora']
                    try:
                        dt_combined = None
                        for fmt_h in ("%H:%M", "%H:%M:%S"):
                            try:
                                dt_combined = datetime.strptime(f"{ev['Data']} {ev['Hora']}", f"%d/%m/%Y {fmt_h}")
                                break
                            except:
                                pass
                        if dt_combined:
                            dt_ajustada = dt_combined - timedelta(hours=1)
                            data_ajustada = dt_ajustada.strftime("%d/%m/%Y")
                            hora_ajustada = dt_ajustada.strftime("%H:%M")
                    except Exception as e:
                        logging.warning(f"Erro ao ajustar data/hora do PDF ({ev['Data']} {ev['Hora']}): {e}")

                    # Filtro de Data (Somente eventos futuros/atuais) usando a data ajustada
                    try:
                        ev_date_obj = datetime.strptime(data_ajustada, "%d/%m/%Y")
                        if ev_date_obj < data_inicio_obj:
                            continue
                    except:
                        continue
                    
                    # 🔥 REGRA DE PRIORIDADE: Se já existir no grid (Selenium), ignora o PDF (compara com data original e ajustada)
                    if is_match_already_in_tree(ev['Jogo'], ev['Data']) or is_match_already_in_tree(ev['Jogo'], data_ajustada):
                        logging.info(f"Ignorando duplicata PDF (Já no grid): {ev['Jogo']} em {ev['Data']} / {data_ajustada}")
                        continue

                    plataformas_evento = [p.strip() for p in ev['TV'].split(',')]
                    # Se 'CBF' estiver selecionado, mostra tudo do PDF da CBF.
                    # Senão, filtra pelas plataformas individuais (Amazon, Cazé, etc)
                    mostrar = is_selected_plat("CBF")
                    if not mostrar:
                        for plat_ev in plataformas_evento:
                            if is_selected_plat(plat_ev):
                                mostrar = True
                                break
                    
                    if mostrar:
                        plat_display = plataformas_evento[0] if plataformas_evento else "CBF"
                        cbf_nome = camp_info['nome']
                        cbf_camp = f"CBF - {cbf_nome}" if "CBF" not in cbf_nome.upper() else cbf_nome
                        jogo_bonito = prettify_match_name(ev['Jogo'])
                        row = (cbf_camp, jogo_bonito, data_ajustada, hora_ajustada, var_navegador, "15", plat_display, camp_info['url_pdf'])
                        tree.insert("", "end", values=row)
                        var_navegador = "Direita" if var_navegador == "Esquerda" else "Esquerda"
                        cont_inseridos += 1
                
                logging.info(f"PDF {camp_info['nome']}: Inseridos {cont_inseridos} jogos após filtro de data.")

            except Exception as e:
                logging.error(f"Erro ao processar PDF {camp_info['nome']}: {e}")

        # --- ADIÇÃO: CBF - Copa do Mundo FIFA 2026 (via Excel Local) ---
        if is_selected_plat("CBF"):
            try:
                xls_path = os.path.join(os.getcwd(), "Tabela_Completa_Copa_Mundo_2026_Fase_Grupos.xlsx")
                if os.path.exists(xls_path):
                    logging.info(f"Processando Tabela Excel CBF - Copa do Mundo FIFA 2026: {xls_path}")
                    import pandas as pd
                    df = pd.read_excel(xls_path)
                    
                    # Identificação de colunas (Data, Hora, Jogo)
                    col_data = next((c for c in df.columns if 'DATA' in str(c).upper()), None)
                    col_hora = next((c for c in df.columns if 'HORA' in str(c).upper()), None)
                    col_jogo = next((c for c in df.columns if 'JOGO' in str(c).upper()), None)
                    
                    if col_data and col_hora and col_jogo:
                        # Data de início para filtro (da UI)
                        try:
                            data_inicio_str = entry_data.get()
                            data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
                        except:
                            data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                        var_navegador_xls = "Esquerda"
                        cont_inseridos_xls = 0
                        
                        for _, row in df.iterrows():
                            data_raw = str(row[col_data]).strip()
                            hora_raw = str(row[col_hora]).strip()
                            jogo_raw = str(row[col_jogo]).strip()
                            
                            if not jogo_raw or jogo_raw == "nan" or jogo_raw == "None": continue

                            # Normalização de data
                            try:
                                if " " in data_raw: data_raw = data_raw.split(" ")[0]
                                if "-" in data_raw:
                                    dt_obj = datetime.strptime(data_raw, "%Y-%m-%d")
                                    data_formatada = dt_obj.strftime("%d/%m/%Y")
                                else:
                                    data_formatada = data_raw
                            except:
                                data_formatada = data_raw
                                
                            # Ajuste de -2 horas conforme solicitado e correção de data se mudar de dia
                            data_ajustada = data_formatada
                            hora_ajustada = hora_raw
                            try:
                                dt_combined = None
                                for fmt_h in ("%H:%M", "%H:%M:%S"):
                                    try:
                                        dt_combined = datetime.strptime(f"{data_formatada} {hora_raw}", f"%d/%m/%Y {fmt_h}")
                                        break
                                    except:
                                        pass
                                if dt_combined:
                                    dt_ajustada = dt_combined - timedelta(hours=2)
                                    data_ajustada = dt_ajustada.strftime("%d/%m/%Y")
                                    hora_ajustada = dt_ajustada.strftime("%H:%M")
                            except Exception as e:
                                logging.warning(f"Erro ao ajustar data/hora em Copa do Mundo Excel ({data_formatada} {hora_raw}): {e}")

                            # Filtro de data futura usando a data ajustada
                            try:
                                ev_date_obj = datetime.strptime(data_ajustada, "%d/%m/%Y")
                                if ev_date_obj < data_inicio_obj:
                                    continue
                            except:
                                pass
                                
                            # 🔥 REGRA DE PRIORIDADE: Se já existir no grid (Selenium), ignora o Excel (compara com data original e ajustada)
                            if is_match_already_in_tree(jogo_raw, data_raw) or is_match_already_in_tree(jogo_raw, data_ajustada):
                                logging.info(f"Ignorando duplicata Excel (Já no grid): {jogo_raw} em {data_raw} / {data_ajustada}")
                                continue

                            # Inserção no grid (Forçando 'Cazé TV' e URL do YouTube)
                            caze_url = "https://www.youtube.com/@CazeTV/streams"
                            jogo_bonito_xls = prettify_match_name(jogo_raw)
                            row_data = ("CBF - Copa do Mundo FIFA 2026", jogo_bonito_xls, data_ajustada, hora_ajustada, var_navegador_xls, "15", "Cazé TV", caze_url)
                            tree.insert("", "end", values=row_data)
                            var_navegador_xls = "Direita" if var_navegador_xls == "Esquerda" else "Esquerda"
                            cont_inseridos_xls += 1
                            
                        logging.info(f"Excel Copa do Mundo: Inseridos {cont_inseridos_xls} jogos.")
                else:
                    logging.warning(f"Arquivo de Tabela da Copa do Mundo não encontrado: {xls_path}")
            except Exception as e:
                logging.error(f"Erro ao processar Excel Copa do Mundo: {e}")

        padronizar_nomes_grid(tree)
        remover_duplicatas(tree)
        progresso["value"] = 100
        label_toolbarprocess.config(text="CBF Atualizado!")
        time.sleep(1)
        progresso.pack_forget()

    except Exception as e:
        logging.error(f"Erro em run_eventos_cbf: {e}")

def parse_cbf_pdf(pdf_path, nome_original):
    """
    Parser refinado e validado para os PDFs da CBF 2026.
    Extrai Jogo, Data, Hora e TV (Amazon Prime / Cazé TV).
    """
    try:
        logging.info(f"Processando PDF CBF: {pdf_path}")
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf_path)
        full_text = ""
        for i in range(len(doc)):
            page = doc.get_page(i)
            textpage = page.get_textpage()
            full_text += textpage.get_text_bounded() + "\n"
            textpage.close()
            page.close()
        doc.close()
        
        if "Copa do Brasil" in nome_original:
            legend = {"3": "Amazon Prime"}
            target_ids = ["3"]
        else: # Brasileirão Série A
            legend = {"4": "Amazon Prime", "5": "Cazé TV"}
            target_ids = ["4", "5"]
        
        lines = full_text.split("\n")
        current_date = ""
        extracted = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
               
            # Procura por data: dd/mm seg|ter|...
            date_match = re.search(r'(\d{2}/\d{2})\s+(?:seg|ter|qua|qui|sex|sáb|sab|dom)', line, re.I)
            if date_match:
                current_date = date_match.group(1) + "/2026"
               
            if " x " in line:
                # Procura por horário: hh:mm
                time_match = re.search(r'(\d{2}:\d{2})', line)
                if time_match:
                    hora = time_match.group(1)
                    
                    # Pula se já tiver placar (jogo passado)
                    if re.search(r'\b\d+\s+x\s+\d+\b', line): continue
                    if re.search(r'\(\d+\)', line): continue
                    
                    parts = line.split(" x ")
                    if len(parts) >= 2:
                        all_nums_pt2 = re.findall(r'\b(\d+)\b', parts[1])
                        relevant_nums = [n for n in all_nums_pt2 if n in target_ids]
                        logging.debug(f"Linha Jogo: {line} | IDs encontrados: {all_nums_pt2} | Relevantes: {relevant_nums}")
                        
                        if not relevant_nums:
                            continue
                        
                        tv_str = ", ".join([legend.get(n, n) for n in relevant_nums])

                    # Limpeza de nomes
                    pt1 = parts[0]
                    # Remove hora se estiver no início do nome do time 1
                    m_time = re.search(r'\d{2}:\d{2}', pt1)
                    if m_time: pt1 = pt1[m_time.end():].strip()
                    # Remove números de ID no início
                    pt1 = re.sub(r'^\d+\s+', '', pt1).strip()
                    # Remove placares entre parênteses
                    pt1 = re.sub(r'\(.*?\)', '', pt1).strip()
                    # Remove UF (estado)
                    pt1 = re.sub(r'\b[A-Z]{2}\b$', '', pt1).strip()
                    pt1 = re.sub(r'\b[A-Z]{2}\b', '', pt1).strip()
                    
                    pt2 = parts[1]
                    pt2 = re.sub(r'\(.*?\)', '', pt2).strip()
                    # Remove UF e tudo que vem depois no time 2 (Estádio, Cidade, Canal)
                    pt2 = re.sub(r'\s[A-Z]{2}\b.*$', '', pt2).strip()
                    jogo_clean = f"{pt1} x {pt2}"
                    
                    extracted.append({
                        "Camp": nome_original, # Mantém o nome limpo aqui
                        "Jogo": jogo_clean,
                        "Data": current_date,
                        "Hora": hora,
                        "TV": tv_str
                    })
        return extracted
    except Exception as e:
        logging.error(f"Erro no parser PDF CBF: {e}")
        return []

def run_eventos_dazn(url_camp, expected_camp="Mundial de Clubes FIFA"):

  try:   
        #  Usa o navegador da esquerda para buscar a lista
        label_toolbarprocess.config(text="Atualização de eventos do Dazn")
        text="Realizando a atualização dos grids com os eventos do Dazn..."
        progresso["value"] = 0
        #    Exibe progressbar
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            text="Chrome (9222) indisponível."
            return
   

        # Configurando as opções do Chrome
        chrome_options = Options()
        chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        service = Service(ChromeDriverManager().install())
        driverchrome1 = webdriver.Chrome(service=service, options=chrome_options)

        #  Cria uma lista para adicionar os items futuramento no treeview
         

        us = get_config_value("usuario_dazn")
        pas = get_config_value("senha_dazn")
           
        csv_list = ()
        list_b = list(csv_list)

        var_navegador = "Esquerda"

        # Abre na url do campeonato em questão selecionado
        text="Abrindo pagina do campeonato..."
        progresso["value"] = progresso["value"] + 5
        logindazn(url_camp,us,pas,driverchrome1,10,"Novos")
        
        text="Limpando o grid..."
        delete_null_items()
       
        text="Atualizando lista do campeonato Dazn..."
        progresso["value"] = progresso["value"] + 5
         # Procura elmento principal dos proximos eventos
        
        
        eventos = obter_eventos_dazn_completo(driverchrome1)
    
        # Obtendo data inicial da UI para filtro
        try:
            data_inicio_str = entry_data.get()
            data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
        except:
            data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for evento in eventos:
            campeonato = expected_camp or "Mundial de Clubes FIFA"
            import re
            jogo = re.sub(r'\s+[vVxX]\s+', ' x ', evento["Jogo"]).upper()
            data_hora = evento["Data/hora"]
            url = evento["URL"]
            plataforma = "Dazn"
            minutos_antes = "15"
            data = data_hora.split(" ")[0]
            hora = data_hora.split(" ")[1]
            
            # FILTRO DE DATA
            try:
                ev_date_obj = datetime.strptime(data, "%d/%m/%Y")
                if ev_date_obj < data_inicio_obj:
                    continue
            except:
                pass
                        
            list_b.append(csv_list)                  
        
  except Exception as e: 
       logging.error(f"Erro ocorrido: {e}")  # Registra o erro no log
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       habilita_botoes()
       update_command() 
       pass     
  

MESES_PT = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}

def format_datetime(data_str, base_date=None):
    """
    Converte strings de data/hora vindas das plataformas (Prime/Max/etc)
    para {"data": "dd/mm/YYYY", "hora": "HH:MM"}.

    Suporta:
      - Max PT-BR curto: "sáb., 14:55"
      - Max PT-BR completo: "18 de jan., 16:55"
      - PT-BR literal: "Hoje: 20:40", "Amanhã: 21:10"
      - Prime/Outros: "Live At 7 PM", "Tomorrow 7:30 PM", "Wed, Jul 30 7 PM", etc.

    base_date (opcional):
      - pode ser datetime/date ou string "dd/mm/yyyy".
      - Para o formato curto do Max ("sáb., 14:55") usamos ref = max(now, base_date)
        para NÃO voltar no tempo e bater com o “próximo sábado” real da agenda.
    """
    try:
        if not data_str:
            return {"data": "", "hora": ""}

        # ---------- helpers ----------
        def _clean(s: str) -> str:
            s = s.replace("\u00a0", " ")
            for ch in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u2066", "\u2067", "\u2068", "\u2069"):
                s = s.replace(ch, "")
            s = re.sub(r"\s+", " ", s).strip()
            return s

        def _parse_base_date(bd):
            if bd is None:
                return None
            if isinstance(bd, datetime):
                return bd
            try:
                from datetime import date as _date
                if isinstance(bd, _date):
                    return datetime(bd.year, bd.month, bd.day)
            except Exception:
                pass
            if isinstance(bd, str):
                try:
                    return datetime.strptime(bd.strip(), "%d/%m/%Y")
                except Exception:
                    return None
            return None

        # ---------- normalização inicial ----------
        original = data_str
        data_str = _clean(str(data_str))

        # Tradução manual de meses/dias (Inglês -> Português) para Prime Video
        eng_pt = {
            'jan': 'jan', 'feb': 'fev', 'mar': 'mar', 'apr': 'abr', 'may': 'mai', 'jun': 'jun',
            'jul': 'jul', 'aug': 'ago', 'sep': 'set', 'oct': 'out', 'nov': 'nov', 'dec': 'dez',
            'mon': 'seg', 'tue': 'ter', 'wed': 'qua', 'thu': 'qui', 'fri': 'sex', 'sat': 'sab', 'sun': 'dom'
        }
        for eng, pt in eng_pt.items():
            data_str = re.sub(rf'\b{eng}\b', pt, data_str, flags=re.IGNORECASE)

        # 🔧 PATCH DEFINITIVO Hoje / Amanhã
        data_str = (
            data_str
            .replace("Hoje:", "Hoje: ")
            .replace("Amanhã:", "Amanhã: ")
        )

        now = datetime.now()
        bd_dt = _parse_base_date(base_date)

        # =====================================================
        # 🇧🇷 HOJE / AMANHÃ (PT-BR literal)
        # =====================================================
        low = data_str.lower()

        if low.startswith("hoje"):
            try:
                # "Hoje: 15:25" → pega HH:MM com regex para não confundir com o ':' do "Hoje:"
                m_hoje = re.search(r"(\d{1,2}:\d{2})", data_str)
                if m_hoje:
                    hh, mm = map(int, m_hoje.group(1).split(":"))
                    dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    return {"data": dt.strftime("%d/%m/%Y"), "hora": dt.strftime("%H:%M")}
            except Exception:
                pass

        if low.startswith("amanh"):
            try:
                m_ama = re.search(r"(\d{1,2}:\d{2})", data_str)
                if m_ama:
                    hh, mm = map(int, m_ama.group(1).split(":"))
                    dt = (now + timedelta(days=1)).replace(
                        hour=hh, minute=mm, second=0, microsecond=0
                    )
                    return {"data": dt.strftime("%d/%m/%Y"), "hora": dt.strftime("%H:%M")}
            except Exception:
                pass


        # =====================================================
        # 🇧🇷 MAX PT-BR CURTO: "sáb., 14:55"
        # =====================================================
        m = re.match(
            r"^(seg|ter|qua|qui|sex|sab|sáb|dom)\.,?\s*(\d{1,2}:\d{2})$",
            data_str.lower()
        )
        if m:
            dia_semana_str = m.group(1).lower().replace("sab", "sáb")
            hora_str = m.group(2)

            dias_map = {
                "seg": 0, "ter": 1, "qua": 2, "qui": 3,
                "sex": 4, "sáb": 5, "dom": 6
            }

            alvo = dias_map.get(dia_semana_str)
            if alvo is not None:
                ref = max(now, bd_dt) if bd_dt else now
                ref0 = ref.replace(hour=0, minute=0, second=0, microsecond=0)

                delta = (alvo - ref0.weekday()) % 7
                h, m_ = map(int, hora_str.split(":"))
                candidato = (ref0 + timedelta(days=delta)).replace(
                    hour=h, minute=m_, second=0, microsecond=0
                )

                if candidato < now:
                    candidato += timedelta(days=7)

                return {
                    "data": candidato.strftime("%d/%m/%Y"),
                    "hora": candidato.strftime("%H:%M")
                }

        # =====================================================
        # 🇧🇷 PORTUGUESE NUMERIC FORMAT: "sábado, 1/08 17:00 BRT"
        # =====================================================
        m = re.search(
            r"(\d{1,2})/(\d{2})\s+(\d{1,2}:\d{2})",
            data_str.lower()
        )
        if m:
            dia = int(m.group(1))
            mes = int(m.group(2))
            hh, mm = map(int, m.group(3).split(":"))

            dt = datetime(now.year, mes, dia, hh, mm)
            if dt < now - timedelta(days=15):
                dt = dt.replace(year=now.year + 1)

            return {
                "data": dt.strftime("%d/%m/%Y"),
                "hora": dt.strftime("%H:%M")
            }

        # =====================================================
        # 🇧🇷 MAX PT-BR COMPLETO: "18 de jan., 16:55"
        # =====================================================
        MESES_PT_LIT = {
            "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
            "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
        }

        m = re.search(
            r"(\d{1,2})\s+de\s+([a-zç]{3})\.?,?\s+(\d{1,2}:\d{2})",
            data_str.lower()
        )
        if m:
            dia = int(m.group(1))
            mes = MESES_PT_LIT.get(m.group(2))
            hh, mm = map(int, m.group(3).split(":"))

            if mes:
                dt = datetime(now.year, mes, dia, hh, mm)
                if dt < now - timedelta(days=1):
                    dt = dt.replace(year=now.year + 1)

                return {
                    "data": dt.strftime("%d/%m/%Y"),
                    "hora": dt.strftime("%H:%M")
                }

        # =====================================================
        # 🔵 FORMATO INGLÊS / GENÉRICO
        # =====================================================
        data_str2 = (
            data_str.title()
            .replace("Pm", "PM")
            .replace("Am", "AM")
        )
        data_str2 = re.sub(r"\s+", " ", data_str2)
        data_str2 = re.sub(r"(\b[AP]M):00\b", r"\1", data_str2)

        if data_str2.startswith("Live At "):
            hora = data_str2.replace("Live At ", "").strip()
            try:
                hora_obj = datetime.strptime(hora, "%I:%M %p")
            except ValueError:
                hora_obj = datetime.strptime(hora, "%I %p")
            dt = now.replace(hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0)
            return {"data": dt.strftime("%d/%m/%Y"), "hora": dt.strftime("%H:%M")}

        if data_str2.startswith("Tomorrow"):
            hora = data_str2.replace("Tomorrow", "").strip()
            try:
                hora_obj = datetime.strptime(hora, "%I:%M %p")
            except ValueError:
                hora_obj = datetime.strptime(hora, "%I %p")
            dt = (now + timedelta(days=1)).replace(
                hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0
            )
            return {"data": dt.strftime("%d/%m/%Y"), "hora": dt.strftime("%H:%M")}

        possible_formats = [
            "%I:%M %p", "%I %p",
            "%b %d %I:%M %p", "%b %d %I %p",
            "%a, %b %d %I:%M %p", "%a, %b %d %I %p",
            "%a, %b %d %I:%M", "%a, %b %d %I",
            "%b %d %I:%M", "%b %d %I"
        ]

        for fmt in possible_formats:
            try:
                parsed = datetime.strptime(data_str2, fmt).replace(year=now.year)
                if parsed < now - timedelta(days=1):
                    parsed = parsed.replace(year=now.year + 1)
                return {"data": parsed.strftime("%d/%m/%Y"), "hora": parsed.strftime("%H:%M")}
            except Exception:
                continue

        return {"data": "", "hora": ""}

    except Exception as e:
        logging.error(f"[ERRO FORMAT_DATETIME] {e} | original='{data_str}'")
        return {"data": "", "hora": ""}

    
def run_eventos_prime(url_camp, expected_camp=""):
    try:
        label_toolbarprocess.config(text="Atualização de eventos do Amazon Prime")
        text="Realizando a atualização dos grids com os eventos do Amazon Prime..."
        progresso["value"] = 0
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            text="Chrome (9222) indisponível."
            return

        chrome_options = Options()
        chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        service = Service(ChromeDriverManager().install())
        driverchrome1 = webdriver.Chrome(service=service, options=chrome_options)

        us = get_config_value("usuario_prime")
        pas = get_config_value("senha_prime")
        url_plataform = "https://www.primevideo.com/offers/nonprimehomepage/ref=atv_auth_signout"

        csv_list = ()
        list_b = list(csv_list)
        var_navegador = "Esquerda"

        text="Abrindo pagina do campeonato..."
        progresso["value"] += 5
        driverchrome1.get(url_plataform)
        loginprime(url_camp, us, pas, driverchrome1, 10, "Novos")

        text="Limpando o grid..."
        delete_null_items()

        text="Atualizando lista do campeonato Amazon Prime..."
        progresso["value"] += 5

        wait = WebDriverWait(driverchrome1, 15)

        # ✅ Localize a UL pela âncora estável data-testid
        uls = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[data-testid='card-container-list']"))
        )
        if not uls:
            text="Nenhuma lista de cards encontrada."
            return

        # Rolagem para forçar carregamento das listas
        valid_uls = []
        for u_idx, ul in enumerate(uls):
            title_text = ""
            try:
                # Procura h2, h3 ou span de título no ancestral
                parent_shelf = ul.find_element(By.XPATH, "./ancestor::section[1] | ./ancestor::div[contains(@class, 'carousel') or contains(@class, 'shelf')][1]")
                for tag in ("h2", "h3", "span"):
                    headers = parent_shelf.find_elements(By.TAG_NAME, tag)
                    for h in headers:
                        if h.text.strip():
                            title_text = h.text.strip()
                            break
                    if title_text:
                        break
                if not title_text:
                    title_text = ul.find_element(By.XPATH, "../preceding-sibling::*[1]").text.strip()
            except:
                pass

            title_lower = title_text.lower()
            
            # Blacklist de palavras-chave para ignorar carrosséis irrelevantes (incluindo replays passados, times/ligas e combo Premiere)
            blacklist = ["repetições", "repetição", "replays", "replay", "equipes", "equipas", "destaques", "melhores", "momento", "moments", "highlights", "excluir", "ligas", "liga", "teams", "times", "terminadas", "encerrados", "recentemente", "concluídos", "concluidos", "premiere", "combo", "upgrade"]
            is_blacklisted = any(word in title_lower for word in blacklist)
            
            if is_blacklisted:
                logging.info(f"[Prime] Ignorando lista {u_idx} ('{title_text}') por estar na blacklist.")
                continue
                
            logging.info(f"[Prime] Carrossel {u_idx} ('{title_text}') aceito.")
            valid_uls.append((ul, title_text))

        # 🔥 REGRA SOLICITADA: No Prime Video, capturar APENAS a lista principal de cima ("Seus eventos ao vivo e próximos eventos") e ignorar carrosséis inferiores / Premiere
        if valid_uls:
            logging.info(f"[Prime] {expected_camp}: restringindo busca apenas à lista principal de cima ('{valid_uls[0][1]}').")
            valid_uls = valid_uls[:1]

        # Rolagem para forçar carregamento das listas válidas
        for ul, title in valid_uls:
            try:
                driverchrome1.execute_script("arguments[0].scrollIntoView({block:'center'});", ul)
                time.sleep(0.5)
            except Exception as scroll_err:
                logging.warning(f"[Prime] Erro ao rolar lista: {scroll_err}")

        # Pega todos os cards de eventos (normais e super carrosséis) diretamente nas listas válidas
        cards = []
        for ul, title in valid_uls:
            try:
                ul_cards = ul.find_elements(By.CSS_SELECTOR, "article[data-testid='card'], article[data-testid='super-carousel-card']")
                cards.extend(ul_cards)
            except Exception as e:
                logging.warning(f"[Prime] Erro ao buscar cards na lista '{title}': {e}")
                
        logging.info(f"[Prime] Total de cards de eventos encontrados nas listas válidas: {len(cards)}")

        for idx, card in enumerate(cards):

            # Título confiável via atributo ou aria-label/alt para super-carousel-cards
            nome_evento = card.get_attribute("data-card-title") or ""
            if not nome_evento.strip():
                try:
                    nome_evento = card.find_element(By.CSS_SELECTOR, "a[aria-label]").get_attribute("aria-label")
                except Exception:
                    pass
            if not nome_evento.strip():
                try:
                    nome_evento = card.find_element(By.CSS_SELECTOR, "img[alt]").get_attribute("alt")
                except Exception:
                    pass
            if not nome_evento.strip():
                try:
                    nome_evento = card.find_element(By.CSS_SELECTOR, "a._3HZFFn").text.strip()
                except Exception:
                    nome_evento = ""

            data_hora = ""

            try:
                # Tenta os seletores conhecidos para o texto de data/hora (qKxeGx é o novo do Prime)
                data_hora_el = None
                for selector in ("p.qKxeGx", "p.GNymT4"):
                    try:
                        data_hora_el = card.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        pass
                if data_hora_el:
                    data_hora = data_hora_el.text.strip()
                    logging.info("[Prime] Data encontrada no card: %r", data_hora)
            except Exception as e:
                logging.warning(
                    "[Prime] Elemento de data não encontrado no card idx=%s: %s",
                    idx, e
                )

            # 🔁 Fallback: tenta ler texto visível do card inteiro
            if not data_hora:
                try:
                    data_hora = card.text.strip()
                    logging.info("[Prime] Fallback data via card.text: %r", data_hora)
                except Exception as e:
                    logging.error(
                        "[Prime] Falha no fallback card.text idx=%s: %s",
                        idx, e, exc_info=True
                    )
            # ================================
            # DATA/HORA – fluxo correto
            # ================================
            raw_text = data_hora  # texto bruto do card

            extracted = extract_prime_datetime(raw_text)

            logging.info(
                        "[Prime][DEBUG] raw_text=%r | extracted=%r",
                        raw_text, extracted
            )

            if not extracted:
                        logging.warning("[Prime] Data não encontrada no card")
                        continue  # pula este evento

                    # ⚠️ A PARTIR DAQUI SÓ USE extracted
            data_hora = extracted

            data_hora_formatada = format_datetime(data_hora)

                    
            # ================================
            # URL – captura robusta
            # ================================
            url = ""

            try:
                a_tags = card.find_elements(By.CSS_SELECTOR, "a[href]")
                if a_tags:
                    url = a_tags[0].get_attribute("href") or ""
            except Exception as e:
                logging.warning("[Prime] Falha ao buscar <a href>: %s", e)

            # Fallback: tenta direto no article
            if not url:
                try:
                    url = card.get_attribute("href") or ""
                except Exception:
                    pass

            # Normalização
            if url.startswith("/"):
                url = "https://www.primevideo.com" + url

            if not url:
                logging.warning("[Prime] URL não encontrada para evento: %r", nome_evento)
            else:
                logging.info("[Prime] URL capturada: %s", url)

            # Se não houver horário no card, entra no detalhe para ler (fallback)
            if not data_hora:
                if url:
                    driverchrome1.execute_script("window.open(arguments[0], '_blank');", url)
                    driverchrome1.switch_to.window(driverchrome1.window_handles[-1])
                    try:
                        cdate = wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="main"]/div[1]/div/div/div[2]/div/div/div/div[2]/span[2]')
                            )
                        )
                        data_hora_BRT = cdate.text
                        data_hora = data_hora_BRT.replace("BRT", "").strip()
                    except Exception:
                        data_hora = ""
                    finally:
                        driverchrome1.close()
                        driverchrome1.switch_to.window(driverchrome1.window_handles[0])

            # Campeonato (se necessário). O seu XPath antigo é frágil; tenta pegar o alt da imagem do card.
            # Campeonato (direto no alt da imagem ou fallback)
            try:
                # Tenta pegar do alt da imagem do card
                campeonato_img = card.find_element(By.CSS_SELECTOR, "img[alt]").get_attribute("alt").strip()
                campeonato = campeonato_img if (campeonato_img and len(campeonato_img) > 3) else expected_camp
            except Exception:
                campeonato = expected_camp or ""

            # Normaliza data/hora
            data_str = (data_hora or "").title()
            data_hora_formatada = {"data": "", "hora": ""}
            if data_str:
                try:
                    data_hora_formatada = format_datetime(data_str)
                except Exception:
                    data_hora_formatada = {"data": "", "hora": ""}

            plataforma = "Amazon Prime"
            dt = data_hora_formatada.get('data', '')

            if nome_evento.strip() and dt:
                csv_row = (
                    campeonato,
                    prettify_match_name(nome_evento),
                    data_hora_formatada['data'],
                    data_hora_formatada['hora'],
                    var_navegador,
                    10,
                    plataforma,
                    url
                )
                tree.insert("", "end", values=csv_row)

                # alterna
                var_navegador = "Direita" if var_navegador == "Esquerda" else "Esquerda"
                list_b.append(csv_row)

            # Progresso a cada item
            if idx % 2 == 0:
                progresso["value"] = min(100, progresso["value"] + 1)

        # Caso seja carrossel com botão "next 3 titles", clique algumas vezes para carregar mais
        try:
            for _ in range(3):
                btns = driverchrome1.find_elements(By.XPATH, '//button[@aria-label="next 3 titles"]')
                if btns:
                    driverchrome1.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
                    time.sleep(0.3)
                    driverchrome1.execute_script("arguments[0].click();", btns[0])
                    time.sleep(1.2)
        except Exception:
            pass

    except UnboundLocalError as e:
        logging.error(f"Erro ocorrido: {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        habilita_botoes()
        update_command()
    except FileNotFoundError:
        logging.error("Arquivo não encontrado")
    except Exception as e:
        logging.error(f"Erro ocorrido: {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        habilita_botoes()
        update_command()

PORTUGUESE_NUMERIC_DT_RE = re.compile(
    r"\b(?:segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|sabado|domingo|segunda|terça|terca|quarta|quinta|sexta|seg|ter|qua|qui|sex|sáb|sab|dom)\b\.?,\s*"
    r"\d{1,2}/\d{2}\s+\d{1,2}:\d{2}(?:\s*BRT)?",
    re.IGNORECASE
)

PORTUGUESE_LITERAL_DT_RE = re.compile(
    r"\b(?:segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|sabado|domingo|segunda|terça|terca|quarta|quinta|sexta|seg|ter|qua|qui|sex|sáb|sab|dom)\b\.?,\s*"
    r"\d{1,2}\s+de\s+"
    r"(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\b\.?\s+"
    r"\d{1,2}:\d{2}(?:\s*BRT)?",
    re.IGNORECASE
)

PRIME_DT_RE = re.compile(
    r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"\d{1,2}\s+"
    r"\d{1,2}(?::\d{2})?\s*(?:AM|PM)\b",
    re.IGNORECASE
)

def extract_prime_datetime(text: str) -> str:
    """
    Extrai data/hora do Prime Video a partir de texto de card (Inglês ou Português).
    Ex: 'Thu, Jan 29 7:30 PM' ou 'sábado, 1/08 17:00 BRT'
    """
    if not text:
        return ""
    # 1. Tenta formato numérico português: "sábado, 1/08 17:00 BRT"
    m = PORTUGUESE_NUMERIC_DT_RE.search(text)
    if m:
        return m.group(0).strip()
    # 2. Tenta formato literal português: "quarta-feira, 22 de jul. 18:50 BRT"
    m = PORTUGUESE_LITERAL_DT_RE.search(text)
    if m:
        return m.group(0).strip()
    # 3. Tenta formato inglês: "Thu, Jan 29 7:30 PM"
    m = PRIME_DT_RE.search(text)
    if m:
        return m.group(0).strip()
    return ""


def run_eventos_max(url_camp, expected_camp="Campeonato Paulista"):
    try:
        label_toolbarprocess.config(text="Atualização de eventos do Max")
        text="Coletando eventos do Campeonato Paulista (Max)..."
        progresso["value"] = 0
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            text="Chrome (9222) indisponível."
            return

        chrome_options = Options()
        chrome_options.add_experimental_option(
            "debuggerAddress", "127.0.0.1:9222"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        wait = WebDriverWait(driver, 30)

        progresso["value"] = 5
        driver.get(url_camp)

        # Aguarda primeiro batch de cards (tolerante — não aborta se não encontrar)
        try:
            wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a[data-testid$="_tile"]')
                )
            )
        except Exception:
            logging.warning(f"[Max] Timeout aguardando tiles em '{url_camp}'. Tentando mesmo assim...")

        progresso["value"] = 15

        # 🔁 Rola o rail até estabilizar
        rolar_cards_proximos_eventos(driver)

        time.sleep(1.5)

        tiles = driver.find_elements(
            By.CSS_SELECTOR,
            'a[data-testid$="_tile"]'
        )

        logging.info(f"[Max] URL: {url_camp} | Campeonato: {expected_camp} | Tiles encontrados: {len(tiles)}")
        text=f"Cards detectados no DOM: {len(tiles)}"
        progresso["value"] = 25

        if len(tiles) == 0:
            # Diagnóstico: tenta listar todos os <a> com data-testid para entender a estrutura
            all_a = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid]')
            logging.warning(f"[Max] Nenhum tile encontrado. Total de <a data-testid>: {len(all_a)}")
            for a in all_a[:10]:
                try:
                    logging.warning(f"[Max] <a data-testid='{a.get_attribute('data-testid')}' href='{a.get_attribute('href')}'>")
                except:
                    pass
            label_toolbarprocess.config(text=f"[Max] Nenhum card encontrado para '{expected_camp}'. Verifique os Logs.")
            progresso.pack_forget()
            return

        delete_null_items()

        var_navegador = "Esquerda"
        eventos_encontrados = 0
        urls_processadas = set()

        # Obtendo data inicial da UI para filtro
        try:
            data_inicio_str = entry_data.get()
            data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
        except:
            data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for idx, a_tag in enumerate(tiles):
            info = ler_tile_max_com_retry(a_tag)

            if not info:
                continue

            url = info["url"]
            if url.startswith("/"):
                url = "https://play.hbomax.com" + url

            if url in urls_processadas:
                continue
            urls_processadas.add(url)

            data_fmt = format_datetime(info["data_hora"])
            dt = data_fmt.get("data", "")
            hr = data_fmt.get("hora", "")

            if not dt:
                continue

            # remove "Rodada XX" do título e normaliza separador 'v/x' → ' x '
            titulo = info["titulo"]
            titulo = re.sub(r"\s+Rodada\s+\d+.*$", "", titulo, flags=re.IGNORECASE).strip()
            titulo = re.sub(r'\s+[vVxX]\s+', ' x ', titulo)
            
            # FILTRO DE DATA
            try:
                ev_date_obj = datetime.strptime(dt, "%d/%m/%Y")
                if ev_date_obj < data_inicio_obj:
                    continue
            except:
                pass

            csv_row = (
                expected_camp or "Campeonato Paulista",
                prettify_match_name(titulo),
                dt,
                hr,
                var_navegador,
                10,
                "TNT_SPORTS",
                url
            )

            tree.insert("", "end", values=csv_row)

            var_navegador = (
                "Direita" if var_navegador == "Esquerda" else "Esquerda"
            )

            eventos_encontrados += 1

            if idx % 3 == 0:
                progresso["value"] = min(95, progresso["value"] + 1)

        if eventos_encontrados == 0:
             text="Nenhum evento do Paulistão encontrado."
        else:
             
             text=f"Eventos do Paulistão (Max): {eventos_encontrados}"
            

        progresso["value"] = 100
        time.sleep(1)
        progresso.pack_forget()
        label_toolbarprocess.config(text="")

    except Exception as e:
        logging.error(f"Erro ocorrido: {e}")
        habilita_botoes()

def ler_tile_max_com_retry(a_tag, tentativas=6, delay=0.4):
    """
    Lê corretamente um tile do Max (Paulistão),
    lidando com virtualização do rail.
    """
    for _ in range(tentativas):
        try:
            # URL
            url = a_tag.get_attribute("href")
            if not url:
                raise Exception("href vazio")

            # DATA / HORA  ✅ (seletor CORRETO)
            badge = a_tag.find_elements(
                By.CSS_SELECTOR,
                'span[class*="StyledBadgeText"]'
            )
            if not badge:
                raise Exception("badge não encontrado")

            data_hora = badge[0].text.strip()
            if not data_hora:
                raise Exception("data vazia")

            # TÍTULO PRINCIPAL  ✅
            titulo = a_tag.find_element(
                By.CSS_SELECTOR,
                'span[class*="StyledPrimaryTitle"]'
            ).text.strip()

            if not titulo:
                raise Exception("titulo vazio")

            # ❌ NÃO adiciona rodada no nome
            return {
                "url": url,
                "data_hora": data_hora,
                "titulo": titulo
            }

        except Exception:
            time.sleep(delay)

    return None

        
def rolar_cards_proximos_eventos(driver, max_clicks=40, wait_time=0.8):
    """
    Força o carregamento TOTAL do rail do Max
    clicando na seta e garantindo repaint do DOM.
    """
    for i in range(max_clicks):
        try:
            btn = driver.find_element(
                By.CSS_SELECTOR,
                'button[data-position="forward"]'
            )

            if not btn.is_displayed():
                break

            # força o botão a ficar visível
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                btn
            )

            time.sleep(0.2)

            # clique via JS (obrigatório no Max)
            driver.execute_script("arguments[0].click();", btn)

            # força repaint do rail
            driver.execute_script("window.dispatchEvent(new Event('resize'));")

            time.sleep(wait_time)

        except Exception:
            break

def reduzir_minutos(minutos_a_subtrair):
    """
    Retorna [data_atual_str, hora_atual_str] com minutos reduzidos.
    
    Args:
        minutos_a_subtrair (int): Minutos a subtrair da hora atual.
    
    Returns:
        list: [data_str, hora_str] (strings formatadas).
    """
    agora = datetime.now()
    resultado = agora - timedelta(minutes=minutos_a_subtrair)
    
    # Formatação como strings (personalizável)
    data_str = resultado.strftime("%d/%m/%Y")  # Ex: "12/05/2025"
    hora_str = resultado.strftime("%H:%M")     # Ex: "18:20"
    
    return [data_str, hora_str]

def converter_data_pt(data_str):

    meses_pt_en = {
    'jan.': 'Jan', 'fev.': 'Feb', 'mar.': 'Mar', 'abr.': 'Apr',
    'mai.': 'May', 'jun.': 'Jun', 'jul.': 'Jul', 'ago.': 'Aug',
    'set.': 'Sep', 'out.': 'Oct', 'nov.': 'Nov', 'dez.': 'Dec'
}

    for pt, en in meses_pt_en.items():
       data_str = data_str.replace(pt, en)
    data_str2 = datetime.strptime(data_str, "%d %b %Y")        
     # 3. Formata como string no novo formato
    return data_str2.strftime("%d/%m/%Y")  # Formato brasileiro

def run_eventos_disney(url_camp, expected_camp=None):

  try:   
        
      
        #  Usa o navegador da esquerda para buscar a lista
        label_toolbarprocess.config(text="Atualização de eventos da Disney")
        text="Realizando a atualização dos eventos da Disney no grids..."
        progresso["value"] = 0
        #    Exibe progressbar
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            text="Chrome (9222) indisponível."
            return

        chrome_options = Options()
        chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        service = Service(ChromeDriverManager().install())
        driverchrome1 = webdriver.Chrome(service=service, options=chrome_options)

        #  Cria uma lista para adicionar os items futuramento no treeview

        us = get_config_value("usuario_disney")
        pas = get_config_value("senha_disney")
        url_plataform = "https://www.disneyplus.com/identity/login/enter-email"
       
        csv_list = ()
        list_b = list(csv_list)

        csv_list = (" "," "," "," "," ","","","","")
        list_b.append(csv_list)

        var_navegador = "Esquerda"

        text="Abrindo pagina do campeonato da Disney..."
        progresso["value"] = progresso["value"] + 5
        driverchrome1.get(url_plataform)
        logindisney(url_camp,us,pas,driverchrome1,10,"Novos")

        text="Limpando o grid..."
        delete_null_items()
       
        text="Atualizando lista..."
        progresso["value"] = progresso["value"] + 5

        # Obtendo data inicial da UI para filtro
        try:
            data_inicio_str = entry_data.get()
            data_inicio_obj = datetime.strptime(data_inicio_str, "%d/%m/%Y")
        except:
            data_inicio_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

         # Procura elmento principal dos proximos eventos
        c1 = driverchrome1.find_elements(By.XPATH,'//*[@class="_192jb2w9 xgfbc11x2 ordv7e0"]')
        terminar_externo = False

        if len(c1) > 0:
            
            for i in range(len(c1)):

                try:
                  c2 = c1[i].find_elements(By.CSS_SELECTOR,'div')
                except StaleElementReferenceException:
                    pass  
            try:                
                for j in range(len(c2)):

                 if j % 2 == 0:
                     
                     progresso["value"] = progresso["value"] + 1
                     elemento_hover = driverchrome1.find_elements(By.XPATH,'//*[@id="explore-ui-main-content-container"]/div[1]/section/div/button[2]')
                     if len(elemento_hover) > 0:
                    #    time.sleep(3)
                       driverchrome1.execute_script("arguments[0].click();", elemento_hover[0])
                    #    driverchrome1.find_element(By.XPATH,'//*[@id="a-page"]/div[1]/div[5]/main/div/div[2]/div/section/div/button[2]').click()
                
                    #  time.sleep(3)
                     it = c2[j].find_elements(By.XPATH,'//*[@class="_192jb2wb _2b0dm73"]')
                     
                     for f in range(len(it)): 

                      h = it[f].find_elements(By.XPATH,'//*[@class="_1o25tbf1 xgfbc1w2"]')
                      
                      for n in range(len(h)):
                    
                                           
                       all_text = h[n].text.split("\n")
                     
                       if re.search('\\bComeçou\\b', all_text[0], re.IGNORECASE):
                        a = all_text[0].split(" ")
                        b = [int(num) for num in re.findall(r'\d+', a[2])]
                        result = reduzir_minutos(b[0])
                        data = result[0]
                        hour = result[1]
                        datahora_str = f"{data} {hour}"
                        data_str = data
                        dt_time = data
                          

                       else:
                        dt_time = all_text[0].split(" • ")

                        if len(all_text) > 2:

                         if  'Transmitido' not in dt_time[0] and 'Brasileiro' in all_text[2]:
                            
                          if len(dt_time) > 1 and dt_time[0] !=  ' ...':
                           data = dt_time[0]
                           data_str = converter_data_pt(data)                        
                           hour = dt_time[1].split("-")[0].rstrip() 
                           datahora_str = f"{data_str} {hour}"
                        
                           if "-" in datahora_str:
                            # Extrai apenas a data e a última hora
                            partes = datahora_str.split()
                            data_str = partes[0]  # "2025-05-14"
                            hora_str = partes[2]  # "18:50"
                                           
                           elif "/" in datahora_str:
                             # Extrai apenas a data e a última hora
                            partes = datahora_str.split()
                            data_str = partes[0]  # "2025-05-14"
                            hour = partes[1]  # "18:50"                          
                          else:
                           data_str = datetime.now().strftime('%d/%m/%Y')           
                           hour = all_text[0].split("-")[0].rstrip()  
                           datahora_str = f"{data_str} {hour}"
                           if '/' in datahora_str and 'Transmitido' not in datahora_str :
                             datetm = datetime.strptime(datahora_str, '%d/%m/%Y %H:%M')  
                           elif '/' not in datahora_str:
                             datetm = datetime.strptime(datahora_str, '%d %m %Y %H:%M') 
                        
                       event = all_text[1]
                       if len(list_b) > 0:

                         if len(all_text) > 2 and 'Transmitido' not in dt_time[0]:
                           event = all_text[1]
                           champ = all_text[2].replace("Campeonato", "").strip() if len(all_text) > 2 else (expected_camp or "Disney")
                           
                           # Tenta pegar o link da tag pai ou de links internos
                           links = h[n].find_elements(By.TAG_NAME, "a")
                           url = links[0].get_attribute("href") if links else ""
                           
                           plataforma = "Disney"
                           
                           # FILTRO DE DATA
                           try:
                               ev_date_obj = datetime.strptime(data_str, "%d/%m/%Y")
                               if ev_date_obj < data_inicio_obj:
                                   continue
                           except:
                               pass

                           csv_list = (champ, prettify_match_name(event), data_str, hour, var_navegador, 0, plataforma, url)
                           tree.insert("", "end", values=csv_list)
                         
                           var_navegador = "Direita" if var_navegador == "Esquerda" else "Esquerda"
                           list_b.append(csv_list)

                           if len(elemento_hover) > 0:
                                 driverchrome1.execute_script("arguments[0].click();", elemento_hover[0])  
                                 c1 = driverchrome1.find_elements(By.XPATH,'//*[@class="_192jb2w9 xgfbc11x2 ordv7e0"]')
                                 c2 = c1[i].find_elements(By.CSS_SELECTOR,'div')
                                 it = c2[j].find_elements(By.XPATH,'//*[@class="_192jb2wb _2b0dm73"]')
                                 h = it[f].find_elements(By.XPATH,'//*[@class="_1o25tbf1 xgfbc1w2"]')
                                 time.sleep(5)              
                         else:
                             terminar_externo = True
                             break
                         
                       if terminar_externo:
                           break     
                      if terminar_externo:
                           break      
                     if terminar_externo:
                           break
                 if terminar_externo:
                        break
                
            except StaleElementReferenceException:
                    #  time.sleep(2)  # Pequena pausa para garantir que o DOM foi atualizado
              pass
                     
            except exceptions.NoSuchElementException:
                    #  time.sleep(2)  # Pequena pausa para garantir que o DOM foi atualizado
             pass

            finally:
             habilita_botoes()     
             pass             #  time.sleep(4)
                     
            remover_duplicatas(tree)
       
        
  except UnboundLocalError as e:
       logging.error(f"Erro ocorrido: {e}")  # Registra o erro no log
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       habilita_botoes()
       update_command()  
       pass

  except FileNotFoundError as e:
        logging.error(f"Arquivo não encontrado = {e}")
  except Exception as e: 
   logging.error(f"Erro ocorrido: {e}")  # Registra o erro no log
   exc_type, exc_obj, exc_tb = sys.exc_info()
   fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
   habilita_botoes()
   update_command()
   pass
  
  finally:
            habilita_botoes()
  
def desabilita_botoes():
    

    button_update.config(state=DISABLED)
    botao_getlista.config(state=DISABLED)
    botao_enviaremail.config(state=DISABLED)
    botao_abrir.config(state=DISABLED)
    botao_limpartree.config(state=DISABLED)
    botao_salvar.config(state=DISABLED)
    button_atualizacao.config(state=DISABLED)
    button_chrome1.config(state=DISABLED)
    button_add.config(state=DISABLED)
    button_chrome2.config(state=DISABLED)
    button_delete.config(state=DISABLED)
    

def habilita_botoes():

    button_update.config(state=NORMAL)
    botao_getlista.config(state=NORMAL)
    botao_enviaremail.config(state=NORMAL)
    botao_abrir.config(state=NORMAL)
    botao_limpartree.config(state=NORMAL)
    botao_salvar.config(state=NORMAL)
    button_atualizacao.config(state=NORMAL)
    button_chrome1.config(state=NORMAL)
    button_add.config(state=NORMAL)
    button_chrome2.config(state=NORMAL)
    button_delete.config(state=NORMAL)
  
def run_busca_eventos(ignorar_trava=False):
    global thread_em_execucao
    if thread_em_execucao and not ignorar_trava:
        logging.info("[INFO] Já existe uma busca em andamento. Abortando nova tentativa.")
        return
    
    conseguiu_trava = False
    if not ignorar_trava:
        thread_em_execucao = True
        conseguiu_trava = True

    try:
        logging.info("Iniciando run_busca_eventos...")

        # MODO SOMENTE RELATORIO: Abre o Chrome 1 automaticamente antes da busca
        if checkbox_busca.get() == 1:
            logging.info("Modo 'Somente Relatório' detectado. Abrindo Chrome (9222)...")
            update_chrome1()
            time.sleep(5) # Aguarda inicialização robusta
        
        if button_update["text"] == "Running" or button_update["text"] == "Stoped":
            update_command()


        if is_selected_plat("Dazn"):
            if is_selected_camp("Mundial de Clubes FIFA"):
                url_camp = 'https://www.dazn.com/pt-BR/competition/Competition:dc4k1xh2984zbypbnunk7ncic'
                run_eventos_dazn(url_camp, expected_camp="Mundial de Clubes FIFA")
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)

        if is_selected_plat("Amazon Prime"):
            if is_selected_camp("Brasileirão serie A"):
                url_camp = 'https://www.primevideo.com/tournament/amzn1.dv.icid.5a28c628-0310-42c0-8966-2f1f748488d3/ref=atv_hm_spo_c_NPzfck_2_1?jic=8%7CEgNhbGw%3D'
                run_eventos_prime(url_camp, expected_camp="Brasileirão serie A")
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)
            if is_selected_camp("Copa do Brasil"):
                url_camp = 'https://www.primevideo.com/tournament/amzn1.dv.icid.6e097abf-f4c9-4638-ba1e-7ff95367e1c8/ref=atv_hm_spo_c_NPzfck_2_2?jic=8%7CEgNhbGw%3D'
                run_eventos_prime(url_camp, expected_camp="Copa do Brasil") 
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)

        if is_selected_plat("Max"):
            if is_selected_camp("Campeonato Paulista"):
                url_camp = 'https://play.hbomax.com/sport/event/paulistao'
                run_eventos_max(url_camp, expected_camp="Campeonato Paulista")
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)

        if is_selected_plat("Disney"):
            if is_selected_camp("CONMEBOL Libertadores"):
                url_camp = 'https://www.disneyplus.com/pt-br/browse/entity-1229387e-c683-4ef3-9f32-68824a7be427'
                run_eventos_disney(url_camp, expected_camp="CONMEBOL Libertadores")
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)
            if is_selected_camp("CONMEBOL Sudamericana"):
                url_camp = 'https://www.disneyplus.com/pt-br/browse/entity-7bf8f49c-cc47-4d42-9a85-587631faee03'
                run_eventos_disney(url_camp, expected_camp="CONMEBOL Sudamericana")
                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)


        if is_selected_plat("Cazé TV"):
            canal_url = 'https://www.youtube.com/@CazeTV/streams'
            label_toolbarprocess.config(text="Atualização de eventos do Caze TV")
            desabilita_botoes()
            progresso.pack_forget()
            eventos = obter_eventos_futuros(canal_url) 
            progresso.pack(side=RIGHT, padx=10, pady=5)
            progresso["value"] = 0  
            var_navegador = "Esquerda"

            if eventos:
                for evento in eventos:
                    champ, titulo, url, data, horario = evento
                    event = titulo
                    plataforma = "Cazé TV"
                    progresso["value"] += 5
                    
                    csv_list = None
                    # Brasileirão na Cazé TV
                    if is_selected_camp("Brasileirão serie A") and "BRASILEIRAO" in champ.upper():
                        csv_list = ("Brasileirão serie A", event, data, horario, var_navegador, 15, plataforma, url)
                    # Paulista na Cazé TV
                    elif is_selected_camp("Campeonato Paulista") and "PAULISTA" in champ.upper():
                        csv_list = ("Campeonato Paulista", event, data, horario, var_navegador, 15, plataforma, url)
                    # Copa do Mundo (se houver na Cazé TV)
                    elif is_selected_camp("Copa do Mundo") and "COPA DO MUNDO" in champ.upper():
                        csv_list = ("Copa do Mundo FIFA 2026", event, data, horario, var_navegador, 15, plataforma, url)
                    # Libertadores na Cazé TV
                    elif is_selected_camp("CONMEBOL Libertadores") and "LIBERTADORES" in champ.upper():
                        csv_list = ("CONMEBOL Libertadores", event, data, horario, var_navegador, 15, plataforma, url)
                    # Sudamericana na Cazé TV
                    elif is_selected_camp("CONMEBOL Sudamericana") and "SUDAMERICANA" in champ.upper():
                        csv_list = ("CONMEBOL Sudamericana", event, data, horario, var_navegador, 15, plataforma, url)

                    if csv_list:
                        # Aplica nome canônico bonito antes de inserir no grid
                        csv_list = (csv_list[0], prettify_match_name(csv_list[1])) + csv_list[2:]
                        tree.insert("", "end", values=csv_list)
                        var_navegador = "Direita" if var_navegador == "Esquerda" else "Esquerda"

        # ── Campeonatos Extras (cadastrados na aba ⚽ Campeonatos) ─────────────
        # Roda ANTES da CBF para que as plataformas oficiais tenham prioridade sobre o PDF
        try:
            _scraper_map = {
                "Amazon Prime": run_eventos_prime,
                "Disney":       run_eventos_disney,
                "Max":          run_eventos_max,
                "Dazn":         run_eventos_dazn,
                "Cazé TV":      None,  # Cazé TV usa pipeline próprio abaixo
            }
            for cfg in carregar_campeonatos_config():
                if not cfg.get("ativo", True):
                    continue
                nome_camp = cfg.get("campeonato", "")
                plat      = cfg.get("plataforma", "")
                url_camp  = cfg.get("url", "")
                if not nome_camp or not url_camp or not plat:
                    continue

                logging.info(f"[CampExtras] Buscando '{nome_camp}' em '{plat}'...")
                label_toolbarprocess.config(text=f"Buscando {nome_camp} ({plat})...")

                if plat == "Cazé TV":
                    # Cazé TV: busca via obter_eventos_futuros e filtra pelo nome
                    try:
                        eventos_caze = obter_eventos_futuros(url_camp)
                        var_nav_ext = "Esquerda"
                        for champ_c, titulo_c, url_c, data_c, horario_c in (eventos_caze or []):
                            row_ext = (nome_camp, prettify_match_name(titulo_c), data_c, horario_c, var_nav_ext, 15, "Cazé TV", url_c)
                            tree.insert("", "end", values=row_ext)
                            var_nav_ext = "Direita" if var_nav_ext == "Esquerda" else "Esquerda"
                    except Exception as e_caze:
                        logging.error(f"[CampExtras] Erro Cazé TV '{nome_camp}': {e_caze}")
                else:
                    fn = _scraper_map.get(plat)
                    if fn:
                        try:
                            fn(url_camp, expected_camp=nome_camp)
                        except Exception as e_ext:
                            logging.error(f"[CampExtras] Erro '{nome_camp}' ({plat}): {e_ext}")

                padronizar_nomes_grid(tree)
                remover_duplicatas(tree)
        except Exception as e_dyn:
            logging.error(f"[CampExtras] Erro geral no pipeline dinâmico: {e_dyn}")

        # 🔥 PIPELINE CBF (PDF/Excel) - Roda por último e pula o que as plataformas já encontraram
        if is_selected_plat("CBF"):
            logging.info("Acionando pipeline CBF...")
            run_eventos_cbf()

        padronizar_nomes_grid(tree)
        remover_duplicatas(tree)
        ajustartodootree()
    
    except Exception as e:
        logging.error(f"Erro em run_busca_eventos: {e}")
    finally:
        if conseguiu_trava:
            thread_em_execucao = False
        habilita_botoes()
        progresso.pack_forget()
        label_toolbarprocess.config(text="")
        
        # MODO SOMENTE RELATORIO: Fecha o Chrome 1 ao terminar
        if checkbox_busca.get() == 1:
            logging.info("Finalizando busca em modo Relatório. Fechando Chrome (9222)...")
            fechar_chrome_por_porta("9222")
        
        

def ajustartodootree():
            text="Ajustando colunas do grid..."
            progresso["value"] = progresso["value"] + 10
            autoajustar_colunas(tree,ignorar=['Url'])          
            text="Ordenando por horário em ordem crescente"
            progresso["value"] = progresso["value"] + 10
            sort_by_time(tree, 2, 3)
            text="filtrando por data em ordem crescente"
            progresso["value"] = progresso["value"] + 10
            sort_by_date(tree, "Data")
            text="Removendo eventos duplicados"      
            text="Finalizado processo de busca de todos os eventos!"
            progresso.pack_forget()
            label_toolbarprocess.config(text="")
            progresso["value"] = 100

            var_navegador = "Esquerda"
            # Percorrendo todos os itens na Treeview
            for item_id in tree.get_children():
                # Obtém os valores atuais do item
                item = tree.item(item_id)
                
                # Modifica o valor da coluna específica
                valores = item['values']
                
                # Modifica o valor da coluna desejada (ex: coluna 1)
                valores = list(valores)  # Converter para lista para poder alterar
                valores[4] = var_navegador  # Atualiza o valor na coluna
                
                # Atualiza o item com o novo valor
                tree.item(item_id, values=tuple(valores))

                if var_navegador == "Esquerda":
                    var_navegador = "Direita"
                elif var_navegador == "Direita":
                    var_navegador = "Esquerda"
                

def sort_by_time(tree, date_col, time_col):
    # Função para ordenar por data e, em seguida, por hora

    # Obtendo todos os itens da Treeview
    items = list(tree.get_children())
    
    qtd = len(items)
    if qtd > 1:    
        # Função personalizada de comparação
        def get_sort_key(item_id):
            item = tree.item(item_id)
            data = item['values'][date_col]
            hora = item['values'][time_col]
            # Retorna tupla (data, hora), para ordenar primeiro por data e depois por hora
            return (data, hora)

        # Ordenando os itens usando a chave de comparação
        sorted_items = sorted(items, key=get_sort_key)

        # Recolocando os itens ordenados na Treeview
        for index, item_id in enumerate(sorted_items):
            tree.move(item_id, '', index)

def mostrar_selecao(event):
    """Função para imprimir o item selecionado"""
    logging.info(f"Selecionado: {combo.get()}")

def formatar_data(entry, event):
    valor = entry.get()
    valor = valor.replace("/", "")  # Remove "/" para facilitar a formatação

    if len(valor) > 2:
        valor = valor[:2] + "/" + valor[2:]
    if len(valor) > 5:
        valor = valor[:5] + "/" + valor[5:]

    entry.delete(0, END)  # Limpa a entrada
    entry.insert(0, valor)  # Insere a string formatada

def returndatetimeatual():
    
        dia = str(datetime.now().day)
        mes = str(datetime.now().month)
        ano = str(datetime.now().year)
        hora = str(datetime.now().hour)
        minuto = str(datetime.now().minute)
        segundo = str(datetime.now().second)
        
        if int(dia) < 10:
            dia = "0" + dia
        if int(mes) < 10:
            mes = "0" + mes 
        if int(hora) < 10:
            hora = "0" + hora
        if int(minuto) < 10:
            minuto = "0" + minuto
        if int(segundo) < 10:
            segundo = "0" + segundo 

        return "Atualizado em: " +dia+"/"+mes+"/"+ano+" "+hora+":"+minuto+":"+segundo

def salvar():
    exportar_para_csv(tree)

    estado_ema = ''
    estado_eventos = ''    

    if checkbox_ema.get() == 1:
        estado_ema = "true"
    elif checkbox_ema.get() == 0:
        estado_ema = "false"

    if checkbox_grid.get() == 1:
        estado_eventos = "true"
    elif checkbox_grid.get() == 0:
        estado_eventos = "false"

    estado_somente_rel = "true" if checkbox_busca.get() == 1 else "false"

    criar_arquivo_xml("config.xml",email_entry.get(),refresh_entry.get(),entry_email2.get(),estado_ema,estado_eventos,estado_somente_rel)

def exportar_para_csv(treeview, nome_arquivo="data.csv"):

 try:

    """
    Exporta os dados da Treeview para um arquivo CSV.
    """
    dados = treeview.get_children()
    colunas = treeview["columns"]
    
    with open(nome_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Escreve os cabeçalhos
        csv_writer.writerow(colunas)
        
        # Escreve os dados
        for item in dados:
            values = treeview.item(item, "values")
            csv_writer.writerow(values)
         
        messagebox.showinfo("Streaming_Scheduler","Dados exportados para:" + (nome_arquivo))

 
 except FileNotFoundError as e:
  logging.error(f"Arquivo não encontrado = {e}")
 except Exception as e: 
  logging.error(f"Erro ocorrido: {e}") 
  exc_type, exc_obj, exc_tb = sys.exc_info()
  fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
  habilita_botoes()
  text =f"Streaming Scheduler error: {e}"
  pass
 
def safe_tree_delete(tree, iid):
    try:
        if tree.exists(iid):
            tree.delete(iid)
    except Exception:
        pass

def limpar_treeview():
    global _eventos_iniciados
    try:
        _eventos_iniciados.clear()
    except Exception:
        pass
    try:
        for item in list(tree.get_children()):
            if tree.exists(item):
                try:
                    tree.delete(item)
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Erro ao limpar Treeview: {e}")
    finally:
        try:
            tree.update_idletasks()
        except Exception:
            pass
        
def delete_null_items():
    # Itera por todos os itens do Treeview
    for item in tree.get_children():
        # Obtém os valores associados ao item (retorna uma tupla)
        values = tree.item(item, "values")
        # Verifica se algum valor (convertido para string e em minúsculo) é "null"
        if any(str(value).strip().lower() == "null" for value in values):
            tree.delete(item)

def autoajustar_colunas(tree, ignorar=None, padding=10):
    """
    Ajusta a largura de cada coluna do Treeview com base no conteúdo (cabeçalho e itens),
    exceto aquelas especificadas em 'ignorar'.

    :param tree: widget Treeview
    :param ignorar: lista de nomes de colunas a serem ignoradas durante o ajuste
    :param padding: valor extra em pixels a ser adicionado à largura calculada
    """
    if ignorar is None:
        ignorar = []

    # Utiliza a fonte padrão do Treeview (ou defina outra, se necessário)
    fonte = tkFont.nametofont("TkDefaultFont")

    # Percorre cada coluna definida no Treeview
    for col in tree["columns"]:
        # Se a coluna estiver na lista de ignoradas, pula este loop
        if col in ignorar:
            continue

        max_width = 0
        
        # Mede a largura do cabeçalho da coluna
        header_text = tree.heading(col)["text"]
        max_width = fonte.measure(header_text)

        # Percorre todos os itens para medir o comprimento do conteúdo
        for item in tree.get_children():
            item_text = tree.set(item, col)
            largura_item = fonte.measure(item_text)
            if largura_item > max_width:
                max_width = largura_item

        # Define a largura da coluna com um padding extra
        tree.column(col, width=max_width + padding)

def remover_duplicatas(tree):
    """
    Remove itens duplicados do Treeview de forma totalmente segura.
    Versão corrigida para evitar erro 'Item not found'.
    
    Parâmetros:
        tree: Objeto Treeview a ser processado
        
    Retorno:
        Número de itens duplicados removidos
    """
    try:
        # Dicionário para armazenar chaves únicas {chave: id_item}
        itens_unicos = {}
        duplicatas = 0
        itens_para_remover = set()  # Armazena IDs dos itens a remover
        
        # Colunas que definem unicidade (Campeonato, Partida, Data, Horário, Plataforma)
        colunas_chave = [0, 1, 2, 3, 6]
        
        # Primeira passada: identificar duplicatas
        for item in tree.get_children():
            values = tree.item(item, 'values')
            
            try:
                # Chave agressiva: Jogo normalizado (FUZZY) e Data
                # Usa deep_normalize_match para detectar 'Vasco' vs 'Vasco da Gama'
                jogo_fuzzy = deep_normalize_match(values[1])
                data_val = str(values[2])
                chave = (jogo_fuzzy, data_val)
            except (IndexError, TypeError, AttributeError) as e:
                logging.warning(f"Item {item} com valores inválidos: {values} - {str(e)}")
                continue
            
            if chave in itens_unicos:
                item_existente = itens_unicos[chave]
                values_exist = tree.item(item_existente, 'values')
                
                # Regra de Prioridade: Plataforma de Streaming Oficial > CBF (PDF)
                camp_exist = str(values_exist[0]).upper() if len(values_exist) > 0 else ""
                url_exist = str(values_exist[7]).lower() if len(values_exist) > 7 else ""
                is_cbf_exist = "CBF" in camp_exist or url_exist.endswith(".pdf")
                
                camp_novo = str(values[0]).upper() if len(values) > 0 else ""
                url_novo = str(values[7]).lower() if len(values) > 7 else ""
                is_cbf_novo = "CBF" in camp_novo or url_novo.endswith(".pdf")
                
                if is_cbf_exist and not is_cbf_novo:
                    # O item existente é da CBF e o novo é da plataforma direta: Descarta a CBF e mantém a plataforma!
                    itens_para_remover.add(item_existente)
                    itens_unicos[chave] = item
                else:
                    # O item existente já é da plataforma ou ambos são do mesmo tipo: Descarta o novo
                    itens_para_remover.add(item)
                duplicatas += 1
            else:
                itens_unicos[chave] = item
        
        # Segunda passada: remoção segura
        for item in itens_para_remover:
            try:
                if tree.exists(item):  # Verifica se o item ainda existe
                    tree.delete(item)
            except Exception as e:
                logging.warning(f"Erro ao remover item {item}: {str(e)}")
                habilita_botoes()
                continue
        
        logging.info(f"Removidas {duplicatas} duplicatas com segurança")
        return duplicatas
        
    except Exception as e:
        error_msg = f"Erro crítico ao remover duplicatas: {str(e)}"
        logging.error(error_msg, exc_info=True)
        habilita_botoes()
        raise RuntimeError(error_msg) from e

def sort_by_date(tree, col, reverse=False):
    from datetime import datetime
    data_list = []
    
    for item in tree.get_children(''):
        date_str = tree.set(item, col)
      
        try:
            date_obj = datetime.strptime(date_str.strip(), "%d/%m/%Y")
            data_list.append((date_obj, item))
        except ValueError as e:
            logging.error(e)
            continue

    data_list.sort(reverse=reverse, key=lambda t: t[0])

    for index, (_, item) in enumerate(data_list):
        tree.move(item, '', index)

    tree.heading(col, command=lambda: sort_by_date(tree, col, not reverse))

def load_csv_new():
        

    # # Defining the columns to read
    # usecols = ["Data", "Horário","Campeonato", "Partida", "Canal de Transmissão", "Url"]
    # data = pd.read_csv(dir_final, usecols=usecols)
    # df = pd.DataFrame(data)


    data_string = entry_data.get()
    formato = "%d/%m/%Y"
    data_objeto = datetime.strptime(data_string, formato)

    # Abre a caixa de diálogo para selecionar o arquivo CSV
    file_path = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
            # Limpa o TreeView
            for item in tree.get_children():
                tree.delete(item)
            # Lê o arquivo CSV
            try:
                
                with open(file_path, 'r',encoding='utf-8',newline='' ) as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    # next(csv_reader)  # Pula a linha de cabeçalho (opcional)
                    # Insere os dados no TreeView
                    for indice,row in enumerate(csv_reader):

                         data_string = str(row['Data'])
                         url_string = str(row['Url'])

                         if data_string != '' and url_string != ''  :
                          formato = "%d/%m/%Y"
                          data_csv = datetime.strptime(data_string, formato)

                          if data_csv >= data_objeto:
                            
                            if 'Prime' in str(row['Canal de Transmissão']):
                                user_stream = user_entry_prime.get()
                                pass_stream = pass_entry_prime.get()
                            elif 'Disney' in str(row['Canal de Transmissão']):
                                user_stream = user_entry_dazn.get()
                                pass_stream = pass_entry_dazn.get()

                            if indice % 2 == 0:
                             csv_list = (str(row['Campeonato']),str(row['Partida']),str(row['Data']),str(row['Horário']),"Esquerda",str(row('Min antes para ação')),str(row['Canal de Transmissão']),str(row['Url']))
                             tree.insert("", "end", values=csv_list)
                            else:
                             csv_list = (str(row['Campeonato']),str(row['Partida']),str(row['Data']),str(row['Horário']),"Direita",str(row('Min antes para ação')),str(row['Canal de Transmissão']),str(row['Url']))
                             tree.insert("", "end", values=csv_list)

            except FileNotFoundError as e:
                logging.error(f"Arquivo não encontrado = {e}")
            except Exception as e: 
                logging.error(f"Erro ocorrido: {e}") 
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                habilita_botoes()
                text=f"Streaming Scheduler error: {e}"
            pass
    
def load_csv_inicio():
       
       data_string = entry_data.get()
       formato = "%d/%m/%Y"
       data_objeto = datetime.strptime(data_string, formato)
       
       for item in tree.get_children():
                tree.delete(item)
            # Lê o arquivo CSV
       try:
                
                with open('data.csv', 'r',encoding='utf-8',newline='' ) as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    # next(csv_reader)  # Pula a linha de cabeçalho (opcional)
                    # Insere os dados no TreeView
                    for indice,row in enumerate(csv_reader):

                         data_string = str(row['Data'])
                         url_string = str(row['Url'])

                         if data_string != '' and url_string != ''  :
                          formato = "%d/%m/%Y"
                          data_csv = datetime.strptime(data_string, formato)

                          if data_csv >= data_objeto:
                               
                            if indice % 2 == 0:
                             csv_list = (str(row['Campeonato']),str(row['Partida']),str(row['Data']),str(row['Horário']),"Esquerda",str(row['Min antes para ação']),str(row['Canal de Transmissão']),str(row['Url']))
                             tree.insert("", "end", values=csv_list)
                            else:
                             csv_list = (str(row['Campeonato']),str(row['Partida']),str(row['Data']),str(row['Horário']),"Direita",str(row['Min antes para ação']),str(row['Canal de Transmissão']),str(row['Url']))
                             tree.insert("", "end", values=csv_list)

       except FileNotFoundError as e:
                logging.error(f"Arquivo não encontrado = {e}")
       except Exception as e: 
                logging.error(f"Erro ocorrido: {e}") 
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                habilita_botoes()        
                text =f"Streaming Scheduler error:{e}"
                pass

def load_csv():
    cwd = os.path.realpath('.')
    file = "data.csv"
    dir_final = os.path.join(cwd,file)
    with open(dir_final) as myfile:
        csvread = csv.reader(myfile, delimiter=',')
        
        for row in csvread:
            tree.insert("", 'end', values=row)
        
    tree.tag_configure('t1', background='#cccccc')
    tree.tag_configure('t2', background='white')
    tree.tag_configure('t3', foreground='white',background='red')

    tree.pack(side=BOTTOM, expand=False, fill=BOTH)

    # fechar todos chromes:
    
    for pid in get_pids("chrome"):
        os.kill(pid, signal.SIGTERM) #or signal

def event_closedwindow():

     for pid in get_pids("start"):
        os.kill(pid, signal.SIGTERM) #or

     resp = messagebox.askyesno("Streaming_Scheduler", "Você quer salvar a configuração atual antes de sair?") 

     if resp:
         salvar()
         text ="Configurações salvas com sucesso"
         root.destroy()
     else:
         root.destroy()

def save_csv():
    cwd = os.path.realpath('.')
    file = "data.csv"
    dir_final = os.path.join(cwd,file)
    
    with open(dir_final, "w", newline='') as myfile:
        csvwriter = csv.writer(myfile, delimiter=',')
        
        for row_id in tree.get_children():
            row = tree.item(row_id)['values']
            csvwriter.writerow(row)
    if messagebox.askokcancel("Streaming_Scheduler", "Você quer realmente sair da aplicação?"):
         root.destroy()

def delete():
   # Get selected item to Delete
   selected_item = tree.selection()[0]
   tree.delete(selected_item)

def add():
   # Get selected item to Delete
  atualizaPercentGrid()

def connectSharepoint():

   cred = HttpNtlmAuth('cleber.goncalves@kantaribopemedia.com', 'Kim1818@!')
   site = Site('https://ktglbuc.sharepoint.com/sites/kim-suportecap/Lists/Projeto%20LiveMode%20%20Caze%20TV/AllItems.aspx', auth=cred)

   sp_list = site.List('#SharePoint_list name here') # this creates SharePlum object
   data = sp_list.GetListItems('All Items') # this will retrieve all items from list

def get_pids(name):
    for proc in psutil.process_iter():
        if name in proc.name():
           yield proc.pid

def update_chrome1():
    # 9222
    try:
       
        cwd = os.path.realpath('.')
        dir_final = os.path.join(cwd, "TempProfile")
        os.makedirs(dir_final, exist_ok=True)
        chromeadres = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chromeadres):
            chromeadres = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe")
        subprocess.Popen([
            chromeadres,
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=9222",
            f"--user-data-dir={dir_final}",
            "--profile-directory=Default",
            "--disable-features=SkipProfilePicker",
            "--no-first-run", "--no-default-browser-check",
        ])
    except Exception as e:
        logging.error(f"Erro ao iniciar Chrome 9222: {e}")

def update_chrome2():
    # 9224
    try:
       
        cwd = os.path.realpath('.')
        dir_final = os.path.join(cwd, "TempProfile2")
        os.makedirs(dir_final, exist_ok=True)
        chromeadres = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chromeadres):
            chromeadres = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe")
        subprocess.Popen([
            chromeadres,
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=9224",
            f"--user-data-dir={dir_final}",
            "--profile-directory=Default",
            "--disable-features=SkipProfilePicker",
            "--no-first-run", "--no-default-browser-check",
        ])
    except Exception as e:
        logging.error(f"Erro ao iniciar Chrome 9224: {e}")



def tentar_reproduzir_evento(driver, url):
    try:
        driver.get(url)
        time.sleep(4)
        banner_youtube = driver.find_elements(By.CSS_SELECTOR, '//*[@id="dismiss-button"]/yt-button-shape/button')

        if len(banner_youtube) > 0:
            banner_youtube[0].click()
     
      
        # Se não está tocando, tenta clicar no botão de play se ele existir
        try:
            play_button = driver.find_element(By.CSS_SELECTOR, "button.ytp-large-play-button")
            play_button.click()
            return True
        except:
            # Se não há botão, assume que está tocando ou prestes a tocar
            return True

    except Exception as e:

        logging.error(f"❌ Erro ao tentar reproduzir evento: {e}")
        habilita_botoes()
        return False

_loop_verificacao_id = None

def update_command():
    global _loop_verificacao_id

    try:
        if button_update["text"] == "Running":
            button_update["text"] = "Start"
            button_update["fg"] = "green"

            if _loop_verificacao_id is not None:
                try:
                    root.after_cancel(_loop_verificacao_id)
                except Exception:
                    pass
                _loop_verificacao_id = None
            return

        if button_update["text"] == "Start":
            button_update["text"] = "Running"
            button_update["fg"] = "red"
            loop_verificacao()
            return

    except Exception as e:
        logging.exception(f"Erro em update_command: {e}")

def loop_verificacao():
    global _loop_verificacao_id
    if button_update["text"] == "Running":
        iniciar_thread(run_app)
        try:
            num_refresh = int(refresh_entry.get())
        except Exception:
            num_refresh = 20
        intervalo_ms = max(5, num_refresh) * 1000
        _loop_verificacao_id = root.after(intervalo_ms, loop_verificacao)
 
def iniciar_thread(metodo):
    """Inicia a thread e captura erros com log e envio para Telegram"""

    def wrapper():
        try:
            metodo()
        except Exception as e:
            mensagem_erro = traceback.format_exc()
            logging.error(mensagem_erro)
            # enviar_erro_telegram("ERROR", mensagem_erro)

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()

def lerCSV():

    cwd = os.path.realpath('.')
    file = 'Programação de eventos - Streaming.csv'
    dir_final = os.path.join(cwd,file)

    csv_list = ()
    list_b = list(csv_list)

 
    # Defining the columns to read
    usecols = ["Data", "Horário","Campeonato", "Partida", "Canal de Transmissão", "Url"]
    data = pd.read_csv(dir_final, usecols=usecols)
    df = pd.DataFrame(data)


    data_string = entry_data.get()
    formato = "%d/%m/%Y"
    data_objeto = datetime.strptime(data_string, formato)

   # Iterating over rows
    for index, row in df.iterrows():

       data_string = str(row['Data'])
       url_string = str(row['Url'])

       if data_string != 'nan' and url_string != 'nan'  :
        formato = "%d/%m/%Y"
        data_csv = datetime.strptime(data_string, formato)

        if data_csv >= data_objeto:

         csv_list = (row['Data'],row['Horário'],row['Campeonato'],row['Partida'],row['Canal de Transmissão'],row['Url'])

         list_b.append(csv_list)
       
  
    return list_b



def verificar_e_clicar(botao):
    """
    Verifica se um botão (obtido pela função get_botao_func) 
    está com texto 'Start' por mais de 10 minutos.
    Se sim, clica no botão.
    """
    logging.info("[INFO] Iniciando monitoramento do botão...")

    tempo_inicial = None

    while True:
        try:

            texto = botao.cget("text")
      
            if texto.lower() == "start":
                if tempo_inicial is None:
                    tempo_inicial = time.time()
                    logging.info("[INFO] Botão 'Start' detectado. Iniciando contagem...")
                    habilita_botoes()
                elif time.time() - tempo_inicial >= 600:
                    logging.info("[INFO] Botão ficou 'Start' por mais de 10 minutos. Clicando...")
                    update_command()
                    tempo_inicial = None
            else:
                if tempo_inicial is not None:
                    logging.info("[INFO] Texto mudou. Resetando contagem.")
                tempo_inicial = None

        except Exception as e:
            logging.error(f"[WARNING] Erro ao acessar o botão: {e}")
            habilita_botoes()
            tempo_inicial = None

        time.sleep(600)  # Verifica a cada 10 minutos


def iniciar_monitoramento(entry_horario, funcao):
    pass

def monitorar_horario(entry_horario, funcao):
    pass
            
def executar_funcao():
    global thread_em_execucao
    if thread_em_execucao:
        logging.info("[INFO] Já está em execução. Ignorado.")
        text="[INFO] Já está em execução. Ignorado."
        return

    thread_em_execucao = True
    try:
        logging.info(f"[EXECUTANDO] Função executada em {datetime.now().strftime('%H:%M:%S')}")
        text=f"[EXECUTANDO] Função executada em {datetime.now().strftime('%H:%M:%S')}"
        time.sleep(10)  # Simula uma tarefa demorada
    finally:
        thread_em_execucao = False
        logging.info("[INFO] Função finalizada.")
        text="[INFO] Função finalizada."


def refresh_youtube(driver):

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        if not body.text.strip():
            logging.info("Corpo vazio ou erro de carregamento detectado")
            driver.refresh()
        
        if "Ah, bolas" in driver.title or "Aw, Snap" in driver.title:
          
            driver.refresh()  # ou driver.get(url) novamente
    except Exception as e:
        logging.info(f"Elemento body não encontrado, possível erro de carregamento: {e}")
        driver.refresh()

def _kill_all_chrome_instances(grace_seconds: float = 2.5):
    """
    Encerra TODAS as instâncias do Chrome e chromedriver.
    Usado somente no modo 'Somente relatório'.
    """
    targets = {"chrome.exe", "chromedriver.exe"}
    procs = []

    for p in psutil.process_iter(["pid", "name"]):
        try:
            if p.info["name"] and p.info["name"].lower() in targets:
                procs.append(p)
        except Exception:
            pass

    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

    _, alive = psutil.wait_procs(procs, timeout=grace_seconds)

    for p in alive:
        try:
            p.kill()
        except Exception:
            pass


def preparar_chrome_esquerda_para_relatorio():
    """
    Fluxo exclusivo para 'Somente relatório':
    - Fecha TODOS os Chromes
    - Abre apenas o Chrome ESQUERDA (9222)
    """
    logging.info("[RELATORIO] Preparando Chrome ESQUERDA (9222)")
    _kill_all_chrome_instances()
    time.sleep(1)

    update_chrome1()   # <<< já existe no seu projeto (9222)
    time.sleep(2)

    if not verificar_chrome_debug("9222"):
        raise RuntimeError("Chrome ESQUERDA (9222) não respondeu")
    

def run_app():
 
 global driverchrome
 global refreshlabel
 global refresh_entry
 global checkbox8
 global checkbox9
 global button_update
 global threadingTimer
 global driverchrome1
 global driverchrome2
 global thread_em_execucao 
 global monitoramento_ativo 

 # 1. Verificação segura do Agendamento Diário (sem travas ou conflitos)
 try:
     agora = datetime.now()
     hora_cfg = entry_email2.get().strip()
     if checkbox_grid.get() and checkbox_ema.get() and ":" in hora_cfg:
         h, m = map(int, hora_cfg.split(":"))
         alvo = agora.replace(hour=h, minute=m, second=0, microsecond=0)
         
         if agora >= alvo and _ultima_janela_envio.date() != agora.date():
             logging.info(f"[AGENDADO] Horário atingido ({hora_cfg}). Executando tarefa_diaria em segundo plano...")
             threading.Thread(target=tarefa_diaria).start()
             return
 except Exception as e:
     logging.error(f"[AGENDADO] Erro ao checar agendamento no início do run_app: {e}")

 conseguiu_trava = False
 try:                           
  
  if thread_em_execucao:
        logging.info("run_app ignorado: execução anterior ainda ativa")
        return

  thread_em_execucao = True
  conseguiu_trava = True

  status = button_update["text"]
  
#    Checar versão nova - removido do loop recorrente para evitar vazamento de sockets e threads
  desabilita_botoes()
  monitoramento_ativo = True
  
  if driverchrome1 is not None:
    refresh_youtube(driverchrome1)
  if driverchrome2 is not None:
    refresh_youtube(driverchrome2)


  if  status == "Running":
      
    
   cwd = os.path.realpath('.')
   file = "data.csv"
   dir_final = os.path.join(cwd,file)
    
   ui_safe(lambda: label_toolbarprocess.config(text=returndatetimeatual()))
   progresso["value"] = 0
#    Exibe progressbar
   progresso.pack(side=RIGHT, padx=10, pady=5)

   i = 0

   if not checkbox_busca.get():

    for parent in tree.get_children():

     if tree.get_children():

      i = progresso['value']
      progresso["value"] = i +10
      time.sleep(0.5)
         
      plataform =  tree.item(parent)["values"][6]
      datastr = tree.item(parent)["values"][2]
      datatemp = datetime.strptime(datastr, '%d/%m/%Y').date()
      dataatual = date.today()
     
      if datatemp == dataatual:
      
       i = i + 1
       horastr = tree.item(parent)["values"][3]
       horatemp = datetime.combine(datatemp,datetime.strptime(horastr, '%H:%M').time())
       timeantes = int(tree.item(parent)["values"][5])
       horasubt = horatemp - timedelta(hours=0, minutes=timeantes)
       horasubt2 = horasubt.strftime("%H:%M")
       horatemp_time_format = datetime.strptime(horasubt2,'%H:%M').time()

       hora_minuto = datetime.now().strftime("%H:%M")
       horaatual_time_format = datetime.strptime(hora_minuto,'%H:%M').time()

       if horaatual_time_format >= horatemp_time_format:
       
        if plataform == "Dazn":
         user =  get_config_value("usuario_dazn")
         pas = get_config_value("senha_dazn")  
        elif plataform == "Amazon Prime":
         user =  get_config_value("usuario_prime")
         pas = get_config_value("senha_prime") 
        elif plataform == "Disney":
         user =  get_config_value("usuario_disney")
         pas = get_config_value("senha_disney") 
        elif plataform == "Max":
         user =  get_config_value("usuario_max")
         pas = get_config_value("senha_max") 
       
        url = tree.item(parent)["values"][7]
        evento = tree.item(parent)["values"][1]

        navegador = str.upper(tree.item(parent)["values"][4])

        chrome_1 = "ESQUERDA"
        chrome_2 = "DIREITA"
                     
    #    Checa se o checkChrome esta ativado:
        if navegador == chrome_1 :
        
         if driverchrome1 is not None:
             try:
                 driverchrome1.quit()
             except Exception:
                 pass
             driverchrome1 = None

         opt = Options()
         opt.add_argument("--js-flags=--max_old_space_size=4096")
         opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

         service = Service(ChromeDriverManager().install())
         driverchrome1 = webdriver.Chrome(service=service, options=opt)
         # Localizando Prime Video
         if re.search('\\bprime\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          driverchrome1.get("https://www.primevideo.com/offers/nonprimehomepage/ref=atv_auth_signout")
        
        #   time.sleep(4)
          loginprime(url,user,pas,driverchrome1,timeantes,evento)
          break;
         
          # Localizando Disney Plus
         elif re.search('\\bdazn\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))                
        #   time.sleep(4)
          logindazn(url,user,pas,driverchrome1,timeantes,evento)
          break;
                        
                  # Localizando Disney Plus
         elif re.search('\\bcaze\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          ret = tentar_reproduzir_evento(driverchrome1,url)
          if ret:
             ui_safe(lambda:  label_toolbar.config(text="Em reprodução youtube "+evento))
                        
          break;
       
        elif re.search('\\bdisney\\b', plataform, re.IGNORECASE):
          ui_safe(lambda: label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          driverchrome1.get("https://www.disneyplus.com/identity/login/enter-email")
        #   time.sleep(4)
          logindisney(url,user,pas,driverchrome1,timeantes,evento)
          break;
        
        elif re.search('\\bmax\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          driverchrome1.get("https://auth.hbomax.com/login")
        #   time.sleep(4)
          loginmax("",url,user,pas,driverchrome1,timeantes,evento)
          break;

        
        elif navegador == chrome_2 :
  
         if not verificar_chrome_debug("9224"):
            habilita_botoes()
            ui_safe(lambda:  label_toolbar.config(text="Chrome (9224) indisponível."))
            return

         if driverchrome2 is not None:
             try:
                 driverchrome2.quit()
             except Exception:
                 pass
             driverchrome2 = None

         chrome_options = Options()
         chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
         chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9224")

         service = Service(ChromeDriverManager().install())
         driverchrome2 = webdriver.Chrome(service=service, options=chrome_options)
     
         # Localizando Prime Video
         if re.search('\\bprime\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da direita a pagina do : "+plataform))
          driverchrome2.get("https://www.primevideo.com/offers/nonprimehomepage/ref=atv_auth_signout")
        #   time.sleep(4)

          loginprime(url,user,pas,driverchrome2,timeantes,evento)
          break;
         
         elif re.search('\\bdazn\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))              
        #   time.sleep(4)
          logindazn(url,user,pas,driverchrome2,timeantes,evento)
          break;
                      
         
         elif re.search('\\bcaze\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          ret = tentar_reproduzir_evento(driverchrome2,url)
          if ret:
             ui_safe(lambda:  label_toolbar.config(text="Em reprodução youtube "+evento))

          # Localizando Disney Plus
         elif re.search('\\bdisney\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da direita a pagina do : "+plataform))
          driverchrome2.get("https://www.disneyplus.com/identity/login/enter-email")
        #   time.sleep(4)
          logindisney(url,user,pas,driverchrome2,timeantes,evento)
          break;
   
        elif re.search('\\bmax\\b', plataform, re.IGNORECASE):
          ui_safe(lambda:  label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform))
          driverchrome2.get("https://auth.hbomax.com/login")
        #   time.sleep(4)
          loginmax(url,user,pas,driverchrome2,timeantes,evento)
          break;
         
   progresso.pack_forget()
   habilita_botoes()
   label_toolbarprocess.config(text="")


 except TclError as e:
    logging.error(f"Erro ocorrido: {e}") 
    habilita_botoes()
    pass

 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes()         
         update_command()
         pass
 
 finally:
        if conseguiu_trava:
            thread_em_execucao = False

        try:
            gc.collect()
        except Exception:
            pass

def ui_safe(fn):
    try:
        root.after(0, fn)
    except Exception:
        pass

def obter_titulo_janelas():
    """ Obtém os títulos das janelas do Chrome via subprocess WMIC """
    comando = 'wmic process where "name=\'chrome.exe\'" get commandline'
    resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
    
    linhas = resultado.stdout.strip().split("\n")
    for linha in linhas:
        logging.info(f"Janela encontrada: {linha}")
   
def updatetree(tree,data):
 
    with open(data, "w", newline='') as myfile:
        csvwriter = csv.writer(myfile, delimiter=',')
        
        for row_id in tree.get_children():
            row = tree.item(row_id)['values']
            csvwriter.writerow(row)

    for i in tree.get_children():
     tree.delete(i)

    with open(data) as myfile:
        csvread = csv.reader(myfile, delimiter=',')
        
        for row in csvread:
            tree.insert("", 'end', values=row)
    
    tree.tag_configure('t1', background='#cccccc')
    tree.tag_configure('t2', background='white')
    tree.tag_configure('t3', foreground='white',background='red')

    tree.pack(side=BOTTOM, expand=False, fill=BOTH)



def resolve_banners_Dazn(driver):
   
    banner = driver.find_elements(By.CLASS_NAME,'content-promotion__modal-close___2MB1S')
    if len(banner) > 0:
        banner[0].click()

    banner2 = driver.find_elements(By.XPATH,' //*[@id="notification-layer"]/div/div/div[1]/div/div[5]/div[2]/button')
    if len(banner2) > 0:
        banner2[0].click()   


def obter_eventos_dazn_completo(driver):
    url = "https://www.dazn.com/pt-BR/competition/Competition:dc4k1xh2984zbypbnunk7ncic"
    driver.get(url)
    time.sleep(5)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
    time.sleep(2)
    orig_size = driver.get_window_size()
    driver.maximize_window()
    
    eventos = []
    titulos_ja_adicionados = set()

    resolve_banners_Dazn(driver)
 
    while True:
        # Coleta apenas os artigos da seção "A seguir"
        artigos = driver.find_elements(
            By.XPATH,
            '//h2[contains(text(), "A seguir")]/ancestor::div[contains(@class, "rail__rail-title")]/following-sibling::div//article'
        )

        for artigo in artigos:
            try:
                link_tag = artigo.find_element(By.CSS_SELECTOR, 'a.tile__link___vuQG1')

                titulo = link_tag.find_element(By.CSS_SELECTOR, 'h4').text.strip()
                campeonato = link_tag.find_element(By.CSS_SELECTOR, 'p').text.strip()
                horario = link_tag.find_element(By.CSS_SELECTOR, 'li span').text.strip()
                url_evento = link_tag.get_attribute('href')
                data_hora = converter_para_data_hora(horario)

                data_hora = re.sub(r'(\d{2}/\d{2}/\d{4})\s.*?\s(\d{2}:\d{2})', r'\1 \2', data_hora)

                # Evita duplicados com base no título
                if titulo and campeonato and horario != "":
                   eventos.append({
                    "Campeonato": campeonato,
                    "Jogo": titulo,
                    "Data/hora": data_hora,
                    "URL": url_evento
                    })
                   titulos_ja_adicionados.add(titulo)
             
            except Exception as e:
                continue

        # Tenta clicar na seta ">"
        try:
            
            seta_direita = driver.find_elements(By.XPATH, "//button[contains(@class, 'slick-next')]")
            # seta_direita = WebDriverWait(driver, 2).until(
                
            #     # EC.element_to_be_clickable((By.XPATH, '//*[@id="hob-tab-content"]/div/section/section[3]/div/div[2]/button[2]'))
            #      EC.element_to_be_clickable((By.XPATH,"button[@class='slick-arrow slick-next rail__rail-next-button___1E79l']"))
            # )
          
            if len(seta_direita) > 0:
                 ActionChains(driver).move_to_element(seta_direita[1]).click().perform()
            time.sleep(3)
            # classe_botao = seta_direita.get_attribute("class")
            classe_botao = driver.find_elements(By.XPATH, "//button[contains(@class, 'next') and contains(@class, 'disable')]")
            if len(classe_botao) > 0:
                break            
        except:
            break  # não há mais botão ou algo deu errado

    driver.set_window_size(orig_size['width'], orig_size['height'])
    return eventos

def converter_para_data_hora(texto):
    """
    Converte textos como:
    - 'Hoje: 20:40'
    - 'Amanhã: 21:10'
    - '21/01/2026 19:40'
    Retorna (data_str, hora_str) ou (None, None) se inválido
    """
    if not texto:
        return None, None

    texto = texto.strip()
    agora = datetime.now()

    try:
        # --- HOJE ---
        if texto.lower().startswith("hoje"):
            hora = texto.split(":")[-1].strip()
            data = agora.strftime("%d/%m/%Y")
            return data, hora

        # --- AMANHÃ ---
        if texto.lower().startswith("amanh"):
            hora = texto.split(":")[-1].strip()
            data = (agora + timedelta(days=1)).strftime("%d/%m/%Y")
            return data, hora

        # --- DATA COMPLETA ---
        if " " in texto:
            data, hora = texto.split(" ", 1)
            datetime.strptime(data, "%d/%m/%Y")  # valida
            return data, hora.strip()

        # --- SOMENTE DATA ---
        datetime.strptime(texto, "%d/%m/%Y")
        return texto, "00:00"

    except Exception:
        return None, None

        return "Data inválida"

def logindazn(url,email,senha,driver,timeantes,evento):
    # Acessa diretamente a URL de login
    driver.get("https://www.dazn.com/pt-BR/account/content/dazn/signup?signin=true&page=emailDetails")
    time.sleep(5)
    




    button = driver.find_elements(By.XPATH,'//*[@id="onetrust-accept-btn-handler"]')
    
    if len(button) > 0:
    
        button[0].click()
        

        text="Efetuando o login no site do DAZN..."

        # Aguarda o campo de e-mail estar disponível
        time.sleep(3)
        input_email = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        input_email.clear()
        input_email.send_keys(email)
        input_email.send_keys(Keys.ENTER)
        input_email.send_keys(email)
        input_email.send_keys(Keys.ENTER)
        text="Inserido usuario!"

        # Aguarda o campo de senha carregar
        time.sleep(2)
        input_senha = driver.find_element(By.XPATH, '//*[@id="password"]')
        input_senha.send_keys(senha)
        input_senha.send_keys(Keys.ENTER)
        text="Inserido senha!"

        # Aguarda possível redirecionamento pós-login
        time.sleep(8)

        driver.get(url)
        time.sleep(4)
        for _ in range(5):
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            time.sleep(2)

        # Verifica se login teve sucesso com base na URL
        if "home" in driver.current_url or "account" in driver.current_url:
            text="✅ Login realizado com sucesso!"
            return True
        else:
            text="❌ Falha no login ou autenticação adicional necessária."
            return False

    else:
         text="✅ Login realizado com sucesso!"
        
    driver.get(url)

    resolve_banners_Dazn(driver)


def clicar_com_espera_segura(driver, xpath, timeout=10):
    try:
        elemento = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView();", elemento)
        driver.execute_script("arguments[0].click();", elemento)
    except ElementClickInterceptedException:
        logging.info("⚠️ Elemento interceptado! Tentando novamente com JS após delay.")
        time.sleep(1)
        try:
            elemento = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", elemento)
        except Exception as e:
           logging.info(f"❌ Falha definitiva ao clicar: {e}")
    except TimeoutException:
        logging.error("❌ Timeout ao esperar o elemento ficar clicável.")
        
def tem_numeros(texto):
  """Verifica se a string informada possui um ou mais números."""
  return any(char.isdigit() for char in texto)


def loginprime(url,us,passw,driver,tempo,evento):

 global driverchrome
#   user prime = 11983539427 pass prime = D15m0321

  
#  tamanho_normal = driver.get_window_size()

 try: 
 
  if len(driver.find_elements(By.XPATH, '//*[@id="ap_email"]')) > 0:   
       
       label_toolbarprocess.config(text="Evento encontrado")
       progresso["value"] = 0
        #    Exibe progressbar
       progresso.pack(side=RIGHT, padx=10, pady=5)
       
       text="Buscando elemento de pagina login..."
       progresso["value"] = 10
       logging.info("Buscando elemento de pagina login!")
       user = driver.find_element(By.XPATH, '//*[@id="ap_email"]')
       t = user.get_attribute("value")
       #    user.send_keys(Keys.ENTER) 
       tuser = "+55" + str(us)
       tuser2 = "55" + str(us)
       if t == tuser or t == tuser2 or t == tuser: 
           user.send_keys(Keys.ENTER)  
       else:
       
        time.sleep(4)
        user.clear()
        time.sleep(2)
        user.send_keys(tuser)
        time.sleep(3)
        user = driver.find_element(By.XPATH, '//*[@id="ap_email"]')
        t = user.get_attribute("value")
        if tem_numeros(t):
         user.clear()
         user.send_keys(tuser)
         user = driver.find_element(By.XPATH, '//*[@id="ap_email"]')
         t = user.get_attribute("value")
         novo_valor = t.replace("+55", "", 1)
         user.clear()
         user.send_keys(novo_valor)
        
        user.send_keys(Keys.ENTER) 
        text="Buscando elemento de senha login..."
        progresso["value"] = progresso["value"] + 10
        logging.info("Buscando elemento de senha login!")
        time.sleep(4)

    #    Se identificar captcha usar a classe AmazonCaptcha para resolver
       try:   
        # frame1 =  WebDriverWait(driver, 1).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,)))     
        frame1 = clicar_com_espera_segura(driver,'//*[@id="aa-challenge-whole-page-iframe"]')
       except exceptions.TimeoutException as ex:
            logging.error(f"Não encontrou o elemento para clicar no botão, Faça manual!. {ex}")
            pass

       
       if len(driver.find_elements(By.XPATH,'//*[@id="aa_amazon_image_captcha"]')) > 0:

        link = driver.find_element(By.XPATH,'//*[@id="aa_amazon_image_captcha"]').get_attribute('src')
        catcha = AmazonCaptcha.fromlink(link)
        captcha_value = AmazonCaptcha.solve(catcha)
        input_field = driver.find_element(By.ID,"aa_captcha_input").send_keys(captcha_value)
        button = driver.find_element(By.CLASS_NAME,"a-button-input")
        button.click()
           
        time.sleep(2)

    #    Senão segue a vida pelo password
       else:
        driver.switch_to.default_content() 
        if len(driver.find_elements(By.XPATH, '//*[@id="authportal-main-section"]/div[2]/div/div[2]/div/form/div/div[2]/div/div/label/div/label/input')) > 0:     
         driver.find_element(By.XPATH, '//*[@id="authportal-main-section"]/div[2]/div/div[2]/div/form/div/div[2]/div/div/label/div/label/input').click() 

       pas = driver.find_element(By.XPATH, '//*[@id="ap_password"]')
       pas.clear()
       pas.send_keys(passw) 
       pas.send_keys(Keys.ENTER) 
       time.sleep(3)
  progresso["value"] = progresso["value"] + 10
  text="Abrindo a URL do evento: "+evento
  
  driver.get(url)

#   Se após a autenticação mostrar o botão de login do prime maximizar clicar e voltar ao normal a janela
  text="Checando necessidade de reautenticação..."
  if len(driver.find_elements(By.XPATH, '//*[@id="pv-nav-container"]/div/div[2]/ul/li[5]/a')) > 0:  

        #  tamanho_normal = driver.get_window_size()
        #  driver.maximize_window()
         time.sleep(3)
         driver.find_element(By.XPATH, '//*[@id="pv-nav-container"]/div/div[2]/ul/li[5]/a').click() 
        #  driver.set_window_size(tamanho_normal["width"], tamanho_normal["height"])
         time.sleep(2)
         loginprime(url,us,passw,driver,tempo,evento)

  time.sleep(5)

  minutos = tempo * 60
  
  if evento != "Novos":

    if len(driver.find_elements(By.XPATH,'//*[@class="webPlayerUIContainer"]')) > 0:  
      time.sleep(10)
   
    # driver.maximize_window()
    time.sleep(3)
    progresso["value"] = progresso["value"] + 10
    text="Aguardando presença do botão do player para o evento: "+evento
    clicar_com_espera_segura(driver,'//*[@role="button"]')
    # WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'//*[@role="button"]'))).click()


#   Botão de watch live em janela pequena apos clicar em webwait caso apareça

    if len(driver.find_elements(By.XPATH, '/html/body/div[3]/div/div/div/div[2]/div/span[3]/div/div[1]/a')) > 0:  
      text="Clicou no sub botão do player... "
      driver.find_element(By.XPATH, '/html/body/div[3]/div/div/div/div[2]/div/span[3]/div/div[1]/a').click()
      time.sleep(2)
      
   

      # Clicar no checkbox de evento mature themes
    if len(driver.find_elements(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[1]/div/div/div')) > 0:
         driver.find_element(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[1]/div/div/div').click()
         progresso["value"] = progresso["value"] + 10
         text="Clicou no check de  permissão para conteúdo sensivel..."
             
            #  Clicar no botão de evento mature themes
         time.sleep(2)
         driver.find_element(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[2]/button[2]').click()
         progresso["value"] = progresso["value"] + 10
         text="Clicou no botão para permissão para conteúdo sensivel..."
  
  # Espera até o botão estar clicável e clica
  botao_close = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Continue']"))
  )
  botao_close.click()
  progresso["value"] = 100
  text="Em reprodução do evento: "+evento
  time.sleep(2)
  label_toolbarprocess.config(text="")
  progresso.pack_forget()

#   retorna ao tamanho normal:
#   driver.set_window_size(tamanho_normal["width"], tamanho_normal["height"])

 except exceptions.TimeoutException as ex:
     pass

 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes() 
         pass
  
def loginmax(url_plataform, url, us, passw, driver, tempo, evento):
    global driverchrome

    try:

        if driver.findelements(By.XPATH,'//*[@id="header-secondary-cta"]'):


            driver.get(url_plataform)
            time.sleep(6)

            label_toolbarprocess.config(text="Evento encontrado")
            progresso["value"] = 10
            progresso.pack(side=RIGHT, padx=10, pady=5)

            text="Localizando campo de login (Shadow DOM)..."
            logging.info("Localizando campo de login (Shadow DOM)")

            # ================================
            # LOGIN (EMAIL / TELEFONE)
            # ================================
            user = driver.execute_script("""
                const giLogin = document.querySelector('gi-login');
                if (!giLogin) return null;

                const root1 = giLogin.shadowRoot;
                if (!root1) return null;

                const emailComp = root1.querySelector('gi-sign-in-email');
                if (!emailComp) return null;

                const root2 = emailComp.shadowRoot;
                if (!root2) return null;

                const input = root2.querySelector('#sign-in-email-input');
                return input;
            """)

            if user is None:
                raise Exception("Campo de login não encontrado (Shadow DOM)")


            driver.execute_script("arguments[0].value = '';", user)
            user.send_keys(us)
            user.send_keys(Keys.ENTER)

            progresso["value"] += 20
        
            time.sleep(6)

            # ================================
            # SENHA
            # ================================
            text="Localizando campo de senha (Shadow DOM)..."

            password = driver.execute_script("""
                const giLogin = document.querySelector("gi-login");
                if (!giLogin || !giLogin.shadowRoot) return null;

                const passStep = giLogin.shadowRoot.querySelector("gi-sign-in-password");
                if (!passStep || !passStep.shadowRoot) return null;

                const pwdComp = passStep.shadowRoot.querySelector("gi-password-input");
                if (!pwdComp || !pwdComp.shadowRoot) return null;

                return pwdComp.shadowRoot.querySelector('input[type="password"]');
            """)

            if password is not None:
            
                driver.execute_script("arguments[0].value = '';", password)
                password.send_keys(passw)
                password.send_keys(Keys.ENTER)

                progresso["value"] += 20
                time.sleep(6)

        # ================================
        # ABRIR EVENTO
        # ================================
        text="Abrindo evento: " + evento
        driver.get(url)
        time.sleep(5)

        if evento != "Novos":
            if len(driver.find_elements(By.XPATH, '//*[@class="webPlayerUIContainer"]')) > 0:
                time.sleep(8)

            progresso["value"] += 20
            text="Ativando player..."
            clicar_com_espera_segura(driver, '//*[@role="button"]')

        # ================================
        # FINAL
        # ================================
        progresso["value"] = 100
        text="Em reprodução do evento: " + evento
        label_toolbarprocess.config(text="")
        progresso.pack_forget()

    except Exception as e:
        logging.error(f"Erro ocorrido: {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        habilita_botoes()
        
def find_in_shadow(driver, selectors):
    script = "let el = document;"
    for sel in selectors:
        script += f"""
        el = el.querySelector('{sel}');
        if (!el) return null;
        if (el.shadowRoot) el = el.shadowRoot;
        """
    script += "return el;"
    return driver.execute_script(script)

     
def logindisney(url,us,passw,driver,tempo,evento):


#   user prime = 11983539427 pass prime = D15m0321

 global driverchrome
#   user prime = 11983539427 pass prime = D15m0321

  
#  tamanho_normal = driver.get_window_size()

 try: 
  
  time.sleep(4)
 
  if len(driver.find_elements(By.XPATH, '//*[@id="email"]')) > 0:   
       
       label_toolbarprocess.config(text="Evento encontrado")
       progresso["value"] = 0
        #    Exibe progressbar
       progresso.pack(side=RIGHT, padx=10, pady=5)
       
       logging.info(text="Buscando elemento de pagina login...")
       progresso["value"] = 10
       logging.info("Buscando elemento de pagina login!")
       user = driver.find_element(By.XPATH, '//*[@id="email"]')
       t = user.get_attribute("value")
    #    user.send_keys(Keys.ENTER) 
       tuser = str(us)
     
       if t == tuser : 
           user.send_keys(Keys.ENTER)  
       else:
        time.sleep(4)
        user.clear()
        time.sleep(2)
        user.send_keys(tuser)
        time.sleep(3)
        user.send_keys(Keys.ENTER) 
        logging.info(text="Buscando elemento de senha login...")
        progresso["value"] = progresso["value"] + 10
        logging.info("Buscando elemento de senha login!")
        time.sleep(4)

         
        time.sleep(2)

    #    Senão segue a vida pelo password
    
       pas = driver.find_element(By.XPATH, '//*[@id="password"]')
       pas.clear()
       pas.send_keys(passw) 
       pas.send_keys(Keys.ENTER) 
       time.sleep(3)
  progresso["value"] = progresso["value"] + 10
  logging.info(text="Abrindo a URL do evento: "+evento)
  
  driver.get(url)

  time.sleep(5)

  minutos = tempo * 60
  
  if evento != "Novos":


    # driver.maximize_window()
   
    progresso["value"] = progresso["value"] + 10
    logging.info(text="Aguardando presença do botão do player para o evento: "+evento)
    time.sleep(5)
    
    # Testa no primeiro metodo o acesso

   

    element = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label="ASSISTIR"]')         
    if len(element)  > 0:
        element[0].click()   
        logging.info(text="Clicou no primeiro botão...")

        
        element2 = driver.find_elements(By.XPATH, '//a[contains(text(), "ASSISTIR AO VIVO")]')     
        if len(element2)  > 0:
                element2[0].click()  
                pass                 

    else:
     element3 = driver.find_elements(By.CSS_SELECTOR, '[data-testid="playback-action-button"]')         
     if len(element2)  > 0:
        element3[0].click()   
        logging.info(text="Não encontrou o elemento para clicar no segundo elemento botão...")
        pass

     else:   

        try:
            #  wait = WebDriverWait(driver, 5)
            #  element = wait.until(EC.element_to_be_clickable((By.XPATH,)))
             clicar_com_espera_segura(driver,'//*[@id="explore-ui-main-content-container"]/div[1]/section/div[2]/div[1]/div[8]/a')
            #  driver.execute_script("arguments[0].click();", element)        
        except exceptions.TimeoutException as ex:
            logging.info(text="Não encontrou o elemento para clicar no segundo elemento botão, Faça manual!. ")
            pass
           
    progresso["value"] = 100
    text="Em reprodução do evento: "+evento
    time.sleep(2)
    label_toolbarprocess.config(text="")
    progresso.pack_forget()

#   retorna ao tamanho normal:
#   driver.set_window_size(tamanho_normal["width"], tamanho_normal["height"])

 except exceptions.TimeoutException as ex:
     pass

 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes()
         pass

def atualizaPercentGrid():
        
     # Grid Estrategia 01
    
     newlistEstrategia01 = []

     newlistEstrategia01.append("Null")
     newlistEstrategia01.append("Null")
     newlistEstrategia01.append("Null")
     newlistEstrategia01.append("Null")
     newlistEstrategia01.append("Chrome 1")
     newlistEstrategia01.append("10")
     newlistEstrategia01.append("Prime Video")
     newlistEstrategia01.append("Null")
    
     # Insert the data in Treeview widget
    
     tree.insert('', 'end', tag=['t3'], text="1", values=(newlistEstrategia01))
    
     tree.tag_configure('t1', background='#cccccc')
     tree.tag_configure('t2', background='white')
     tree.tag_configure('t3', foreground='white',background='red')

     tree.pack(side=BOTTOM, expand=False, fill=BOTH)
    
def selectItem(a):

    global nomeestra
    global greenc
    global gat

    tree.update()

    curItem = tree.focus()

    curRow = tree.set(curItem)

    nomeestra = curRow["c2"]
    gat = curRow["c3"]
    greenc = curRow["c4"]

    gatilho = gat.replace(",","")
 
def list_contains(A, B): 
    n = len(A) 
    return all(A == B[i:i + n] for i in range(len(B)-n + 1))

def contains(small, big):

    tam = 0

    for i in range(len(big)-len(small)+1):
        for j in range(len(small)):
            if big[i+j] != small[j]:
                break
        else:
            tam = tam +1          
    
    return tam

def impedir_minimizacao(nome_janela):
    """ Thread infinita para impedir que o Chrome seja minimizado """
    while True:
        try:
            janela = [j for j in gw.getWindowsWithTitle(nome_janela) if j.title][0]  # Obtém a janela
            if janela.isMinimized:
                janela.restore()  # Restaura se for minimizada
            time.sleep(1)  # Pausa breve para não sobrecarregar CPU
        except IndexError as e:
           logging.error(f"Janela do Chrome não encontrada. Tentando novamente...{e}")
           time.sleep(5)  # Aguarda antes de tentar novamente


# Variável global para controlar se já existe uma atualização em andamento
atualizacao_em_andamento = False

def checar_update():
    """Verifica atualização sem travar UI, scheduler ou agendamentos"""
    global atualizacao_em_andamento

    if atualizacao_em_andamento:
        return

    atualizacao_em_andamento = True
    label_toolbar.config(text="🔍 Verificando atualizações...")

    def worker():
        nonlocal updater, nova_versao
        try:
            updater = Update(
                label=None,  # ❌ nunca UI em thread
                sftp_host="sftp.kantaribopemedia.com",
                sftp_user="suportemdna",
                sftp_pass="Kafjtwev2018MO@",
                remote_path="suportemdna/Streaming_Scheduller",
                version_file="version.txt",
                update_file="update.zip",
                local_version_file="ver.txt",
                app_exe="Streaming_Scheduler.exe",
            )

            tem_update = updater.verificar_atualizacao()

            if not tem_update:
                root.after(0, lambda: finalizar("✅ Sistema atualizado"))
                return

            with open("version.txt", "r") as f:
                nova_versao = f.read().strip()

            root.after(0, mostrar_dialogo)

        except Exception as e:
            logging.error(f"❌ Erro no update: {e}", exc_info=True)
            root.after(0, lambda: finalizar("❌ Falha ao verificar atualização"))

    def mostrar_dialogo():
        dialog = Toplevel(root)
        dialog.title("Atualização Disponível")
        dialog.resizable(False, False)
        dialog.grab_set()

        dialog_width = 300
        dialog_height = 150
        pos_x = root.winfo_x() + (root.winfo_width() // 2) - (dialog_width // 2)
        pos_y = root.winfo_y() + (root.winfo_height() // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")

        Label(
            dialog,
            text=f"Versão {nova_versao} disponível!",
            font=("Arial", 10, "bold"),
            pady=10
        ).pack()

        Label(dialog, text="Deseja instalar agora?").pack(pady=5)

        def confirmar():
            dialog.destroy()
            iniciar_instalacao()

        def cancelar():
            dialog.destroy()
            finalizar("Atualização cancelada")

        Button(dialog, text="Sim", width=8, command=confirmar).pack(side=LEFT, padx=20, pady=10)
        Button(dialog, text="Não", width=8, command=cancelar).pack(side=RIGHT, padx=20, pady=10)

    def iniciar_instalacao():
        try:
            label_toolbar.config(text="🛠 Preparando atualização...")

            if not updater.preparar_atualizacao():
                raise Exception("Falha ao preparar atualização")

            label_toolbar.config(text="💾 Salvando configurações...")
            salvar()

            def countdown(i=3):
                if i == 0:
                    executar_update()
                    return
                label_toolbar.config(text=f"🔄 Reiniciando em {i}s...")
                root.after(1000, lambda: countdown(i - 1))

            countdown()

        except Exception as e:
            logging.error(f"❌ Erro ao instalar update: {e}", exc_info=True)
            finalizar("❌ Falha ao instalar atualização")

    def executar_update():
        try:
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                subprocess.Popen(
                    "update.bat",
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                root.destroy()
                sys.exit(0)
        except Exception as e:
            logging.error(f"❌ Falha ao executar update.bat: {e}", exc_info=True)
            finalizar("❌ Erro ao reiniciar")

    def finalizar(msg):
        global atualizacao_em_andamento
        label_toolbar.config(text=msg)
        atualizacao_em_andamento = False

        # limpeza segura
        for temp_file in ("version.txt", "update.zip", "update.bat"):
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    updater = None
    nova_versao = ""

    threading.Thread(target=worker, daemon=True).start()
    

def obter_versao():
    try:
        result = ""

        with open("ver.txt", "r") as f:
            result =  f.read().strip()  # Lê e remove espaços extras
     

        return result


    except FileNotFoundError:
        return "Arquivo não encontrado"
    
def checa_botao_start(get_botao_func):
    thread = threading.Thread(target=verificar_e_clicar, args=(get_botao_func,))
    thread.daemon = True
    thread.start()
      
def loadversion():
    label_version.config(text=obter_versao())

def criptograrunicavez():
    tree = ET.parse("config.xml")
    root = tree.getroot()

    # Substitui os campos sensíveis por versões criptografadas
    root.find("usuario_max").text = criptografar("luiz.lemos@kantaribopemedia.com")
    root.find("senha_max").text = criptografar("Kantar1234")

    # Salva de volta
    tree.write("config.xml", encoding="utf-8", xml_declaration=True)
    logging.info("Config.xml criptografado com sucesso.")

    # tree = ET.parse("auth.xml")
    # root = tree.getroot()

    # # Substitui os campos sensíveis por versões criptografadas
    # root.find("email").text = criptografar("kimsuportecaptacao@gmail.com")
    # root.find("senha").text = criptografar("iiaq bzwn ussg qmwg")
    # tree.write("auth.xml", encoding="utf-8", xml_declaration=True)


    # from crypto_utils import gerar_chave
    # gerar_chave()
    # valor = "AIzaSyB9ac-XdyMI13A_LBe1-CXkj9AcYF3VX9o"
    # cripto = criptografar(valor)

    # with open(".env.enc", "w") as f:
    #     f.write(f"YOUTUBE_API_KEY={cripto}\n")

if __name__ == "__main__":
    try:
        root = Tk()
        app = App(root)
        add()
        carrega_config_xml()
        load_csv_inicio()
        ajustartodootree()
        
        time.sleep(3)
        time.sleep(5)
        limpar_arquivo_periodicamente("log.txt")
        loadversion()
        root.after(2000, update_command)

        checa_botao_start(button_update)
        root.focus_force()
        root.mainloop()
    except Exception as e:
        logging.error(f"Erro fatal na inicialização: {e}")
        habilita_botoes()
        if 'root' in locals():
            root.mainloop()



      


