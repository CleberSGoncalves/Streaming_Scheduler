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
from crypto_utils import criptografar,carregar_env_criptografado,descriptografar,get_config_value
import hashlib

thread_em_execucao = False
_lock_envio_email = threading.Lock()
_ultimo_hash_enviado = None
_ultima_janela_envio = datetime.min
_COOLDOWN_MIN = 5  # minutos

class App:

    logging.basicConfig(
    filename="log.txt",
    level=logging.ERROR,
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
        criar_aba_acessos(nb)
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

        
        
        def toggle_checkbox_plat(option, var):
            checkbox_states_plat[option] = var.get()
            update_combobox_text_plat()

        def update_combobox_text_plat():
    # Atualiza o texto do Combobox com as opções selecionadas
            selected_options = [opt for opt in options_plat if checkbox_states_plat[opt]]
            combo_plat.set(", ".join(selected_options) if selected_options else "Selecione...")

        def show_checkbox_menu_plat():
    # Mostra o menu de checkboxes abaixo do Combobox
            menu_plat.tk_popup(combo_plat.winfo_rootx(), combo_plat.winfo_rooty() + combo_plat.winfo_height())
        # Opções do Combobox
        options_plat = ["Amazon Prime", "Disney", "Caze", "Dazn"]
        checkbox_states_plat = {opt: True for opt in options_plat}  # Rastreia o estado dos checkboxes

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

        botao_salvar = Button(tb1, text="Salvar", comman= salvar)
        botao_salvar["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=5)
        botao_salvar["font"] = 'Helvetica 8 bold'
        botao_salvar["fg"] = "black"
        botao_salvar["justify"] = "center"
        botao_salvar.place(x=187,y=80,width=50,height=30)


        def toggle_checkbox_camp(option, var):
            checkbox_states_camp[option] = var.get()
            update_combobox_text_camp()

        def update_combobox_text_camp():
    # Atualiza o texto do Combobox com as opções selecionadas
            selected_options = [opt for opt in options_camp if checkbox_states_camp[opt]]
            combo_camp.set(", ".join(selected_options) if selected_options else "Selecione...")

        def show_checkbox_menu_camp():
    # Mostra o menu de checkboxes abaixo do Combobox
            menu_camp.tk_popup(combo_camp.winfo_rootx(), combo_camp.winfo_rooty() + combo_camp.winfo_height())

        # Opções do Combobox
        options_camp = ["Brasileirão serie A", "Brasileirão serie B", "Copa do Brasil","Mundial de Clubes FIFA"]
        checkbox_states_camp = {opt: True for opt in options_camp}  # Rastreia o estado dos checkboxes

        # Cria o Combobox (apenas como gatilho para o menu)
        combo_camp = ttk.Combobox(tb1, state="readonly")
        combo_camp.place(x=290, y=80, width=150, height=30)
        combo_camp.set("Selecione Campeonatos")  # Texto inicial

# Cria um Menu suspenso com Checkboxes
        menu_camp = Menu(tb1, tearoff=0)
        checkbox_vars_camp = {}

        def toggle_checkbox_camp():
            for opt, var in checkbox_vars_camp.items():
               logging.info(f"{opt} => {var.get()}")

        for option in options_camp:
            var = BooleanVar(value=False)  # ou True se quiser iniciar marcado
            checkbox_vars_camp[option] = var
            menu_camp.add_checkbutton(
                label=option,
                variable=var,
                onvalue=True,
                offvalue=False,
                command=toggle_checkbox_camp,
                indicatoron=True,
                selectcolor='green'
            )
# Associa o clique do Combobox ao menu
        combo_camp.bind("<Button-1>", lambda e: show_checkbox_menu_camp())
# Cria o combobox na posição desejada (x=270, y=80)
      
        

         # Add a Treeview widget
        tree = ttk.Treeview(tb1, column=("Campeonato", "Partida", "Data", "Horário","Navegador","Min antes para ação","Canal de Transmissão","Url"), show='headings', height=13)
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

        
    
        tree.column("# 1", anchor=CENTER,width=minwidth)
        tree.heading("# 1", text="Campeonato")       
        tree.column("# 2", anchor=CENTER,width=minwidth)
        tree.heading("# 2", text="Evento")
        tree.column("# 3", anchor=CENTER,width=minwidth)
        tree.heading("#3", text="Data", command=lambda: sort_by_date(tree, "#3"))
        tree.column("# 4", anchor=CENTER,width=minwidth)
        tree.heading("# 4", text="Horario")
        tree.column("# 5", anchor=CENTER,width=minwidth)
        tree.heading("# 5", text="Navegador")
        tree.column("# 6", anchor=CENTER,width=minwidth)
        tree.heading("# 6", text="Min antes para ação")
        tree.column("# 7", anchor=CENTER,width=minwidth)
        tree.heading("# 7", text="Plataforma")
        tree.column("# 8", anchor=CENTER,width=minwidth)
        tree.heading("# 8", text="Url")      
        tree.place(x=960,y=90,width=250,height=20)
        # tree.bind('<ButtonRelease-1>', selectItem)
        
        button_delete=Button(tb1)
        button_delete["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=25)
        button_delete["font"] = 'Helvetica 18 bold'
        button_delete["fg"] = "blue"
        button_delete["justify"] = "center"
        button_delete["text"] = "+"
        button_delete.place(x=5,y=120,width=30,height=20)
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
                            options=("Amazon Prime", "Disney", "Caze", "Dazn", "Paramount"))
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

        # Import local para não impactar outros pontos que já usam DateEntry
        from tkcalendar import DateEntry
        from datetime import datetime

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
    from tkcalendar import DateEntry

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

    # Campos em pares: (usuário, senha)
    pares = [
        (("Usuário Prime", "usuario_prime"), ("Senha Prime", "senha_prime")),
        (("Usuário Disney", "usuario_disney"), ("Senha Disney", "senha_disney")),
        (("Usuário DAZN", "usuario_dazn"), ("Senha DAZN", "senha_dazn")),
        (("Usuário Paramount", "usuario_paramount"), ("Senha Paramount", "senha_paramount")),
        (("Usuário Max", "usuario_max"), ("Senha Max", "senha_max")),
    ]

    entrys = []
    campos_xml = []

    for i, ((label_user, campo_user), (label_senha, campo_senha)) in enumerate(pares):
        # Coluna 0: Usuário
        ttk.Label(lf, text=label_user + ":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
        e_user = ttk.Entry(lf, width=25)
        e_user.grid(row=i, column=1, sticky="w", padx=8, pady=6)
        entrys.append(e_user)
        campos_xml.append(campo_user)

        # Coluna 2: Senha
        ttk.Label(lf, text=label_senha + ":").grid(row=i, column=2, sticky="e", padx=8, pady=6)
        e_senha = ttk.Entry(lf, width=25, show="*")
        e_senha.grid(row=i, column=3, sticky="w", padx=8, pady=6)
        entrys.append(e_senha)
        campos_xml.append(campo_senha)

    # Botão de salvar centralizado
    btn_salvar = ttk.Button(lf, text="💾 Salvar Dados", command=lambda: salvar_novos_acessos(entrys, campos_xml))
    btn_salvar.grid(row=len(pares), column=0, columnspan=4, pady=25)

    # Ativar tema moderno
    style = ttk.Style()
    style.theme_use("clam")
    
        
def salvar_novos_acessos(entrys, campos):
            try:
                tree = ET.parse("config.xml")
                root = tree.getroot()

                for i, campo in enumerate(campos):
                    novo_valor = entrys[i].get().strip()
                    if novo_valor:
                        # Cria a tag se não existir ainda
                        if root.find(campo) is None:
                            ET.SubElement(root, campo)
                        root.find(campo).text = criptografar(novo_valor)

                tree.write("config.xml", encoding="utf-8", xml_declaration=True)
                messagebox.showinfo("Sucesso", "Dados atualizados com sucesso.")

                for e in entrys:
                    e.delete(0, tkinter.END)

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao atualizar os dados: {e}")

class _QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def obter_eventos_futuros(canal_url):
    """
    Retorna [(champ, titulo, url, dd/mm/YYYY, HH:MM)] para eventos futuros do canal.
    Não baixa vídeo. Silencia warnings/erros de formatos/lives futuras.
    """
    from datetime import datetime
    import yt_dlp
    import logging

    eventos_futuros = []

    try:
        # 1) Lista rápida do canal (flat) – só IDs e títulos
        ydl_opts_list = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
            'playlistend': 40,
            'ignoreerrors': True,
            'logger': _QuietLogger(),
        }
        with yt_dlp.YoutubeDL(ydl_opts_list) as ydll:
            info = ydll.extract_info(canal_url, download=False)

        for entry in (info.get('entries') or []):
            titulo_raw = (entry.get('title') or '').strip()
            titulo = titulo_raw.replace("AO VIVO: ", "").split("|")[0].strip()

            # Sua lógica de campeonato
            if "BRASILEIRÃO 2025" in titulo_raw.upper():
                champ = titulo_raw.split("|")[2].strip() if "|" in titulo_raw else ""
            else:
                champ = ""

            # Monta URL do vídeo
            vid_url = (
                entry.get('url')
                or entry.get('webpage_url')
                or (f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') else None)
            )
            if not vid_url:
                continue

            # 2) Re-extrai metadados do VÍDEO (sem download)
            ydl_opts_video = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'ignore_no_formats_error': True,   # não reclamar de lives futuras/sem formatos
                'extractor_retries': 2,
                'logger': _QuietLogger(),
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts_video) as ydv:
                    vinfo = ydv.extract_info(vid_url, download=False)
            except Exception:
                continue

            # Pega o melhor timestamp disponível
            ts = (
                vinfo.get('scheduled_start_time') or
                vinfo.get('release_timestamp') or
                vinfo.get('timestamp')
            )
            if not ts:
                ds = vinfo.get('release_date') or vinfo.get('upload_date')
                if ds and len(ds) == 8:
                    try:
                        ts = int(datetime.strptime(ds, '%Y%m%d').timestamp())
                    except Exception:
                        ts = None
            if not ts:
                continue

            try:
                dt = datetime.fromtimestamp(int(ts))
            except Exception:
                continue

            # Só futuros (ou explicitamente incoming)
            if vinfo.get('live_status') != 'is_upcoming' and dt <= datetime.now():
                continue

            if "BRASILEIRÃO 2025" in champ.upper() or "CLUBES DA FIFA" in champ.upper():
                eventos_futuros.append((
                    champ, titulo, vid_url, dt.strftime('%d/%m/%Y'), dt.strftime('%H:%M')
                ))

        return eventos_futuros

    except Exception as e:
        logging.error(f"Erro ocorrido na coleta do YouTube: {e}")
        try: habilita_botoes()
        except Exception: pass
        return None

def carrega_config_xml():
    dados = ler_arquivo_xml("config.xml")

    if dados:
     
  
     email_entry.delete(0, END)
     refresh_entry.delete(0,END)
     entry_email2.delete(0,END)
          
   
     email_entry.insert(END,dados["emails"])
     refresh_entry.insert(END,dados["refresh"])
     entry_email2.insert(END,dados["hora_automatico"])
     

     if dados["check_automatico_Email"] == "true":
         checkbox_ema.set(1)
     elif dados["check_automatico_Email"] == "false":
         checkbox_ema.set(0)

     if dados["check_automatico_Evento"] == "true":
         checkbox_grid.set(1)
     elif dados["check_automatico_Evento"] == "false":
         checkbox_grid.set(0)
     
     if dados.get("somente_relatorio") == "true":
         checkbox_busca.set(1)
     else:
        checkbox_busca.set(0)

    if dados["plataforma_dazn"] == "true":
         checkbox_vars_plat["Dazn"].set(1)
    elif dados["plataforma_dazn"] == "false":
         checkbox_vars_plat["Dazn"].set(0)

    if dados["plataforma_prime"] == "true":
         checkbox_vars_plat["Amazon Prime"].set(1)
    elif dados["plataforma_prime"] == "false":
         checkbox_vars_plat["Amazon Prime"].set(0)
    
    if dados["plataforma_caze"] == "true":
         checkbox_vars_plat["Caze"].set(1)
    elif dados["plataforma_caze"] == "false":
         checkbox_vars_plat["Caze"].set(0)

    if dados["plataforma_disney"] == "true":
         checkbox_vars_plat["Disney"].set(1)
    elif dados["plataforma_disney"] == "false":
         checkbox_vars_plat["Disney"].set(0)
    

def is_selected_camp(option):
            return checkbox_states_camp.get(option)

def is_selected_plat(option):
            var = checkbox_vars_plat.get(option, BooleanVar()).get()
            return var
    
def ler_arquivo_xml(nome_arquivo):
    try:
        # Carregar e analisar o arquivo XML
        tree = ET.parse(nome_arquivo)
        root = tree.getroot()

        # Extrair usuário e senha
        usuario_prime = descriptografar(root.find("usuario_prime").text)
        senha_prime = descriptografar(root.find("senha_prime").text)
        usuario_disney = descriptografar(root.find("usuario_disney").text)
        senha_disney = descriptografar(root.find("senha_disney").text)
        emails = root.find("emails").text
        refresh = root.find("refresh").text
        hora_automatico = root.find("hora_automatico").text
        check_automatico_Email = root.find("check_automatico_Email").text
        check_automatico_Evento = root.find("check_automatico_Evento").text
        sr_elem = root.find("somente_relatorio")
        somente_relatorio = sr_elem.text if sr_elem is not None else "false"
        plataforma_dazn = root.find("plataforma_dazn").text
        plataforma_prime = root.find("plataforma_prime").text
        plataforma_disney = root.find("plataforma_disney").text
        plataforma_caze = root.find("plataforma_caze").text
        
        # Retornar os dados como um dicionário
        return {
            "usuario_prime": usuario_prime,
            "senha_prime": senha_prime,
            "usuario_disney": usuario_disney,
            "senha_disney": senha_disney,
            "emails": emails,
            "refresh": refresh,
            "hora_automatico": hora_automatico,
            "check_automatico_Email": check_automatico_Email,
            "check_automatico_Evento": check_automatico_Evento,
            "somente_relatorio": somente_relatorio,
            "plataforma_dazn": plataforma_dazn,
            "plataforma_prime": plataforma_prime,
            "plataforma_disney": plataforma_disney,
            "plataforma_caze": plataforma_caze
        }
    except FileNotFoundError:

        label_toolbar.config(text=f"Arquivo '{nome_arquivo}' não encontrado.")
        pass
        return None
    except ET.ParseError:
        label_toolbar.config(text="Erro ao analisar o XML. Verifique o formato do arquivo.")
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

    set_tag("plataforma_dazn", "true" if is_selected_plat("Dazn") else "false")
    set_tag("plataforma_prime", "true" if is_selected_plat("Amazon Prime") else "false")
    set_tag("plataforma_caze", "true" if is_selected_plat("Caze") else "false")
    set_tag("plataforma_disney", "true" if is_selected_plat("Disney") else "false")

    # Salva no mesmo arquivo
    tree.write(nome_arquivo, encoding="utf-8", xml_declaration=True)
    label_toolbar.config(text=f"Arquivo XML '{nome_arquivo}' atualizado com sucesso!")

def validar_hora_minuto(texto):
    """ Verifica se o texto inserido está no formato HH:MM """
    padrao = r"^(?:[01]\d|2[0-3]):[0-5]\d$"  # Permite 00:00 a 23:59
    if re.match(padrao, texto):
        entry_email2.config(bg="lightgreen")  # Verde se for válido
    else:
        entry_email2.config(bg="lightcoral")  # Vermelho se for inválido




def tarefa_diaria():
    global thread_em_execucao
    if thread_em_execucao:
        label_toolbar.config(text="[INFO] Já está em execução. Ignorado.")
        return
    thread_em_execucao = True
    try:
        desabilita_botoes()
        label_toolbar.config(text=f"Executando atividades agendadas. {datetime.now()}")

        # Só limpa quando realmente for buscar de novo
        if checkbox_grid.get():
            limpar_treeview()
            run_busca_eventos()

        # Envia relatório com o que houver na grade
        if checkbox_ema.get():
            if tree.get_children():
                enviar_email()
            else:
                label_toolbar.config(text="Nenhum dado encontrado para enviar por e-mail")
                logging.warning("Tentativa de envio de e-mail sem dados no treeview")
    except Exception as e:
        logging.error(f"Erro em tarefa_diaria: {str(e)}", exc_info=True)
    finally:
        habilita_botoes()
        thread_em_execucao = False

colunas_excluidas = ["Navegador", "Usuario", "Senha"]
def extrair_dados_treeview(tree):
    """ Extrai os dados do Treeview e formata como uma tabela HTML, excluindo colunas específicas. """
    colunas = [col for col in tree["columns"] if col not in colunas_excluidas]  # Filtra colunas
    tabela_html = "<table border='1' style='border-collapse: collapse; text-align: left;'>"
    tabela_html += "<tr style='background-color: #4CAF50; color: white;'>"

    # Adicionando cabeçalhos
    for col in colunas:
        tabela_html += f"<th style='padding: 8px;'>{tree.heading(col)['text']}</th>"
    tabela_html += "</tr>"

    # Adicionando itens do Treeview
    for i, item in enumerate(tree.get_children()):
        cor_fundo = "#f2f2f2" if i % 2 == 0 else "#ffffff"
        tabela_html += f"<tr style='background-color: {cor_fundo};'>"
        for col in colunas:
            tabela_html += f"<td style='padding: 8px;'>{tree.set(item, col)}</td>"
        tabela_html += "</tr>"

    tabela_html += "</table>"
    return tabela_html

def validar_emails(email_text):
    """ Separa e valida os e-mails digitados no Entry. """
    emails = [email.strip() for email in email_text.split(";")]  # Separar por ";"
    padrao = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    emails_validos = [email for email in emails if re.match(padrao, email)]
    emails_invalidos = [email for email in emails if not re.match(padrao, email)]

    if emails_invalidos:
        email_entry.config(bg="lightcoral")  # Vermelho se houver e-mails inválidos
        label_toolbar.config(text=f"E-mails inválidos: {', '.join(emails_invalidos)}")
        return None
    else:
        email_entry.config(bg="lightgreen")  # Verde se todos forem válidos
        label_toolbar.config(text="Todos os e-mails são válidos!")
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
                try:
                    label_toolbar.config(text=f"Erro SMTP ao enviar e-mail: {e}")
                except Exception:
                    pass
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
            label_toolbar.config(text=f"Erro inesperado ao enviar e-mail: {e}")
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
                    label_toolbar.config(text=f"O arquivo '{arquivo}' foi limpo em: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} ")
             
            else:
                with open(arquivo, "w") as f:
                    f.write("")  # Cria o arquivo vazio
                label_toolbar.config(text=f"O arquivo '{arquivo}' não existia, então foi criado e limpo!")

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
            label_toolbar.config(text=f"Fechando instância existente de {nome_programa} (PID: {processo.info['pid']})...")
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
            "--no-first-run", "--no-default-browser-check"
        ])
    except Exception as e:
        logging.error(f"Falha ao abrir Chrome na porta {porta}: {e}")



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

    

def run_eventos_dazn(url_camp):

  try:   
        #  Usa o navegador da esquerda para buscar a lista
        label_toolbarprocess.config(text="Atualização de eventos do Dazn")
        label_toolbar.config(text="Realizando a atualização dos grids com os eventos do Dazn...")
        progresso["value"] = 0
        #    Exibe progressbar
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9222) indisponível.")
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
        label_toolbar.config(text="Abrindo pagina do campeonato...")
        progresso["value"] = progresso["value"] + 5
        logindazn(url_camp,us,pas,driverchrome1,10,"Novos")
        
        label_toolbar.config(text="Limpando o grid...")
        delete_null_items()
       
        label_toolbar.config(text="Atualizando lista do campeonato Dazn...")
        progresso["value"] = progresso["value"] + 5
         # Procura elmento principal dos proximos eventos
        
        
        eventos = obter_eventos_dazn_completo(driverchrome1)
    
        for evento in eventos:
            campeonato = "Mundial de Cluber FiFA"
            jogo = evento["Jogo"].upper()
            data_hora = evento["Data/hora"]
            url = evento["URL"]
            plataforma = "Dazn"
            minutos_antes = "15"
            data = data_hora.split(" ")[0]
            hora = data_hora.split(" ")[1]
                        
            csv_list = (campeonato,jogo,data,hora,var_navegador,minutos_antes,plataforma,url)
            tree.insert("", "end", values=csv_list)

            if var_navegador == "Esquerda":
             var_navegador = "Direita"
            elif var_navegador == "Direita":
                var_navegador = "Esquerda"
            list_b.append(csv_list)                  
        
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
  

def format_datetime(data_str):
    try:
        if not data_str:
            return {"data": "", "hora": ""}

        data_str = data_str.strip().title().replace("Pm", "PM").replace("Am", "AM")
        data_str = re.sub(r'\s+', ' ', data_str)
        data_str = re.sub(r'(\b[AP]M):00\b', r'\1', data_str)  # corrige "7 PM:00" -> "7 PM"

        now = datetime.now()

        # Live at → define data como hoje
        if data_str.startswith("Live At "):
            hora = data_str.replace("Live At ", "").strip()
            try:
                hora_obj = datetime.strptime(hora, "%I:%M %p")
            except ValueError:
                hora_obj = datetime.strptime(hora, "%I %p")  # Ex: "7 PM"

            dt = now.replace(hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0)
            return {
                "data": dt.strftime("%d/%m/%Y"),
                "hora": dt.strftime("%H:%M")
            }

        # Tomorrow
        elif data_str.startswith("Tomorrow"):
            hora = data_str.replace("Tomorrow", "").strip()
            try:
                hora_obj = datetime.strptime(hora, "%I:%M %p")
            except ValueError:
                hora_obj = datetime.strptime(hora, "%I %p")

            dt = now + timedelta(days=1)
            dt = dt.replace(hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0)
            return {
                "data": dt.strftime("%d/%m/%Y"),
                "hora": dt.strftime("%H:%M")
            }

        # Possíveis formatos
        possible_formats = [
            "%I:%M %p",
            "%I %p",
            "%b %d %I:%M %p",
            "%b %d %I %p",
            "%a, %b %d %I:%M %p",
            "%a, %b %d %I %p",
            "%a, %b %d %I:%M",
            "%a, %b %d %I",
            "%b %d %I:%M",
            "%b %d %I"
        ]

        for fmt in possible_formats:
            try:
                parsed = datetime.strptime(data_str, fmt)
                parsed = parsed.replace(year=now.year)

                # Corrige se for data passada (ex: Aug 6 sendo hoje Jul 30)
                if parsed < now - timedelta(days=1):
                    parsed = parsed.replace(year=now.year + 1)

                return {
                    "data": parsed.strftime("%d/%m/%Y"),
                    "hora": parsed.strftime("%H:%M")
                }
            except:
                continue

        logging.warning(f"[DESCARTADO] Data inválida: '{data_str}'")
        return {"data": "", "hora": ""}

    except Exception as e:
        logging.error(f"[ERRO FORMAT_DATETIME] {e}")
        return {"data": "", "hora": ""}
def run_eventos_prime(url_camp):
    try:
        label_toolbarprocess.config(text="Atualização de eventos do Amazon Prime")
        label_toolbar.config(text="Realizando a atualização dos grids com os eventos do Amazon Prime...")
        progresso["value"] = 0
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9222) indisponível.")
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

        label_toolbar.config(text="Abrindo pagina do campeonato...")
        progresso["value"] += 5
        driverchrome1.get(url_plataform)
        loginprime(url_camp, us, pas, driverchrome1, 10, "Novos")

        label_toolbar.config(text="Limpando o grid...")
        delete_null_items()

        label_toolbar.config(text="Atualizando lista do campeonato Amazon Prime...")
        progresso["value"] += 5

        wait = WebDriverWait(driverchrome1, 15)

        # ✅ Localize a UL pela âncora estável data-testid
        uls = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[data-testid='card-container-list']"))
        )
        if not uls:
            label_toolbar.config(text="Nenhuma lista de cards encontrada.")
            return

        ul = uls[0]

        # Pega os <li> (cada card fica dentro de um li)
        lis = ul.find_elements(By.CSS_SELECTOR, "li")

        # Se for um carrossel virtualizado, garanta rolagem para materializar elementos
        if not lis:
            driverchrome1.execute_script("arguments[0].scrollIntoView({block:'center'});", ul)
            time.sleep(1)
            lis = ul.find_elements(By.CSS_SELECTOR, "li")

        for idx, li in enumerate(lis):
            try:
                # ✅ Card estável por data-testid
                card = li.find_element(By.CSS_SELECTOR, "article[data-testid='card']")
            except Exception:
                # Pode haver placeholders; ignore
                continue

            # Título confiável via atributo
            nome_evento = card.get_attribute("data-card-title") or ""

            # Fallback: se não vier pelo atributo, tenta o <a> interno
            if not nome_evento.strip():
                try:
                    nome_evento = card.find_element(By.CSS_SELECTOR, "a._3HZFFn").text.strip()
                except Exception:
                    nome_evento = ""

            # Horário direto no card (p.GNymT4)
            data_hora = ""
            try:
                data_hora = card.find_element(By.CSS_SELECTOR, "p.GNymT4").text.strip()
            except Exception:
                pass

            # Link do detalhe
            url = ""
            try:
                a_tag = card.find_element(By.CSS_SELECTOR, "a._3HZFFn")
                url = a_tag.get_attribute("href") or ""
                # Se vier relativo, prefixa
                if url.startswith("/"):
                    url = "https://www.primevideo.com" + url
            except Exception:
                pass

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
            # Campeonato (direto no alt da imagem)
            try:
                campeonato = card.find_element(By.XPATH, '//*[@id="a-page"]/div[1]/div[5]/main/div/div/div[1]/div/div/ul/li/article/div[5]/h2/div/picture/img').get_attribute('alt').strip()
            except Exception:
                campeonato = ""

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
                    nome_evento,
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

def run_eventos_disney(url_camp):

  try:   
        
      
        #  Usa o navegador da esquerda para buscar a lista
        label_toolbarprocess.config(text="Atualização de eventos da Disney")
        label_toolbar.config(text="Realizando a atualização dos eventos da Disney no grids...")
        progresso["value"] = 0
        #    Exibe progressbar
        progresso.pack(side=RIGHT, padx=10, pady=5)

        if not verificar_chrome_debug("9222"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9222) indisponível.")
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

        # Abre na url do campeonato em questão selecionado
        label_toolbar.config(text="Abrindo pagina do campeonato da Disney...")
        progresso["value"] = progresso["value"] + 5
        driverchrome1.get(url_plataform)
        loginprime(url_camp,us,pas,driverchrome1,10,"Novos")

        label_toolbar.config(text="Limpando o grid...")
        delete_null_items()
       
        label_toolbar.config(text="Atualizando lista...")
        progresso["value"] = progresso["value"] + 5
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

                         if 'Brasileiro' in all_text[2] and 'Transmitido' not in dt_time[0] :
                           event = all_text[1]
                           champ =  all_text[2].replace("Campeonato", "").strip()                       
                           nor = h[n].find_elements(By.XPATH,'//*[@class="_2c2l371 _11x60sa1 xgfbc1ge xgfbc1l2 xgfbc1pq xgfbc1ue xgfbc11yw xgfbc17w xgfbc18q"]')
                           url = nor[n].get_attribute("href")
                           
                           plataforma = "Disney"

                           csv_list = (champ,event,data_str,hour,var_navegador,0,plataforma,url)
                           tree.insert("", "end", values=csv_list)
                         
                           if var_navegador == "Esquerda":
                            var_navegador = "Direita"
                           elif var_navegador == "Direita":
                            var_navegador = "Esquerda"
                           
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
  
def run_busca_eventos():

 try:
 
  if  button_update["text"] == "Running" or button_update["text"] == "Stoped":
    update_command()


  if is_selected_plat("Dazn"):

        if is_selected_camp("Mundial de Clubes FIFA"):
          url_camp = 'https://www.dazn.com/pt-BR/competition/Competition:dc4k1xh2984zbypbnunk7ncic'
          run_eventos_dazn(url_camp)
          remover_duplicatas(tree)
   
  if is_selected_plat("Amazon Prime"):

        if is_selected_camp("Brasileirão serie A"):
          url_camp = 'https://www.primevideo.com/tournament/amzn1.dv.icid.5a28c628-0310-42c0-8966-2f1f748488d3/ref=atv_hm_spo_c_NPzfck_2_1?jic=8%7CEgNhbGw%3D'
          run_eventos_prime(url_camp)
          remover_duplicatas(tree)
       
        if is_selected_camp("Copa do Brasil"):
          url_camp = 'https://www.primevideo.com/tournament/amzn1.dv.icid.6e097abf-f4c9-4638-ba1e-7ff95367e1c8/ref=atv_hm_spo_c_NPzfck_2_2?jic=8%7CEgNhbGw%3D'
          run_eventos_prime(url_camp) 
          remover_duplicatas(tree)

    
#   if is_selected_plat("Disney"):

#         if is_selected_camp("Brasileirão serie B"):
#           url_camp = 'https://www.disneyplus.com/pt-br/browse/entity-50b0affc-3aa0-4ac1-bda8-d37b1745ea95'
#           run_eventos_disney(url_camp) 
#           remover_duplicatas(tree)


  if is_selected_plat("Caze"):
   
   csv_list = ()
   list_b = list(csv_list)
   canal_url = 'https://www.youtube.com/@CazeTV/streams'  # Substitua com o URL do canal desejado
    #  Usa o navegador da esquerda para buscar a lista
   label_toolbarprocess.config(text="Atualização de eventos do Caze TV")
   label_toolbar.config(text="Realizando a atualização dos grids com os eventos do Caze TV...")
    #    Exibe progressbar
   desabilita_botoes()
   progresso.pack_forget()
   eventos = obter_eventos_futuros(canal_url) 
   progresso.pack(side=RIGHT, padx=10, pady=5)
   progresso["value"] = 0  
   var_navegador = "Esquerda"

   if eventos:
    for evento in eventos:
        champ,titulo, url, data, horario = evento
        event = titulo 
                                            
        plataforma = "Caze"
                            
               
        progresso["value"] = progresso["value"] + 5
        time.sleep(1)
        if is_selected_camp("Brasileirão serie A"):

            if "BRASILEIRÃO" in champ:
                champ =  "Brasileirão serie A" 
                csv_list = (champ,event,data,horario,var_navegador,0,plataforma,url)

        if is_selected_camp("Mundial de Clubes FIFA"): 

            if "BRASILEIRÃO" not in champ.upper():
                champ =  "Mundial de Clubes FiFA" 
                csv_list = (champ,event,data,horario,var_navegador,0,plataforma,url)        

        tree.insert("", "end", values=csv_list)

        if var_navegador == "Esquerda":
                var_navegador = "Direita"
        elif var_navegador == "Direita":
                var_navegador = "Esquerda"
        
        list_b.append(csv_list)     
                                 
    remover_duplicatas(tree)
   
  ajustartodootree()

        #  Volta a running a aplicação
  update_command()

  habilita_botoes()
  progresso["value"] = 100
  time.sleep(2)
  progresso.pack_forget()
 
 except UnboundLocalError as e:
       logging.error(f"Erro ocorrido: {e}")  # Registra o erro no log
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       habilita_botoes()
       update_command()  
       pass

 except Exception as e: 
  logging.error(f"Erro ocorrido: {e}") 
  exc_type, exc_obj, exc_tb = sys.exc_info()
  fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
  habilita_botoes()
  pass

def ajustartodootree():
            label_toolbar.config(text="Ajustando colunas do grid...")
            progresso["value"] = progresso["value"] + 10
            autoajustar_colunas(tree,ignorar=['Url'])          
            label_toolbar.config(text="Ordenando por horário em ordem crescente") 
            progresso["value"] = progresso["value"] + 10
            sort_by_time(tree, 2, 3)
            label_toolbar.config(text="filtrando por data em ordem crescente")
            progresso["value"] = progresso["value"] + 10
            sort_by_date(tree, "Data")
            label_toolbar.config(text="Removendo eventos duplicados")            
            label_toolbar.config(text="Finalizado processo de busca de todos os eventos!")
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
  label_toolbar.config(text =f"Streaming Scheduler error: {e}")
  pass

def limpar_treeview():
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
            valores = tree.item(item, 'values')
            
            try:
                # Cria chave única baseada nas colunas relevantes
                chave = tuple(str(valores[i]) for i in colunas_chave if i < len(valores))
            except (IndexError, TypeError, AttributeError) as e:
                logging.warning(f"Item {item} com valores inválidos: {valores} - {str(e)}")
                continue
            
            if chave in itens_unicos:
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
                label_toolbar.config(text=f"Streaming Scheduler error: {e}")
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
                label_toolbar.config(text =f"Streaming Scheduler error:{e}")
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
         label_toolbar.config(text ="Configurações salvas com sucesso")
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


def update_command():
 
 try:
   
   if  button_update["text"] == "Running":
               button_update["text"] = "Stoped"
               button_update["fg"] = "red"
            #    threadingTimer.cancel()    
               button_update["text"] = "Start"
               button_update["fg"] = "green"
   
   
   elif  button_update["text"] == "Start":
                button_update["text"] = "Running"
                button_update["fg"] = "red"
                iniciar_thread(run_app)

   elif  button_update["text"] == "Stoped":
                button_update["text"] = "Start"
                button_update["fg"] = "green"


 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes()
         pass
 
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
                    label_toolbar.config(text="[INFO] Botão 'Start' detectado. Iniciando contagem...")
                    habilita_botoes()
                elif time.time() - tempo_inicial >= 600:
                    logging.info("[INFO] Botão ficou 'Start' por mais de 10 minutos. Clicando...")
                    label_toolbar.config(text="[INFO] Botão ficou 'Start' por mais de 10 minutos. Clicando...")
                    update_command()
                    tempo_inicial = None
            else:
                if tempo_inicial is not None:
                    logging.info("[INFO] Texto mudou. Resetando contagem.")
                    label_toolbar.config(text="[INFO] Texto mudou. Resetando contagem.")
                tempo_inicial = None

        except Exception as e:
            logging.error(f"[WARNING] Erro ao acessar o botão: {e}")
            label_toolbar.config(text=f"[WARNING] Erro ao acessar o botão: {e}")
            habilita_botoes()
            tempo_inicial = None

        time.sleep(600)  # Verifica a cada 10 minutos


def iniciar_monitoramento(entry_horario, funcao):

 try:
    thread = threading.Thread(target=monitorar_horario, args=(entry_horario, funcao))
    thread.daemon = True
    thread.start()

    logging.info(f"Aguardando proximo update de eventos: {entry_horario.get()}")
    label_toolbar.config(text=f"Aguardando proximo update de eventos: {entry_horario.get()}")

 except Exception as e:
            logging.info(f"[ERRO] {e}")
            habilita_botoes()
            time.sleep(5)

def monitorar_horario(entry_horario, funcao):
    while True:
        try:
            horario_entrada = entry_horario.get().strip()

            if ":" not in horario_entrada:
                logging.info("[ERRO] Horário inválido. Use MM:SS")
                label_toolbar.config(text="[ERRO] Horário inválido. Use MM:SS")
                time.sleep(5)
                continue

            horas, minutos = map(int, horario_entrada.split(":"))

            agora = datetime.now()
            if agora.hour == horas and agora.minute == minutos:
                if not thread_em_execucao:
                    logging.info(f"[INFO] Executando no horário {horario_entrada}")
                    label_toolbar.config(text=f"[INFO] Executando no horário {horario_entrada}")
                    threading.Thread(target=funcao).start()
                else:
                    logging.info("[INFO] Já está executando, aguardando próxima janela.")
                    label_toolbar.config(text="[INFO] Já está executando, aguardando próxima janela.")
                time.sleep(60)  # Evita executar mais de uma vez no mesmo minuto
            else:
                time.sleep(1)
        except Exception as e:
            logging.info(f"[ERRO] {e}")
            habilita_botoes()
            time.sleep(5)
            
def executar_funcao():
    global thread_em_execucao
    if thread_em_execucao:
        logging.info("[INFO] Já está em execução. Ignorado.")
        label_toolbar.config(text="[INFO] Já está em execução. Ignorado.")
        return

    thread_em_execucao = True
    try:
        logging.info(f"[EXECUTANDO] Função executada em {datetime.now().strftime('%H:%M:%S')}")
        label_toolbar.config(text=f"[EXECUTANDO] Função executada em {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(10)  # Simula uma tarefa demorada
    finally:
        thread_em_execucao = False
        logging.info("[INFO] Função finalizada.")
        label_toolbar.config(text="[INFO] Função finalizada.")


def refresh_youtube(driver):

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        if not body.text.strip():
            logging.info("Corpo vazio ou erro de carregamento detectado")
            driver.refresh()
        
        if "Ah, bolas" in driver.title or "Aw, Snap" in driver.title:
          
            driver.refresh()  # ou driver.get(url) novamente
    except:
        logging.info("Elemento body não encontrado, possível erro de carregamento")
        driver.refresh()

    

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

 try:                           
  status = button_update["text"]
  
#    Checar versão nova
  checar_update()
  desabilita_botoes()
  iniciar_monitoramento(entry_email2, tarefa_diaria)
  
  if driverchrome1 is not None:
    refresh_youtube(driverchrome1)
  if driverchrome2 is not None:
    refresh_youtube(driverchrome2)


  if  status == "Running":

   cwd = os.path.realpath('.')
   file = "data.csv"
   dir_final = os.path.join(cwd,file)
    
   root.update()

   label_toolbarprocess.config(text=returndatetimeatual())
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
       horasubt2 = str(horasubt.hour)+":"+str(horasubt.minute)
       horatemp_time_format = datetime.strptime(horasubt2,'%H:%M').time()

       hora_minuto = str(datetime.now().hour)+":"+str(datetime.now().minute)
       horaatual_time_format = datetime.strptime(hora_minuto,'%H:%M').time()

       if horaatual_time_format == horatemp_time_format:
       
        if plataform == "Dazn":
         user =  get_config_value("usuario_dazn")
         pas = get_config_value("senha_dazn")  
        elif plataform == "Amazon Prime":
         user =  get_config_value("usuario_prime")
         pas = get_config_value("senha_prime") 
        elif plataform == "Disney":
         user =  get_config_value("usuario_disney")
         pas = get_config_value("senha_disney") 
       
        url = tree.item(parent)["values"][7]
        evento = tree.item(parent)["values"][1]

        navegador1 = str.upper(tree.item(parent)["values"][4])
        navegador2 = str.upper(tree.item(parent)["values"][4])

        chrome_1 = "ESQUERDA"
        chrome_2 = "DIREITA"
                     
    #    Checa se o checkChrome esta ativado:
        if navegador1 == chrome_1 :
        
         opt = Options()
         opt.add_argument("--js-flags=--max_old_space_size=4096")
         opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

         service = Service(ChromeDriverManager().install())
         driverchrome1 = webdriver.Chrome(service=service, options=opt)
         # Localizando Prime Video
         if re.search('\\bprime\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)
          driverchrome1.get("https://www.primevideo.com/offers/nonprimehomepage/ref=atv_auth_signout")
        
        #   time.sleep(4)
          loginprime(url,user,pas,driverchrome1,timeantes,evento)
          break;
         
          # Localizando Disney Plus
         elif re.search('\\bdazn\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)                
        #   time.sleep(4)
          logindazn(url,user,pas,driverchrome1,timeantes,evento)
          break;
                        
                  # Localizando Disney Plus
         elif re.search('\\bcaze\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)
          ret = tentar_reproduzir_evento(driverchrome1,url)
          if ret:
             label_toolbar.config(text="Em reprodução youtube "+evento)
                        
          break;
       
        elif re.search('\\bdisney\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)
          driverchrome1.get("https://www.disneyplus.com/identity/login/enter-email")
        #   time.sleep(4)
          logindisney(url,user,pas,driverchrome1,timeantes,evento)
          break;

        
        elif navegador2 == chrome_2 :
  
         if not verificar_chrome_debug("9224"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9224) indisponível.")
            return

         chrome_options = Options()
         chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
         chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9224")

         service = Service(ChromeDriverManager().install())
         driverchrome2 = webdriver.Chrome(service=service, options=chrome_options)
     
         # Localizando Prime Video
         if re.search('\\bprime\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da direita a pagina do : "+plataform)
          driverchrome2.get("https://www.primevideo.com/offers/nonprimehomepage/ref=atv_auth_signout")
        #   time.sleep(4)

          loginprime(url,user,pas,driverchrome2,timeantes,evento)
          break;
         
         elif re.search('\\bdazn\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)                
        #   time.sleep(4)
          logindazn(url,user,pas,driverchrome2,timeantes,evento)
          break;
                      
         
         elif re.search('\\bcaze\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da esquerda a pagina do : "+plataform)
          ret = tentar_reproduzir_evento(driverchrome2,url)
          if ret:
             label_toolbar.config(text="Em reprodução youtube "+evento)

          # Localizando Disney Plus
         elif re.search('\\bdisney\\b', plataform, re.IGNORECASE):
          label_toolbar.config(text="Abrindo no navegador da direita a pagina do : "+plataform)
          driverchrome2.get("https://www.disneyplus.com/identity/login/enter-email")
        #   time.sleep(4)
          logindisney(url,user,pas,driverchrome2,timeantes,evento)
          break;
         
   progresso.pack_forget()
   habilita_botoes()
   label_toolbarprocess.config(text="")
   num_refresh = int(refresh_entry.get())
   threadingTimer = Timer(num_refresh, run_app)
   threadingTimer.start()  

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
    hoje = datetime.now()
    try:
        if texto.startswith("HOJE"):
            hora = texto.replace("HOJE", "").strip()
            data = hoje.strftime("%d/%m/%Y")

        elif texto[:3] in ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]:
            dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
            hoje_idx = hoje.weekday()
            alvo_idx = dias_semana.index(texto[:3])
            dias_diff = (alvo_idx - hoje_idx + 7) % 7
            data = (hoje + timedelta(days=dias_diff)).strftime("%d/%m/%Y")
            hora = texto[3:].strip()

        elif len(texto.split()) == 3:  # Ex: "22 JUN 13:00"
            dia, mes_abrev, hora = texto.split()
            meses = {
                "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
                "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
                "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
            }
            mes_num = meses.get(mes_abrev.upper(), "??")
            ano = hoje.year
            data = f"{dia.zfill(2)}/{mes_num}/{ano}"

        else:
            return "Data inválida"

        return f"{data} {hora}"

    except Exception:
        return "Data inválida"

def logindazn(url,email,senha,driver,timeantes,evento):
    # Acessa diretamente a URL de login
    driver.get("https://www.dazn.com/pt-BR/account/content/dazn/signup?signin=true&page=emailDetails")
    time.sleep(5)
    




    button = driver.find_elements(By.XPATH,'//*[@id="onetrust-accept-btn-handler"]')
    
    if len(button) > 0:
    
        button[0].click()
        

        label_toolbar.config(text="Efetuando o login no site do DAZN...")

        # Aguarda o campo de e-mail estar disponível
        time.sleep(3)
        input_email = driver.find_element(By.XPATH, '//*[@id="email"]')
        input_email.send_keys(email)
        input_email.send_keys(Keys.ENTER)
        label_toolbar.config(text="Inserido usuario!")

        # Aguarda o campo de senha carregar
        time.sleep(2)
        input_senha = driver.find_element(By.XPATH, '//*[@id="password"]')
        input_senha.send_keys(senha)
        input_senha.send_keys(Keys.ENTER)
        label_toolbar.config(text="Inserido senha!")

        # Aguarda possível redirecionamento pós-login
        time.sleep(8)

        driver.get(url)
        time.sleep(4)
        for _ in range(5):
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            time.sleep(2)

        # Verifica se login teve sucesso com base na URL
        if "home" in driver.current_url or "account" in driver.current_url:
            label_toolbar.config(text="✅ Login realizado com sucesso!")
            return True
        else:
            label_toolbar.config(text="❌ Falha no login ou autenticação adicional necessária.")
            return False

    else:
        label_toolbar.config(text="✅ Login realizado com sucesso!")
        
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
       
       label_toolbar.config(text="Buscando elemento de pagina login...")
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
        label_toolbar.config(text="Buscando elemento de senha login...")
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
  label_toolbar.config(text="Abrindo a URL do evento: "+evento)
  
  driver.get(url)

#   Se após a autenticação mostrar o botão de login do prime maximizar clicar e voltar ao normal a janela
  label_toolbar.config(text="Checando necessidade de reautenticação...")
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
    label_toolbar.config(text="Aguardando presença do botão do player para o evento: "+evento)
    clicar_com_espera_segura(driver,'//*[@role="button"]')
    # WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'//*[@role="button"]'))).click()


#   Botão de watch live em janela pequena apos clicar em webwait caso apareça

    if len(driver.find_elements(By.XPATH, '/html/body/div[3]/div/div/div/div[2]/div/span[3]/div/div[1]/a')) > 0:  
      label_toolbar.config(text="Clicou no sub botão do player... ")
      driver.find_element(By.XPATH, '/html/body/div[3]/div/div/div/div[2]/div/span[3]/div/div[1]/a').click()
      time.sleep(2)
      
   

      # Clicar no checkbox de evento mature themes
    if len(driver.find_elements(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[1]/div/div/div')) > 0:
         driver.find_element(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[1]/div/div/div').click()
         progresso["value"] = progresso["value"] + 10
         label_toolbar.config(text="Clicou no check de  permissão para conteúdo sensivel...")
             
            #  Clicar no botão de evento mature themes
         time.sleep(2)
         driver.find_element(By.XPATH, '//*[@id="dv-web-player"]/div/div[2]/div/div/div/div/div[1]/div[8]/div/div/div[2]/button[2]').click()
         progresso["value"] = progresso["value"] + 10
         label_toolbar.config(text="Clicou no botão para permissão para conteúdo sensivel...")
  
  # Espera até o botão estar clicável e clica
  botao_close = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Continue']"))
  )
  botao_close.click()
  progresso["value"] = 100
  label_toolbar.config(text="Em reprodução do evento: "+evento)
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
  
def loginmax(url,us,passw,driver):

 global driverchrome
#   user max= luiz.lemos@kantaribopemedia.com9427 pass = Kantar1234
#

 try: 
  
  
   user = driver.find_elements(By.XPATH, '//*[@id="login-email-input"]')

   if len(user) > 0:      
       logging.info("Buscando elemento de pagina login!")
       user = driver.find_element(By.CSS_SELECTOR, '#login-email-input')
       user.clear()
       time.sleep(2)
       user.send_keys(us) 
       user.clear()
       user.send_keys(us) 
       time.sleep(2)
    #    user.send_keys(Keys.ENTER) 
       logging.info("Buscando elemento de senha login!")
       time.sleep(2)
       pas = driver.find_element(By.XPATH, '//*[@id="login-password-input"]')
       pas.clear()
       pas.send_keys(passw) 
       pas.send_keys(Keys.ENTER) 
       time.sleep(3)
       driverchrome.get(url)
       time.sleep(4)
           
   if len(driver.find_elements(By.XPATH, '//*[@id="layer-root-app-content"]/div/main/div/div[1]/div/div[3]/button')) > 0:

           driver.find_element(By.XPATH, '//*[@id="layer-root-app-content"]/div/main/div/div[1]/div/div[3]/button').click()
  
       
 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes()
         pass
     
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
    label_toolbar.config(text="Em reprodução do evento: "+evento)
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
    """Função para iniciar a verificação de atualização em thread separada"""
    def atualizacao_completa():
        global atualizacao_em_andamento
        
        if atualizacao_em_andamento:
            return
            
        atualizacao_em_andamento = True
        try:
            # Configuração do updater
            updater = Update(
                label=label_toolbar,
                sftp_host="mediaftp.kantaribopemedia.com",
                sftp_user="suportemdna",
                sftp_pass="Kafjtwev2018MO",
                remote_path="suportemdna/Streaming_Scheduller",
                version_file="version.txt",
                update_file="update.zip",
                local_version_file="ver.txt",
                app_exe="Streaming_Scheduler.exe",
            )

            # Verificar atualização
            label_toolbar.config(text="🔍 Verificando atualizações...")
            root.update()

            if not updater.verificar_atualizacao():
                label_toolbar.config(text="✅ Sistema atualizado")
                return

            # Mostrar versão disponível
            with open("version.txt", "r") as f:
                nova_versao = f.read().strip()

            # Cria um diálogo modal personalizado com tamanho reduzido
            dialog = Toplevel(root)
            dialog.title("Atualização Disponível")
            dialog.resizable(False, False)
            dialog.grab_set()  # Torna modal
            
            # Tamanho reduzido (300x150) e centralizado
            dialog_width = 300
            dialog_height = 150
            pos_x = root.winfo_x() + (root.winfo_width() // 2) - (dialog_width // 2)
            pos_y = root.winfo_y() + (root.winfo_height() // 2) - (dialog_height // 2)
            dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
            
            # Conteúdo do diálogo compacto
            Label(dialog, text=f"Versão {nova_versao} disponível!", 
                 pady=5, font=('Arial', 10, 'bold')).pack()
            Label(dialog, text="Deseja instalar agora?", pady=5).pack()
            
            resposta = BooleanVar()
            
            def sim():
                resposta.set(True)
                dialog.destroy()
                
            def nao():
                resposta.set(False)
                dialog.destroy()
                
            # Botões compactos e alinhados
            Button(dialog, text="Sim", command=sim, width=8).pack(side=LEFT, padx=10, pady=5, expand=True)
            Button(dialog, text="Não", command=nao, width=8).pack(side=RIGHT, padx=10, pady=5, expand=True)
            
            # Espera até que o diálogo seja fechado
            root.wait_window(dialog)
            
            if not resposta.get():
                label_toolbar.config(text="Atualização cancelada")
                return

            # Preparar atualização (cria o update.bat)
            label_toolbar.config(text="🛠 Preparando atualização...")
            root.update()

            if not updater.preparar_atualizacao():
                raise Exception("Falha ao preparar arquivos de atualização")

            # Salvar configurações antes de atualizar
            label_toolbar.config(text="💾 Salvando configurações...")
            salvar()

            # Contagem regressiva
            for i in range(3, 0, -1):
                label_toolbar.config(text=f"🔄 Reiniciando em {i}s...")
                root.update()
                time.sleep(1)

            # Executar a atualização
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

            atualizacao_em_andamento = False

        except Exception as e:   
            logging.error(f"❌ Erro na atualização: {str(e)}")

            # Limpeza de arquivos temporários
            for temp_file in ["version.txt", "update.zip", "update.bat"]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        finally:
            atualizacao_em_andamento = False

    # Inicia a thread de atualização
    thread = threading.Thread(target=atualizacao_completa, daemon=True)
    thread.start()
    

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

# def criptograrunicavez():
    # tree = ET.parse("config.xml")
    # root = tree.getroot()

    # # Substitui os campos sensíveis por versões criptografadas
    # root.find("usuario_prime").text = criptografar("11982749388")
    # root.find("senha_prime").text = criptografar("Kantar123")
    # root.find("usuario_disney").text = criptografar("luiz.lemos@kantaribopemedia.com")
    # root.find("senha_disney").text = criptografar("Kantar123")

    # # Salva de volta
    # tree.write("config.xml", encoding="utf-8", xml_declaration=True)
    #logging.info("Config.xml criptografado com sucesso.")

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
    # load_csv()
    # fechar_instancia("Streaming_Scheduler.exe")
    root = Tk()
    app = App(root)    
    # criptograrunicavez()
    add()
    carrega_config_xml()
    load_csv_inicio()
    ajustartodootree()
   
    # update_chrome1()
    # update_chrome2()
    time.sleep(3)
   
    time.sleep(5)
    limpar_arquivo_periodicamente("log.txt")
    # Checar versão atual
    loadversion()
    # ao abrir já abre em running
    update_command()
    # Checa se os navegadores estão abertos senao abre
    if not verificar_chrome_debug("9222"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9222) indisponível.")            
    if not verificar_chrome_debug("9224"):
            habilita_botoes()
            label_toolbar.config(text="Chrome (9224) indisponível.")
    # checa se o botão está em start
    checa_botao_start(button_update)
   
    root.focus_force()
 except Exception as e: 
         logging.error(f"Erro ocorrido: {e}") 
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         habilita_botoes()  
         update_command()
         pass
 
     # Mantém o script principal rodando
          
 root.mainloop()    



      


