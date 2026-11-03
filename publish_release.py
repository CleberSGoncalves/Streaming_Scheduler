# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
import requests

CWD = r"e:\desenvolvimento\Streaming_Scheduler"

ver_json_path = os.path.join(CWD, "version.json")
with open(ver_json_path, "r", encoding="utf-8") as f:
    ver_data = json.load(f)

ver_num = str(ver_data.get("version", "17.7")).strip()
TAG = f"v{ver_num}" if not ver_num.startswith("v") else ver_num
changelog = ver_data.get("changelog", f"Versão {TAG} do Streaming Scheduler")

EXE_PATH = os.path.join(CWD, "dist", "Streaming_Scheduler.exe")
if not os.path.exists(EXE_PATH):
    print(f"[1/5] Compilando executável {TAG} com PyInstaller...")
    res_build = subprocess.run(["pyinstaller", "Streaming_Scheduler.spec", "--noconfirm"], cwd=CWD)
    if res_build.returncode != 0:
        print("[ERRO FATAL] Falha na compilação do PyInstaller.")
        sys.exit(1)
    print(f"[SUCESSO] Compilação {TAG} concluída!")
else:
    print(f"[1/5] Executável {TAG} já compilado e presente em dist ({os.path.getsize(EXE_PATH)/(1024*1024):.1f} MB).")

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

print(f"[3/5] Buscando ou Criando Release {TAG} no GitHub...")
url_get = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"

rel_data = None
resp_get = requests.get(url_get, headers=headers, verify=False, timeout=30)
if resp_get.status_code == 200:
    rel_data = resp_get.json()
    print(f"[RELEASE EXISTENTE] ID: {rel_data['id']}")
elif resp_get.status_code == 404:
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
    resp_c = requests.post(url_create, json=payload, headers=headers, verify=False, timeout=30)
    if resp_c.status_code in (200, 201):
        rel_data = resp_c.json()
        print(f"[RELEASE CRIADA] ID: {rel_data['id']}")
    else:
        print(f"[ERRO CRIAR RELEASE] {resp_c.status_code}: {resp_c.text}")
else:
    print(f"[ERRO GET RELEASE] {resp_get.status_code}: {resp_get.text}")

if not rel_data:
    print(f"[ERRO FATAL] Não foi possível obter ou criar a release {TAG}.")
    sys.exit(1)

print("[4/5] Deletando asset antigo se existir...")
for asset in rel_data.get("assets", []):
    if asset["name"] == "Streaming_Scheduler.exe":
        print(f"[DELETANDO ASSET ANTIGO] ID: {asset['id']}")
        url_d = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/assets/{asset['id']}"
        resp_d = requests.delete(url_d, headers=headers, verify=False, timeout=30)
        print(f"[STATUS DELETAR] {resp_d.status_code}")

print(f"[5/5] Upload do novo executável {TAG} ({os.path.getsize(EXE_PATH) / (1024*1024):.1f} MB)...")
upload_url_template = rel_data.get("upload_url", "")
upload_url = upload_url_template.split("{")[0] + "?name=Streaming_Scheduler.exe"
file_size = os.path.getsize(EXE_PATH)

headers_up = dict(headers)
headers_up["Content-Type"] = "application/octet-stream"

with open(EXE_PATH, "rb") as f:
    resp_up = requests.post(upload_url, data=f, headers=headers_up, verify=False, timeout=180)

if resp_up.status_code in (200, 201):
    up_res = resp_up.json()
    print(f"\n[EXECUTÁVEL {TAG} PUBLICADO COM SUCESSO!]")
    print(f"URL Direct Download: {up_res.get('browser_download_url')}")
else:
    print(f"[ERRO NO UPLOAD] {resp_up.status_code}: {resp_up.text}")
