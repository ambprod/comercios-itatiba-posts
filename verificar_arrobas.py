"""Confere se cada @ da fila existe no Instagram (via business_discovery).
Só leitura: não publica nada. Contas pessoais (não profissionais) não aparecem
nessa consulta e são marcadas para conferência manual."""
import csv
import os
import requests

GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v21.0')}"
IG = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]

with open("fila.csv", encoding="utf-8") as f:
    linhas = list(csv.DictReader(f))

print("| # | Comércio | @ na fila | Resultado no Instagram |")
print("|---|---|---|---|")
for l in linhas:
    user = l["arroba"].lstrip("@")
    r = requests.get(f"{GRAPH}/{IG}", params={
        "fields": f"business_discovery.username({user}){{username,name}}",
        "access_token": TOKEN}, timeout=30)
    if r.status_code == 200:
        bd = r.json()["business_discovery"]
        ok = "OK" if bd["username"] == user else f"DIFERENTE: @{bd['username']}"
        res = f"{ok} ({bd.get('name', '')})"
    else:
        res = "NÃO ENCONTRADA como conta profissional — conferir manualmente"
    print(f"| {l['ordem']} | {l['nome']} | @{user} | {res} |")
