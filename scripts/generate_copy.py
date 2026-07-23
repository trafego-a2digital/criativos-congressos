"""
Calls the Gemini API to generate this week's headline + supporting copy for
a client's creative, rotating through the angles defined in clients.json.

Env var expected: GEMINI_API_KEY
"""
import os
import json
import random
import time
import requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

PROMPT_TEMPLATE = """Voce e um copywriter de anuncios (Meta Ads) especializado em vender
ingressos para congressos e eventos profissionais no Brasil.

Evento: {display_name}
Oferta atual: {discount_label}, {installments}
Categorias de ingresso: {ticket_tiers}
Data: {date_label}
Local: {location_label}
Palestrantes confirmados (use nomes reais quando o angulo pedir): {speakers}

Angulo desta semana: {angle}

Gere um JSON com exatamente estas chaves, em portugues do Brasil, sem
acentuacao problematica, linguagem direta e sem cliche de IA (nada de
"desbloqueie", "imperdivel", "transformador"). Se o angulo mencionar citar
palestrantes, escolha 2 a 3 nomes da lista fornecida e cite pelo nome real
(nao invente nomes que nao estao na lista):

{{
  "headline_lines": ["linha 1", "linha 2", "linha 3 (max 3 linhas curtas)"],
  "highlight_word": "uma palavra da ultima linha do headline para destacar em cor de acento",
  "subtext": "uma frase curta de apoio, max 90 caracteres"
}}

Responda apenas com o JSON, sem markdown, sem comentario."""


def generate_weekly_copy(client_config, angle=None):
    offer = client_config["offer"]
    angle = angle or random.choice(client_config["copy_angles"])
    speakers = client_config.get("speakers", [])
    speakers_sample = random.sample(speakers, min(6, len(speakers))) if speakers else []

    prompt = PROMPT_TEMPLATE.format(
        display_name=client_config["display_name"],
        discount_label=offer["discount_label"],
        installments=offer["installments"],
        ticket_tiers="; ".join(offer.get("ticket_tiers", [])),
        date_label=offer["date_label"],
        location_label=offer["location_label"],
        speakers=", ".join(speakers_sample) if speakers_sample else "nao informado",
        angle=angle,
    )

    if not GEMINI_KEY:
        # fallback so the pipeline still produces something without a key
        return {
            "headline_lines": ["Garanta seu ingresso", "com desconto para o", "CBFD 2026"],
            "highlight_word": "CBFD",
            "subtext": f"{offer['discount_label']} - {offer['installments']}",
        }

    body = {"contents": [{"parts": [{"text": prompt}]}]}

    max_attempts = 4
    for attempt in range(max_attempts):
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            json=body,
            timeout=30,
        )
        if r.status_code == 429:
            wait = 20 * (attempt + 1)
            print(f"Gemini 429 (rate limit), aguardando {wait}s antes de tentar de novo "
                  f"(tentativa {attempt + 1}/{max_attempts})...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        break
    else:
        raise RuntimeError("Gemini continuou retornando 429 apos varias tentativas")

    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().strip("`").replace("json\n", "", 1)
    return json.loads(text)


if __name__ == "__main__":
    with open("config/clients.json") as f:
        clients = json.load(f)["clients"]
    result = generate_weekly_copy(clients[0])
    print(json.dumps(result, indent=2, ensure_ascii=False))
