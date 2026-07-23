import json
import os

with open("config/clients.json") as f:
    clients = json.load(f)["clients"]

html = ["""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Criativos semanais</title>
<style>
body { font-family: sans-serif; background: #111; color: #eee; padding: 40px; }
h1 { font-size: 22px; }
h2 { font-size: 18px; margin-top: 40px; color: #f0a028; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.grid img { width: 100%; border-radius: 8px; display: block; }
.grid a { text-decoration: none; color: #ccc; font-size: 13px; }
</style>
</head>
<body>
<h1>Criativos gerados</h1>
"""]

for client in clients:
    client_id = client["id"]
    folder = f"docs/criativos/{client_id}"
    html.append(f"<h2>{client['display_name']}</h2><div class='grid'>")
    if os.path.isdir(folder):
        files = sorted(os.listdir(folder), reverse=True)
        for fname in files:
            if fname.endswith(".png"):
                html.append(
                    f"<a href='criativos/{client_id}/{fname}' target='_blank'>"
                    f"<img src='criativos/{client_id}/{fname}'><br>{fname}</a>"
                )
    html.append("</div>")

html.append("</body></html>")

with open("docs/index.html", "w") as f:
    f.write("\n".join(html))

print("docs/index.html atualizado")
