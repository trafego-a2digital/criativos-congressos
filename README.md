# Gerador semanal de criativos

Gera automaticamente, toda semana, os criativos de imagem (1080x1080) para
venda de ingresso de eventos/congressos, no mesmo padrao usado no CBFD:
logo com fundo removido, foto de fundo esmaecida, headline gerado por IA,
pills de data/desconto e botao de CTA.

## Como funciona

1. **GitHub Actions** roda toda segunda-feira (`workflow_dispatch` tambem
   disponivel para rodar manualmente).
2. Para cada cliente ativo em `config/clients.json`:
   - `generate_copy.py` chama a **Gemini API** e gera headline + subtexto,
     variando entre os `copy_angles` definidos.
   - `fetch_photo.py` busca uma foto em **Pexels** (ou Unsplash, como
     fallback) usando as queries definidas em `photo_search`.
   - `render_creative.py` monta a imagem final com Pillow.
3. O PNG final e salvo em `docs/criativos/{cliente}/{data}.png` e commitado
   de volta no repo.
4. `docs/index.html` funciona como galeria, servida via **GitHub Pages**
   (ative em Settings > Pages > Source: branch `main`, pasta `/docs`).

## Configurar

1. Crie o repositorio no GitHub e suba esta pasta.
2. Em Settings > Secrets and variables > Actions, adicione:
   - `GEMINI_API_KEY`
   - `PEXELS_API_KEY` (crie gratis em pexels.com/api)
   - `UNSPLASH_ACCESS_KEY` (opcional, fallback)
3. Ative o GitHub Pages apontando para a pasta `docs/`.
4. Rode manualmente uma vez pela aba Actions ("Run workflow") pra validar
   antes de deixar no automatico.

## Adicionar um novo cliente/evento

Duplique um bloco em `config/clients.json` com:
- cores da marca (`bg_start`, `bg_end`, `wave`, `accent`, `text_muted`)
- `logo_file` apontando pra um PNG em `assets/logos/` (pode ter fundo solido
  -- o script remove automaticamente por diferenca de cor; se tiver o PNG
  ja transparente do cliente, e melhor ainda)
- dados da oferta (`discount_label`, `installments`, datas, local, CTA)
- `photo_search.queries` com termos de busca (em ingles funciona melhor no
  Pexels/Unsplash)
- `copy_angles`: lista de angulos que o Gemini vai revezar semana a semana

Nenhuma mudanca de codigo e necessaria para adicionar clientes novos -- e
por isso que uma conta/repo so aguenta quantos clientes voce quiser, ao
contrario do limite de 2 cenarios ativos do Make free.

## Rodando localmente pra testar

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
export PEXELS_API_KEY=...
cd scripts
python main.py
python build_gallery.py
```

## Limitacoes conhecidas

- `remove_bg.py` remove fundo por diferenca de cor (funciona bem pra fundo
  solido/quase solido). Logos com fundo complexo ou gradiente forte podem
  precisar de um PNG ja transparente.
- APIs gratuitas do Pexels/Unsplash tem rate limit -- com 1 chamada por
  cliente por semana, folga enorme mesmo com dezenas de clientes.
- Gemini pode ocasionalmente devolver um JSON mal formado; `generate_copy.py`
  cai num fallback fixo se a chave nao estiver configurada, mas nao trata
  erro de parsing ainda -- vale adicionar um retry se isso acontecer na
  pratica.
