"""
Publica o próximo carrossel pendente da fila (fila.csv) no Instagram via Graph API.

Cada execução publica 1 post. O agendamento (GitHub Actions) roda 3x por dia.

Variáveis de ambiente (configuradas como Secrets no GitHub):
  IG_USER_ID       ID da conta profissional do Instagram (@comerciositatiba)
  IG_ACCESS_TOKEN  Token de acesso com permissão instagram_content_publish
Opcionais:
  GRAPH_VERSION    versão da API (padrão v21.0)
  DRY_RUN=1        só mostra o que seria publicado, sem publicar
  GITHUB_REPOSITORY / BRANCH  usados para montar o link público das imagens

Estrutura esperada:
  posts/<slug>/1.jpg, 2.jpg, 3.jpg   (JPEG, proporção entre 4:5 e 1.91:1)
  fila.csv  colunas: ordem,slug,nome,arroba,legenda,status,media_id,publicado_em
"""
import csv
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

RAIZ = Path(__file__).parent
FILA = RAIZ / "fila.csv"
GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v21.0')}"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("BRANCH", "main")
DRY_RUN = os.environ.get("DRY_RUN") == "1"
BRT = timezone(timedelta(hours=-3))


def api(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Erro da API em {path}: {r.status_code} {r.text}")
    return r.json()


def esperar_container(container_id, tentativas=30):
    for _ in range(tentativas):
        status = api("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} com status {status}")
        time.sleep(5)
    raise RuntimeError(f"Container {container_id} não ficou pronto a tempo")


def url_imagem(slug, arquivo):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/posts/{slug}/{arquivo}"


def publicar(linha):
    ig = os.environ["IG_USER_ID"]
    pasta = RAIZ / "posts" / linha["slug"]
    imagens = sorted(p.name for p in pasta.glob("*.jpg"))
    if not 2 <= len(imagens) <= 10:
        raise RuntimeError(f"{linha['slug']}: precisa de 2 a 10 JPEGs, achei {len(imagens)}")

    urls = [url_imagem(linha["slug"], i) for i in imagens]
    if DRY_RUN:
        print("[DRY_RUN] publicaria:", linha["nome"], urls, "\nLegenda:\n" + linha["legenda"])
        return "dry-run"

    filhos = []
    for u in urls:
        c = api("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"]
        esperar_container(c)
        filhos.append(c)

    carrossel = api("POST", f"{ig}/media", media_type="CAROUSEL",
                    children=",".join(filhos), caption=linha["legenda"])["id"]
    esperar_container(carrossel)
    return api("POST", f"{ig}/media_publish", creation_id=carrossel)["id"]


def main():
    with FILA.open(encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        campos = leitor.fieldnames
        linhas = list(leitor)

    pendentes = sorted((l for l in linhas if l["status"].strip().lower() == "pendente"),
                       key=lambda l: int(l["ordem"]))
    if not pendentes:
        print("Fila vazia: nada para publicar.")
        return

    linha = pendentes[0]
    print(f"Publicando: {linha['nome']} ({linha['arroba']})")
    try:
        media_id = publicar(linha)
    except Exception as e:  # registra a falha e segue para o próximo na próxima execução
        linha["status"] = "falha"
        linha["media_id"] = str(e)[:300]
        print("FALHA:", e, file=sys.stderr)
    else:
        if not DRY_RUN:
            linha["status"] = "publicado"
            linha["media_id"] = media_id
            linha["publicado_em"] = datetime.now(BRT).strftime("%Y-%m-%d %H:%M")
        print("OK:", media_id)

    if not DRY_RUN:
        with FILA.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(linhas)


if __name__ == "__main__":
    main()
