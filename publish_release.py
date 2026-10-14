import os
import sys
import json
import urllib.request
import subprocess

CWD = r"e:\desenvolvimento\Streaming_Scheduler"
TAG = "v17.3"

# Lê dados de version.json
ver_json_path = os.path.join(CWD, "version.json")
with open(ver_json_path, "r", encoding="utf-8") as f:
    ver_data = json.load(f)

ver_num = ver_data.get("version", "17.3")
changelog = ver_data.get("changelog", "Atualização Streaming Scheduler")

print(f"[1/5] Compilando executável {TAG} com PyInstaller...")
res_build = subprocess.run(["pyinstaller", "Streaming_Scheduler.spec", "--noconfirm"], cwd=CWD)
if res_build.returncode != 0:
    print("[ERRO FATAL] Falha na compilação do PyInstaller.")
    sys.exit(1)
print(f"[SUCESSO] Compilação {TAG} concluída!")

print("[2/5] Commit e Push para o GitHub...")
subprocess.run(["git", "add", "."], cwd=CWD)
subprocess.run(["git", "commit", "-m", f"{TAG}: {changelog}"], cwd=CWD)
subprocess.run(["git", "push", "github", "main"], cwd=CWD)
subprocess.run(["git", "tag", "-a", TAG, "-m", TAG], cwd=CWD)
subprocess.run(["git", "push", "github", TAG, "--force"], cwd=CWD)

def get_git_credentials():
    p = subprocess.Popen(["git", "credential", "fill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=CWD)
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    user, pwd = None, None
    for line in out.splitlines():
        if line.startswith("username="):
            user = line.split("=", 1)[1].strip()
        elif line.startswith("password="):
            pwd = line.split("=", 1)[1].strip()
    return user, pwd

username, token = get_git_credentials()
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "ReleaseUploaderStreamingScheduler"
}

OWNER = "CleberSGoncalves"
REPO = "Streaming_Scheduler"
EXE_PATH = os.path.join(CWD, "dist", "Streaming_Scheduler.exe")

print(f"[3/5] Buscando ou Criando Release {TAG} no GitHub...")
url_get = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"
req_get = urllib.request.Request(url_get, headers=headers)

rel_data = None
try:
    with urllib.request.urlopen(req_get) as resp:
        rel_data = json.loads(resp.read().decode("utf-8"))
        print(f"[RELEASE EXISTENTE] ID: {rel_data['id']}")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"[RELEASE CRIANDO] Tag {TAG}...")
        url_create = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
        payload = {
            "tag_name": TAG,
            "target_commitish": "main",
            "name": f"{TAG} - Sistema de Atualização GitHub Releases",
            "body": changelog,
            "draft": False,
            "prerelease": False
        }
        req_c = urllib.request.Request(url_create, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req_c) as resp_c:
                rel_data = json.loads(resp_c.read().decode("utf-8"))
                print(f"[RELEASE CRIADA] ID: {rel_data['id']}")
        except Exception as e_c:
            print(f"[ERRO CRIAR] {e_c}")
    else:
        print(f"[ERRO GET] {e.code}")

if not rel_data:
    print(f"[ERRO FATAL] Não foi possível obter ou criar a release {TAG}.")
    sys.exit(1)

print("[4/5] Deletando asset antigo se existir...")
for asset in rel_data.get("assets", []):
    if asset["name"] == "Streaming_Scheduler.exe":
        print(f"[DELETANDO ASSET ANTIGO] ID: {asset['id']}")
        req_d = urllib.request.Request(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/assets/{asset['id']}", headers=headers, method="DELETE")
        try:
            urllib.request.urlopen(req_d)
            print("[SUCESSO] Asset antigo deletado!")
        except Exception as e_d:
            print(f"[AVISO DELETAR] {e_d}")

print(f"[5/5] Upload do novo executável {TAG} ({os.path.getsize(EXE_PATH) / (1024*1024):.1f} MB)...")
upload_url_template = rel_data.get("upload_url", "")
upload_url = upload_url_template.split("{")[0] + "?name=Streaming_Scheduler.exe"
file_size = os.path.getsize(EXE_PATH)

headers_up = dict(headers)
headers_up["Content-Type"] = "application/octet-stream"
headers_up["Content-Length"] = str(file_size)

with open(EXE_PATH, "rb") as f:
    binary_data = f.read()

req_up = urllib.request.Request(upload_url, data=binary_data, headers=headers_up, method="POST")
with urllib.request.urlopen(req_up) as resp_up:
    up_res = json.loads(resp_up.read().decode("utf-8"))
    print(f"\n[EXECUTAVEL {TAG} PUBLICADO COM SUCESSO!]")
    print(f"URL Direct Download: {up_res.get('browser_download_url')}")
