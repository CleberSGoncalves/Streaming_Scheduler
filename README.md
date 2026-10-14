# Streaming Scheduler

Aplicação desktop em Python com interface gráfica (Tkinter) para monitoramento, agendamento e automação de transmissões esportivas em múltiplos canais e plataformas de streaming (Amazon Prime, Cazé TV / YouTube, Disney, Dazn, Max, CBF), com sincronização automática em tempo real para o SharePoint e envio programado de relatórios por e-mail.

---

## ⚠️ REGRA CRÍTICA DE DESENVOLVIMENTO E RELEASE (GITHUB)

> [!IMPORTANT]
> **SEMPRE QUE UMA NOVA VERSÃO FOR GERADA OU UMA ALTERAÇÃO FOR CONCLUÍDA, É OBRIGATÓRIO ENVIAR PARA O GITHUB PARA NÃO PERDERMOS NADA.**
> 
> Todo código, tag de versão e executável compilado devem ser versionados e publicados no GitHub imediatamente.

### Checklist Obrigatório para Toda Nova Versão:
1. **Atualizar versão nos arquivos de controle**:
   - `version.json` (versão, download_url e changelog descritivo)
   - `ver.txt` (somente o número da versão, ex: `17.5`)
   - `version.txt` (somente o número da versão, ex: `17.5`)
   - `auto_updater.py` (`CURRENT_VERSION = "17.5"`)

2. **Compilar e Publicar via Script Automatizado**:
   Execute o script unificado na raiz do projeto:
   ```powershell
   python publish_release.py
   ```
   O script executa de ponta a ponta:
   - ✅ Compilação do executável com PyInstaller (`Streaming_Scheduler.spec`);
   - ✅ `git add .` e `git commit -m "vX.X: <changelog>"`;
   - ✅ `git push github main` (envia o código-fonte atualizado para o repositório remoto);
   - ✅ `git tag -a vX.X -m "vX.X"` e `git push github vX.X --force` (cria e envia a tag para o GitHub);
   - ✅ Criação automática da Release no GitHub via API;
   - ✅ Upload do binário `Streaming_Scheduler.exe` no GitHub Releases.

3. **Garantia de Preservação de Dados Pessoais do Usuário**:
   - O sistema de auto-atualização (`auto_updater.py`) substitui apenas o binário `Streaming_Scheduler.exe`.
   - **NUNCA** versionar, sobrescrever ou apagar as configurações locais de produção: `config.xml`, `auth.xml` e `secret.key`.

---

## 📦 Requisitos do Sistema

- **Python**: 3.12+ (x64)
- **Google Chrome**: Instalado (necessário para as portas de depuração 9222 e 9224 do Selenium)
- **ChromeDriver**: Compatível com a versão instalada do Chrome
- **Repositório GitHub**: `https://github.com/CleberSGoncalves/Streaming_Scheduler`

---

## ⚙️ Instalação e Configuração

1. **Clonar o Repositório**:
   ```powershell
   git clone https://github.com/CleberSGoncalves/Streaming_Scheduler.git
   cd Streaming_Scheduler
   ```

2. **Ativar o Ambiente Virtual**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instalar Dependências**:
   ```powershell
   pip install -r Requirements.txt
   ```

4. **Configurar Credenciais e Chaves de Criptografia**:
   - Crie o arquivo `secret.key` contendo a chave Fernet de 32 bytes base64 (gerada via `crypto_utils.gerar_chave()`).
   - Crie `config.xml` (a partir de `config.xml.example`) e configure as credenciais das plataformas.
   - Crie `auth.xml` (a partir de `auth.xml.example`) com e-mail e App Password do Gmail.

---

## 🚀 Como Executar

- **Execução direta em Python**:
  ```powershell
  python Streaming_Scheduler.py
  ```
- **Execução rápida via batch**:
  - `Inicializar_Streaming_Scheduler.bat`
  - `Gerador profile Chrome1.bat` / `Gerador profile Chrome2.bat`

---

## 🔄 Sistema de Atualização Automática (Auto-Updater)

O aplicativo conta com verificação nativa de novas versões:
- O módulo `auto_updater.py` consulta o endpoint `version.json` no branch `main` do GitHub.
- Ao detectar versão mais recente, permite atualizar com 1 clique.
- O executável novo é baixado de `https://github.com/CleberSGoncalves/Streaming_Scheduler/releases/download/<TAG>/Streaming_Scheduler.exe`.
- A substituição ocorre de forma atômica via `update_launcher.bat`, preservando integralmente `config.xml`, `auth.xml` e `data.csv`.

---

## 🛡️ Segurança e Boas Práticas

- Arquivos com credenciais e chaves criptográficas (`secret.key`, `auth.xml`, `config.xml`, `.env`, `.env.enc`) estão protegidos no `.gitignore` e não devem ser versionados publicamente.
- Todos os caminhos de arquivos locais utilizam `get_app_path(...)` baseado no diretório real do executável para evitar erros em inicializações via atalhos do Windows.
