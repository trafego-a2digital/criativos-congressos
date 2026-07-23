"""
Calls the Gemini API to generate this week's headline + supporting copy for
a client's creative, rotating through the angles defined in clients.json.

Env var expected: GEMINI_API_KEY
"""
import os
import json
import random
import requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

PROMPT_TEMPLATE = """Voce e um copywriter de anuncios (Meta Ads) especializado em vender
ingressos para congressos e eventos profissionais no Brasil.

Evento: {display_name}
Oferta atual: {discount_label}, {installments}
Data: {date_label}
Local: {location_label}

Angulo desta semana: {angle}

Gere um JSON com exatamente estas chaves, em portugues do Brasil, sem
acentuacao problematica, linguagem direta e sem cliche de IA (nada de
"desbloqueie", "imperdivel", "transformador"):

{{
  "headline_lines": ["linha 1", "linha 2", "linha 3 (max 3 linhas curtas)"],
  "highlight_word": "uma palavra da ultima linha do headline para destacar em cor de acento",
  "subtext": "uma frase curta de apoio, max 90 caracteres"
}}

Responda apenas com o JSON, sem markdown, sem comentario."""


def generate_weekly_copy(client_config, angle=None):
    offer = client_config["offer"]
    angle = angle or random.choice(client_config["copy_angles"])

    prompt = PROMPT_TEMPLATE.format(
        display_name=client_config["display_name"],
        discount_label=offer["discount_label"],
        installments=offer["installments"],
        date_label=offer["date_label"],
        location_label=offer["location_label"],
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
    r = requests.post(
        f"{GEMINI_URL}?key={GEMINI_KEY}",
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().strip("`").replace("json\n", "", 1)
    return json.loads(text)


if __name__ == "__main__":
    with open("config/clients.json") as f:
        clients = json.load(f)["clients"]
    result = generate_weekly_copy(clients[0])
    print(json.dumps(result, indent=2, ensure_ascii=False))
