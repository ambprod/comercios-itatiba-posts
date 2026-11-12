# Comércios Itatiba — publicação automática no Instagram

Publica 1 carrossel por execução no @comerciositatiba, via Graph API, às 11h, 15h e 19h (horário de Brasília).

## Como funciona
- `posts/<slug>/1.jpg, 2.jpg, 3.jpg` — as 3 telas do carrossel de cada comércio (JPEG, proporção 4:5 recomendada: 1080×1350).
- `fila.csv` — ordem de publicação, legenda e status (`pendente` → `publicado` ou `falha`).
- `publicar.py` — pega o próximo `pendente`, publica e registra o resultado na fila.
- `.github/workflows/publicar.yml` — agendamento.

## Secrets necessários (Settings → Secrets and variables → Actions)
- `IG_USER_ID` — ID da conta do Instagram
- `IG_ACCESS_TOKEN` — token com `instagram_content_publish`

## Testar sem publicar
Actions → "Publicar carrossel no Instagram" → Run workflow → deixar "Só testar" marcado.

## Pausar
Actions → workflow → "Disable workflow". Itens com status diferente de `pendente` (ex.: `aguardando`, `pausado`) não são publicados.

## Reprocessar uma falha
Trocar o status da linha de `falha` para `pendente`.
