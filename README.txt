# Streaming Scheduler

Projeto Python para agendamento e gerenciamento de streams com automação, coleta de dados e integração com SharePoint e YouTube.

---

## 📦 Requisitos

- Python 3.x
- pip
- Google Chrome (para automação Selenium)
- chromedriver.exe (compatível com sua versão do Chrome)

---

## ⚙️ Instalação

1️⃣ Clone o repositório:
git clone <URL_DO_SEU_REPOSITORIO_AZURE>

css
Copiar
Editar

2️⃣ Acesse a pasta:
cd Streaming_Scheduler

cpp
Copiar
Editar

3️⃣ Crie e ative um ambiente virtual:
python -m venv venv

No Windows
venv\Scripts\activate

csharp
Copiar
Editar

4️⃣ Instale as dependências:
pip install -r Requirements.txt

yaml
Copiar
Editar

---

## 🔐 Configuração de Ambiente

1️⃣ Gere uma chave de criptografia:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

markdown
Copiar
Editar

Copie o valor e salve como `secret.key` (arquivo já ignorado pelo .gitignore).

---

2️⃣ Configure os arquivos necessários:
- Crie `.env` a partir de `.env.enc.example`
- Crie `auth.xml` a partir de `auth.xml.example`
- Crie `config.xml` a partir de `config.xml.example`

Use os comandos/funções internas para criptografar os dados reais, como:
criptografar('sua_senha_aqui')

yaml
Copiar
Editar

---

## 🚀 Como Rodar

Você pode rodar diretamente:
python Streaming_Scheduler.py

yaml
Copiar
Editar

Ou usar os arquivos `.bat` incluídos para inicialização rápida:
- `Inicializar_Streaming_Scheduler.bat`
- `Instalador_App.bat`
- `Gerador profile Chrome1.bat` (etc.)

---

## 🛡️ Segurança

- Arquivos `.env.enc`, `auth.xml`, `config.xml` estão criptografados.
- O arquivo `secret.key` NÃO DEVE ser versionado.
- Para ambientes novos, gere uma nova `secret.key` ou use uma chave compartilhada segura.

---

## 🛠️ Scripts Úteis

- `update.py`: script para atualização.
- `crypto_utils.py`: funções de criptografia e descriptografia.
- `.bat` files: inicializadores e utilitários de ambiente.

---

## 💬 Contato

Para dúvidas, sugestões ou contribuições, entre em contato com o mantenedor do proj