"""
Modulo de Atualização Automática (Auto-Updater) para o Streaming Scheduler via GitHub Releases.
Verifica novas versões disponibilizadas no repositório GitHub e realiza o auto-deploy
preservando integralmente os arquivos de configuração locais (config.xml, auth.xml, etc.).
"""

import os
import sys
import json
import time
import urllib.request
import subprocess
import logging

CURRENT_VERSION = "17.5"

class AutoUpdater:
    def __init__(self, version_url: str = "https://raw.githubusercontent.com/CleberSGoncalves/Streaming_Scheduler/main/version.json"):
        self.version_url = version_url
        self.current_version = self._get_local_version()

    def _get_local_version(self) -> str:
        """Obtém versão local de ver.txt se existir, ou o fallback CURRENT_VERSION."""
        try:
            exe_path = sys.executable
            if not exe_path.lower().endswith(".exe") or "python" in os.path.basename(exe_path).lower():
                exe_dir = os.path.dirname(os.path.abspath(__file__))
            else:
                exe_dir = os.path.dirname(exe_path)
            ver_file = os.path.join(exe_dir, "ver.txt")
            if os.path.exists(ver_file):
                with open(ver_file, "r", encoding="utf-8") as f:
                    v = f.read().strip()
                    if v:
                        return v
        except Exception:
            pass
        return CURRENT_VERSION

    def check_for_update(self):
        """
        Verifica se há uma versão mais recente disponível no GitHub.
        Retorna (has_update, remote_version, download_url, changelog)
        """
        try:
            url = f"{self.version_url}?_t={int(time.time())}"
            req = urllib.request.Request(
                url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache'
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    remote_ver = str(data.get("version", "0.0")).strip()
                    download_url = data.get("download_url", "")
                    changelog = data.get("changelog", "Melhorias gerais e correções de estabilidade.")
                    
                    if self._is_newer(remote_ver, self.current_version):
                        return True, remote_ver, download_url, changelog
                    return False, remote_ver, download_url, changelog
        except Exception as e:
            logging.error(f"[AUTO-UPDATER] Erro ao verificar atualizações no GitHub: {e}")
        return False, self.current_version, "", ""

    def _is_newer(self, remote_ver: str, local_ver: str) -> bool:
        try:
            # Aceita formatos tipo "17.3", "v17.3", "2.4.1"
            def parse_v(v_str):
                cleaned = v_str.lower().replace("v", "").strip()
                return [int(x) for x in cleaned.split(".") if x.isdigit()]

            r_parts = parse_v(remote_ver)
            l_parts = parse_v(local_ver)
            return r_parts > l_parts
        except Exception:
            return False

    def perform_update_and_restart(self, download_url: str, remote_version: str = "", progress_callback=None):
        """
        Baixa o novo executável diretamente do GitHub Releases, cria o script de substituição atômico
        e reinicia a aplicação. Os arquivos locais (config.xml, auth.xml) JAMAIS são tocados.
        """
        try:
            exe_path = sys.executable
            # Se executando em modo script (.py), usa o caminho de Streaming_Scheduler.exe no cwd
            if not exe_path.lower().endswith(".exe") or "python" in os.path.basename(exe_path).lower():
                exe_path = os.path.abspath("Streaming_Scheduler.exe")

            exe_dir = os.path.dirname(exe_path)
            new_exe_path = os.path.join(exe_dir, "Streaming_Scheduler_new.exe")
            old_exe_path = os.path.join(exe_dir, "Streaming_Scheduler_old.exe")
            bat_path = os.path.join(exe_dir, "update_launcher.bat")

            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/octet-stream,application/vnd.github.v3+json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            
            logging.info(f"[AUTO-UPDATER] Baixando atualização de {download_url}...")
            response = requests.get(download_url, headers=headers, stream=True, verify=False, timeout=120, allow_redirects=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB por bloco
            
            with open(new_exe_path, "wb") as f_out:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f_out.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            if total_size > 0:
                                percent = min(100, int(downloaded * 100 / total_size))
                                progress_callback(percent)
                            else:
                                mb = downloaded / (1024 * 1024)
                                progress_callback(f"{mb:.1f} MB")

            # Validação do arquivo baixado (mínimo 10 MB para um binário PyInstaller completo)
            if not os.path.exists(new_exe_path) or os.path.getsize(new_exe_path) < 5 * 1024 * 1024:
                raise RuntimeError("Arquivo baixado corrompido ou incompleto.")

            # Atualiza o arquivo local ver.txt para refletir a nova versão
            if remote_version:
                try:
                    with open(os.path.join(exe_dir, "ver.txt"), "w", encoding="utf-8") as vf:
                        vf.write(remote_version)
                except Exception as ex_v:
                    logging.warning(f"[AUTO-UPDATER] Não foi possível atualizar ver.txt: {ex_v}")

            pid = os.getpid()
            old_exe_name = os.path.basename(old_exe_path)
            exe_name = os.path.basename(exe_path)
            
            # Script Batch resiliente (idêntico ao do Monitor_Esportes)
            bat_content = f"""@echo off
setlocal enabledelayedexpansion
chcp 65001 > NUL

:: 1. Limpar variáveis de ambiente herdadas do PyInstaller
set "_MEIPASS="
set "_MEIPASS2="
set "PYTHONHOME="
set "PYTHONPATH="

echo [AUTO-UPDATE] Encerrando processos e aguardando liberação do sistema...
timeout /t 3 /nobreak > NUL

:: 2. Encerrar processo principal pelo PID e por nome
if not "{pid}"=="" taskkill /F /PID {pid} > NUL 2>&1
taskkill /F /T /IM "{exe_name}" > NUL 2>&1
timeout /t 2 /nobreak > NUL

:: 3. Loop de verificação se o processo encerrou no Gerenciador de Tarefas
set /a pcount=0
:CHECK_PROCESS
tasklist /FI "IMAGENAME eq {exe_name}" 2>NUL | find /I "{exe_name}" > NUL
if "%ERRORLEVEL%"=="0" (
    set /a pcount+=1
    if !pcount! LSS 10 (
        taskkill /F /T /IM "{exe_name}" > NUL 2>&1
        timeout /t 1 /nobreak > NUL
        goto CHECK_PROCESS
    )
)

:: 4. Limpar backup antigo se existir
if exist "{old_exe_path}" del /f /q /a "{old_exe_path}" > NUL 2>&1

:: 5. Loop de insistência para mover o executável em produção
set /a count=0
:RETRY_SWAP
set /a count+=1

move /y "{exe_path}" "{old_exe_path}" > NUL 2>&1
if not exist "{exe_path}" goto DO_REPLACE

ren "{exe_path}" "{old_exe_name}" > NUL 2>&1
if not exist "{exe_path}" goto DO_REPLACE

del /f /q /a "{exe_path}" > NUL 2>&1
if not exist "{exe_path}" goto DO_REPLACE

if !count! LSS 30 (
    timeout /t 1 /nobreak > NUL
    goto RETRY_SWAP
)

:DO_REPLACE
:: 6. Mover o novo executável baixado para o lugar do executável de produção
if exist "{new_exe_path}" (
    move /y "{new_exe_path}" "{exe_path}" > NUL 2>&1
    if not exist "{exe_path}" (
        copy /y "{new_exe_path}" "{exe_path}" > NUL 2>&1
        del /f /q /a "{new_exe_path}" > NUL 2>&1
    )
)

:: 7. Confirmar substituição e reiniciar com ambiente limpo
if exist "{exe_path}" (
    echo [AUTO-UPDATE] Atualização concluída com sucesso! Iniciando Streaming Scheduler...
    if exist "{new_exe_path}" del /f /q /a "{new_exe_path}" > NUL 2>&1
    if exist "{old_exe_path}" del /f /q /a "{old_exe_path}" > NUL 2>&1
    timeout /t 2 /nobreak > NUL
    set "_MEIPASS="
    set "_MEIPASS2="
    set "PYTHONHOME="
    set "PYTHONPATH="
    cd /d "{exe_dir}"
    start "" "{exe_path}"
) else (
    echo [AUTO-UPDATE] ERRO: Falha ao substituir executável. Restaurando backup anterior...
    timeout /t 2 /nobreak > NUL
    set "_MEIPASS="
    set "_MEIPASS2="
    set "PYTHONHOME="
    set "PYTHONPATH="
    cd /d "{exe_dir}"
    if exist "{old_exe_path}" (
        copy /y "{old_exe_path}" "{exe_path}" > NUL 2>&1
        start "" "{exe_path}"
    ) else if exist "{new_exe_path}" (
        copy /y "{new_exe_path}" "{exe_path}" > NUL 2>&1
        start "" "{exe_path}"
    )
)

timeout /t 2 /nobreak > NUL
(goto) 2>nul & del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)

            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            clean_env = os.environ.copy()
            clean_env.pop("_MEIPASS", None)
            clean_env.pop("_MEIPASS2", None)
            clean_env.pop("PYTHONHOME", None)
            clean_env.pop("PYTHONPATH", None)
            
            if "PATH" in clean_env:
                clean_paths = [p for p in clean_env["PATH"].split(os.pathsep) if "_MEI" not in p]
                clean_env["PATH"] = os.pathsep.join(clean_paths)
            
            subprocess.Popen(
                f'cmd.exe /c "{bat_path}"', 
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS, 
                close_fds=True,
                env=clean_env,
                shell=True
            )
            
            time.sleep(0.5)
            os._exit(0)
            return True
        except Exception as e:
            logging.error(f"[AUTO-UPDATER] Falha ao realizar atualização: {e}")
            raise e
