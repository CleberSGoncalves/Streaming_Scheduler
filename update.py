import os
import platform
import paramiko
import subprocess
import sys
import time
from stat import S_ISREG
from tkinter import messagebox

class Update:
    """Classe para gerenciamento robusto de atualizações via SFTP utilizando unzip.exe."""
    
    def __init__(self, label, sftp_host, sftp_user, sftp_pass, remote_path, version_file, update_file, local_version_file, app_exe):
        self.label = label
        self.sftp_host = sftp_host
        self.sftp_user = sftp_user
        self.sftp_pass = sftp_pass
        self.remote_path = remote_path.rstrip('/')
        self.version_file = f"{self.remote_path}/{version_file}"
        self.update_file = f"{self.remote_path}/{update_file}"
        self.local_version_file = local_version_file
        self.app_exe = app_exe

    

    def preparar_atualizacao(self):
     """Prepara a atualização garantindo a criação do arquivo update.bat"""
     try:
        # 1. Verificar se os arquivos necessários existem
        arquivos_necessarios = {
            "update.zip": "Arquivo de atualização não encontrado",
            "version.txt": "Arquivo de versão não encontrado",            
        }

        for arquivo, mensagem_erro in arquivos_necessarios.items():
            if not os.path.exists(arquivo):
                raise FileNotFoundError(mensagem_erro)

        # 2. Verificar se o unzip.exe está disponível
        unzip_path = self._encontrar_unzip()
        if not unzip_path:
            raise Exception("unzip.exe não encontrado no sistema")

        # 3. Criar o conteúdo do batch file
        batch_content = self._gerar_conteudo_batch(unzip_path)

        # 4. Escrever o arquivo batch com múltiplas tentativas
        tentativas = 3
        for tentativa in range(tentativas):
            try:
                with open("update.bat", "w", encoding='utf-8') as bat_file:
                    bat_file.write(batch_content)
                
                # Verificar se o arquivo foi criado corretamente
                if os.path.exists("update.bat") and os.path.getsize("update.bat") > 0:
                    return True
                
                # Se chegou aqui, houve problema na criação
                if tentativa < tentativas - 1:
                    time.sleep(1)  # Espera antes de tentar novamente
                    continue
                    
                raise Exception("Falha ao criar update.bat (arquivo vazio ou inválido)")
            
            except PermissionError:
                if tentativa < tentativas - 1:
                    time.sleep(1)
                    continue
                raise Exception("Permissão negada para criar update.bat")
            except Exception as e:
                if tentativa < tentativas - 1:
                    time.sleep(1)
                    continue
                raise Exception(f"Erro ao criar update.bat: {str(e)}")

     except Exception as e:
        self.atualizar_label(f"⛔ Erro: {str(e)}")
        # Limpar arquivos temporários em caso de erro
        self._limpar_arquivos()
        return False

    def _encontrar_unzip(self):
     """Encontra o caminho para o unzip.exe"""
     # 1. Verifica no diretório atual
     if os.path.exists("unzip.exe"):
        return os.path.abspath("unzip.exe")
    
     # 2. Verifica no PATH do sistema
     for path_dir in os.environ["PATH"].split(os.pathsep):
        unzip_path = os.path.join(path_dir, "unzip.exe")
        if os.path.exists(unzip_path):
            return unzip_path
    
    # 3. Verifica em locais comuns
     locais_comuns = [
        os.path.join(os.environ["ProgramFiles"], "7-Zip"),
        os.path.join(os.environ["ProgramFiles(x86)"], "7-Zip"),
        r"C:\Program Files\WinRAR",
        r"C:\Program Files (x86)\WinRAR"
    ]
    
     for local in locais_comuns:
        unzip_path = os.path.join(local, "unzip.exe")
        if os.path.exists(unzip_path):
            return unzip_path
         
     return None

    def _gerar_conteudo_batch(self, unzip_path):
     """Gera o conteúdo do arquivo batch com tratamento robusto"""
     return f"""@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title Atualizador - Aguarde...

:: Log de execução
echo [%date% %time%] Iniciando atualização >> update.log

:: 1. Encerrar aplicação
echo Encerrando {self.app_exe}...
taskkill /IM "{self.app_exe}" /F >nul 2>&1

:: Esperar até encerrar
:esperar
tasklist /FI "IMAGENAME eq {self.app_exe}" 2>nul | find /I "{self.app_exe}" >nul
if %errorlevel% == 0 (
    timeout /t 1 /nobreak >nul
    goto esperar
)

:: 2. Extrair atualização
echo Extraindo atualização...
"{unzip_path}" -o update.zip >> update.log 2>&1
if %errorlevel% neq 0 (
    echo ERRO na extração >> update.log
    echo.
    echo ⚠️ ERRO: Falha ao extrair a atualização
    echo.
    pause
    exit /b 1
)

:: 3. Atualizar versão
if exist version.txt (
    if exist "{self.local_version_file}" del "{self.local_version_file}"
    ren version.txt "{os.path.basename(self.local_version_file)}"
)

:: 4. Iniciar nova versão
echo Iniciando nova versão...
start "" "{os.path.abspath(self.app_exe)}"

:: 5. Limpeza
del update.zip 2>nul

echo.
echo ✔ Atualização concluída com sucesso!
echo.
pause
del "%~f0" 2>nul
exit /b 0
"""

    def _limpar_arquivos(self):
     """Remove arquivos temporários em caso de erro"""
     for arquivo in ["update.bat", "version.txt", "update_temp.txt"]:
        try:
            if os.path.exists(arquivo):
                os.remove(arquivo)
        except Exception:
            pass


    def atualizar_label(self, mensagem):
        """Atualiza o label na interface de forma segura."""
        try:
            if self.label is None:
                return
            if not hasattr(self.label, "winfo_exists"):
                return
            if self.label.winfo_exists():
                self.label.config(text=mensagem)
                self.label.update_idletasks()
        except Exception:
            # nunca deixar update quebrar a aplicação
            pass

    def testar_conexao_sftp(self):
        """Testa a conexão SFTP com tratamento de erros."""
        try:
            transport = paramiko.Transport((self.sftp_host, 22))
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            transport.close()
            return True
        except Exception as e:
            self.atualizar_label(f"⛔ Erro de conexão: {str(e)}")
            return False

    def verificar_arquivo_remoto(self, remote_path):
        """Verifica se um arquivo existe no servidor SFTP."""
        transport = None
        sftp = None
        try:
            transport = paramiko.Transport((self.sftp_host, 22))
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.stat(remote_path)
            return True
        except IOError:
            return False
        except Exception as e:
            self.atualizar_label(f"⚠️ Erro ao verificar arquivo: {str(e)}")
            return False
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()

    def baixar_arquivo_sftp(self, remote_path, local_path, timeout=30):
        """Baixa arquivo via SFTP com validação."""
        transport = None
        sftp = None
        try:
            transport = paramiko.Transport((self.sftp_host, 22))
            transport.banner_timeout = timeout
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            file_stat = sftp.stat(remote_path)
            if not S_ISREG(file_stat.st_mode):
                raise Exception("Caminho remoto não é um arquivo regular")
            
            def callback(bytes_transferred, total_bytes):
                percent = (bytes_transferred / total_bytes) * 100
                self.atualizar_label(f"⬇️ Baixando... {percent:.1f}%")
            
            sftp.get(remote_path, local_path, callback=callback)
            
            if not os.path.exists(local_path):
                raise Exception("Arquivo local não foi criado")
            if os.path.getsize(local_path) == 0:
                os.remove(local_path)
                raise Exception("Arquivo baixado está vazio")
                
            return True
            
        except Exception as e:
            self.atualizar_label(f"⚠️ Erro no download: {str(e)}")
            return False
        finally:
            try:
                if sftp:
                    sftp.close()
                if transport:
                    transport.close()
            except:
                pass

    def verificar_atualizacao(self, timeout=30):
     """Verifica e gerencia atualizações sem usar arquivos temporários"""
     try:
        # 1. Verificação inicial
        self.atualizar_label("🔍 Conectando ao servidor...")
        if not self.testar_conexao_sftp():
            return False

        # 2. Verifica se existe versão remota
        if not self.verificar_arquivo_remoto(self.version_file):
            self.atualizar_label("⚠️ Arquivo de versão não encontrado no servidor")
            return False

        # 3. Baixa versão remota diretamente para version.txt
        if not self.baixar_arquivo_sftp(self.version_file, "version.txt",timeout=timeout):
            return False

        # 4. Processa versões
        with open("version.txt", "r") as f:
            versao_remota = f.read().strip()

        versao_local = "0.0"
        if os.path.exists(self.local_version_file):
            with open(self.local_version_file, "r") as f:
                versao_local = f.read().strip()

        try:
            if float(versao_remota) > float(versao_local):
                self.atualizar_label(f"🔄 Nova versão {versao_remota} disponível")
                
                # 5. Baixa atualização
                if not self.verificar_arquivo_remoto(self.update_file):
                    raise Exception("Arquivo de atualização não encontrado no servidor")
                    
                if not self.baixar_arquivo_sftp(self.update_file, "update.zip"):
                    raise Exception("Falha ao baixar atualização")
                
                # 6. Valida arquivo de atualização
                if os.path.getsize("update.zip") < 1024:  # 1KB mínimo
                    os.remove("update.zip")
                    raise Exception("Arquivo de atualização inválido")
                
                return True
            else:
                self.atualizar_label("✅ Sistema atualizado")
                # Remove o version.txt se não for usado
                if os.path.exists("version.txt"):
                    os.remove("version.txt")
                return False
                
        except ValueError:
            raise Exception("Formato de versão inválido")
            
     except Exception as e:
        self.atualizar_label(f"❌ Erro: {str(e)}")
        # Limpeza em caso de erro
        if os.path.exists("version.txt"):
            os.remove("version.txt")
        return False

    def encerrar_e_atualizar(self):
     """Gera o arquivo update.bat com todas as instruções necessárias"""
     try:
        cwd = os.path.abspath('.')
        exe_path = os.path.join(cwd, self.app_exe)
        
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"Executável {self.app_exe} não encontrado!")
        
        if not os.path.exists("update.zip"):
            raise FileNotFoundError("Arquivo update.zip não encontrado!")
        
        if not os.path.exists("version.txt"):
            raise FileNotFoundError("Arquivo version.txt não encontrado!")

        # Conteúdo do arquivo batch
        bat_content = f"""@echo off
chcp 65001 > nul
echo [Atualizador] Encerrando aplicação...
taskkill /IM "{self.app_exe}" /F > nul 2>&1
timeout /t 3 /nobreak > nul

echo [Atualizador] Extraindo arquivos...
unzip.exe -o update.zip || (
    echo ERRO: Falha ao extrair atualização
    pause
    exit /b 1
)

echo [Atualizador] Atualizando versão...
if exist version.txt (
    if exist "{self.local_version_file}" del "{self.local_version_file}"
    ren version.txt "{os.path.basename(self.local_version_file)}"
)

echo [Atualizador] Iniciando nova versão...
start "" "{exe_path}"

echo [Atualizador] Finalizando...
del update.zip
del "%~f0"
"""
        # Escreve o arquivo batch
        with open("update.bat", "w", encoding='utf-8') as bat_file:
            bat_file.write(bat_content)
            
        return True
        
     except Exception as e:
        self.atualizar_label(f"⛔ Erro ao preparar atualização: {str(e)}")
        return False


