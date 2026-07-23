import json
import os

with open("config/clients.json") as f:
    clients = json.load(f)["clients"]

html = ["""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Criativos semanais</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<style>
body { font-family: sans-serif; background: #111; color: #eee; padding: 40px; }
h1 { font-size: 22px; }
h2 { font-size: 18px; margin-top: 40px; color: #f0a028; display: flex; align-items: center; gap: 16px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.grid img { width: 100%; border-radius: 8px; display: block; }
.grid a { text-decoration: none; color: #ccc; font-size: 13px; }
.download-btn {
  background: #f0a028; color: #1a1a1a; border: none; border-radius: 6px;
  padding: 8px 16px; font-size: 14px; font-weight: bold; cursor: pointer;
}
.download-btn:hover { background: #ffb84d; }
.download-btn:disabled { opacity: 0.6; cursor: default; }
</style>
</head>
<body>
<h1>Criativos gerados</h1>
"""]

script_lines = ["<script>",
                "async function baixarTodos(clientId, files, btn) {",
                "  btn.disabled = true;",
                "  const original = btn.textContent;",
                "  btn.textContent = 'Baixando...';",
                "  const zip = new JSZip();",
                "  for (const f of files) {",
                "    const resp = await fetch(`criativos/${clientId}/${f}`);",
                "    const blob = await resp.blob();",
                "    zip.file(f, blob);",
                "  }",
                "  const content = await zip.generateAsync({type: 'blob'});",
                "  const url = URL.createObjectURL(content);",
                "  const a = document.createElement('a');",
                "  a.href = url;",
                "  a.download = `${clientId}_criativos.zip`;",
                "  a.click();",
                "  URL.revokeObjectURL(url);",
                "  btn.disabled = false;",
                "  btn.textContent = original;",
                "}",
                "</script>"]

for client in clients:
    client_id = client["id"]
    folder = f"docs/criativos/{client_id}"
    files = []
    if os.path.isdir(folder):
        files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))

    files_js = json.dumps(files)
    btn_html = (
        f"<button class='download-btn' "
        f"onclick='baixarTodos(\"{client_id}\", {files_js}, this)'>"
        f"Baixar todos ({len(files)})</button>"
        if files else "<span style='color:#888; font-size:13px;'>nenhum criativo ainda</span>"
    )

    html.append(f"<h2>{client['display_name']} {btn_html}</h2><div class='grid'>")
    for fname in files:
        html.append(
            f"<a href='criativos/{client_id}/{fname}' target='_blank'>"
            f"<img src='criativos/{client_id}/{fname}'><br>{fname}</a>"
        )
    html.append("</div>")

html.extend(script_lines)
html.append("</body></html>")

with open("docs/index.html", "w") as f:
    f.write("\n".join(html))

print("docs/index.html atualizado")
