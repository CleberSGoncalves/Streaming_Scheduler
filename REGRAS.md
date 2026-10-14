# REGRAS DO PROJETO STREAMING SCHEDULER

## 🚨 REGRA OBRIGATÓRIA: ENVIO PARA O GITHUB A CADA NOVA VERSÃO

> **ATENÇÃO:** Sempre que uma nova versão ou correção for gerada no projeto, ela DEVE ser enviada para o GitHub para não perdermos o histórico nem as alterações.

### Procedimento Padrão para Lançamento de Versão:

1. **Atualizar Arquivos de Versão**:
   - `version.json`
   - `ver.txt`
   - `version.txt`
   - `auto_updater.py` (`CURRENT_VERSION`)

2. **Publicar no GitHub (Código + Tag + Release)**:
   - Executar o script oficial:
     ```powershell
     python publish_release.py
     ```
   - Este script executa:
     1. Compilação do executável com PyInstaller (`Streaming_Scheduler.spec`);
     2. `git add .` e `git commit`;
     3. `git push github main` (código-fonte);
     4. `git tag` e `git push github <tag>` (tag de versão);
     5. Publicação do executável `Streaming_Scheduler.exe` na Release do GitHub.

3. **Preservação dos Arquivos Locais**:
   - O atualizador (`auto_updater.py`) JAMAIS toca em `config.xml`, `auth.xml` ou `secret.key`.
   - Credenciais e configurações pessoais do usuário são sempre preservadas entre atualizações.
