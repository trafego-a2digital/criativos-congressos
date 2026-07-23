import json
import os
from datetime import date

from fetch_photo import fetch_background_photo
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

        print(f"[{client_id}] fetching background photo...")
        photo_path = fetch_background_photo(
            client["photo_search"]["queries"],
            orientation=client["photo_search"].get("orientation", "squarish"),
            cache_path=f"/tmp/{client_id}_bg.jpg",
        )

        out_dir = f"docs/criativos/{client_id}"
        os.makedirs(out_dir, exist_ok=True)

        for i, angle in enumerate(client["copy_angles"], start=1):
            print(f"[{client_id}] generating copy for angle {i}/{len(client['copy_angles'])}: {angle}")
            copy = generate_weekly_copy(client, angle=angle)

            print(f"[{client_id}] rendering creative {i}...")
            img = render(
                client_config=client,
                copy=copy,
                photo_path=photo_path,
                logo_path=client["logo_file"],
            )

            out_path = f"{out_dir}/{today}_{i}.png"
            img.save(out_path, quality=95)
            print(f"[{client_id}] saved {out_path}")


if __name__ == "__main__":
    run()
