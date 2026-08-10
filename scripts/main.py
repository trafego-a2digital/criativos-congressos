import json
import os
import shutil
import time
from datetime import date

from fetch_photo import fetch_multiple_backgrounds
from generate_copy import generate_weekly_copy
from render_creative import render


def run():
    with open("config/clients.json") as f:
        clients = json.load(f)["clients"]

    today = date.today().isoformat()

    for client in clients:
        if not client.get("active", True):
            continue

        client_id = client["id"]
        out_dir = f"docs/criativos/{client_id}"

        # limpa a semana anterior antes de gerar a nova -- so mantem a rodada atual
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        themes = client.get("themes") or [client["colors"]]
        layouts = ["classico", "foto_destaque", "selo_central"]
        angles = client["copy_angles"]

        print(f"[{client_id}] fetching {len(angles)} distinct background photos...")
        photo_paths = fetch_multiple_backgrounds(
            client["photo_search"]["queries"],
            count=len(angles),
            orientation=client["photo_search"].get("orientation", "squarish"),
            cache_prefix=f"/tmp/{client_id}_bg",
        )

        for i, angle in enumerate(angles, start=1):
            if i > 1:
                # espaca as chamadas pra nao estourar o limite por minuto da
                # chave do Gemini (ainda mais se ela for compartilhada com
                # outras automacoes rodando perto do mesmo horario)
                print(f"[{client_id}] aguardando 12s antes da proxima chamada ao Gemini...")
                time.sleep(12)

            print(f"[{client_id}] generating copy for angle {i}/{len(angles)}: {angle}")
            copy = generate_weekly_copy(client, angle=angle)

            theme = themes[(i - 1) % len(themes)]
            layout = layouts[(i - 1) % len(layouts)]
            photo_path = photo_paths[i - 1]
            print(f"[{client_id}] rendering creative {i} -- theme '{theme.get('name', i)}', "
                  f"layout '{layout}', photo '{os.path.basename(photo_path)}'...")
            img = render(
                client_config=client,
                copy=copy,
                photo_path=photo_path,
                logo_path=client["logo_file"],
                colors_override=theme,
                layout=layout,
            )

            out_path = f"{out_dir}/{today}_{i}.png"
            img.save(out_path, quality=95)
            print(f"[{client_id}] saved {out_path}")


if __name__ == "__main__":
    run()
