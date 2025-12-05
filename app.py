from flask import Flask, request, render_template_string
import requests
from urllib.parse import urlparse, parse_qs, unquote
import re

app = Flask(__name__)

# ============================
# NORMALIZAÇÃO DE LINKS
# ============================
def normalizar_url(url):
    debug = []
    try:
        original = url.strip()
        current = original
        debug.append(f"INICIAL: {original}")

        if "shp.ee" in current:
            r = requests.get(current, allow_redirects=True, timeout=10)
            current = r.url
            debug.append(f"DEPOIS REDIRECT SHP: {current}")

        if "shopee.com.br/universal-link" in current:
            parsed = urlparse(current)
            qs = parse_qs(parsed.query)
            if "redir" in qs:
                redir = unquote(qs["redir"][0])
                debug.append(f"DEPOIS DECOD REDIR: {redir}")
                current = redir

        return current, "\n".join(debug)

    except Exception as e:
        debug.append(f"ERRO NORMALIZAR: {e}")
        return url, "\n".join(debug)


# ============================
# EXTRAI JSON __NEXT_DATA__
# ============================
def extrair_json_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL
    )
    if match:
        return match.group(1)
    return None


# ============================
# REMOVE A MARCA D'ÁGUA
# ============================
def limpar_watermark(url):
    return re.sub(r'\.\d+\.\d+\.mp4$', '.mp4', url)


# ============================
# TEMPLATE HTML
# ============================
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Gerador de Link Shopee Sem Marca D'água</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 600px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h2 {
    margin-top: 0;
}

form {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

input, button {
    width: 100%;
    font-size: 16px;
    padding: 14px;
    border-radius: 10px;
    border: 1px solid #ccc;
    box-sizing: border-box;
}

button {
    background: #ff5b00;
    color: white;
    font-weight: bold;
    border: none;
}

button:hover {
    background: #e24e00;
}

.resultado-box {
    padding: 14px;
    margin-top: 20px;
    background: #e6ffe6;
    border-left: 4px solid #009900;
    border-radius: 10px;
}

.video-wrapper {
    margin-top: 12px;
}

.video-wrapper video {
    width: 100%;
    max-height: 320px;
    border-radius: 10px;
    background: #000;
}

.download-btn {
    margin-top: 12px;
    padding: 12px 20px;
    background: #ff5b00;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    width: 100%;
}

.download-btn:hover {
    background: #e24e00;
}

.debug-toggle {
    margin-top: 15px;
    font-size: 14px;
    cursor: pointer;
    color: #555;
}

.debug {
    margin-top: 5px;
    font-family: monospace;
    font-size: 13px;
    white-space: pre-wrap;
    background: #222;
    color: #0f0;
    padding: 10px;
    border-radius: 10px;
    display: none;
}
</style>

<script>
function toggleDebug() {
    var box = document.getElementById('debug-box');
    if (!box) return;
    box.style.display = (box.style.display === 'none' || box.style.display === '') ? 'block' : 'none';
}

async function baixarVideo(buttonEl) {
    try {
        var url = buttonEl.getAttribute('data-url');
        if (!url) {
            alert("Nenhum link encontrado.");
            return;
        }

        const response = await fetch(url);
        if (!response.ok) {
            alert("Erro ao baixar o vídeo (HTTP " + response.status + ").");
            return;
        }

        const blob = await response.blob();
        const link = document.createElement("a");
        const blobUrl = URL.createObjectURL(blob);

        link.href = blobUrl;
        link.download = "video_shopee.mp4";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(blobUrl);

    } catch (e) {
        alert("Erro ao baixar o vídeo.");
        console.error(e);
    }
}
</script>

</head>
<body>
<div class="container">
    <div class="card">
        <h2>Gerador de Link Shopee Sem Marca D'água</h2>

        <form method="POST">
            <label>Link da Shopee:</label>
            <input name="url" placeholder="Cole o link aqui..." required />
            <button type="submit">Gerar</button>
        </form>

        {% if erro %}
        <div class="resultado-box erro">
            {{ erro }}
        </div>
        {% endif %}

        {% if link_final %}
        <div class="resultado-box">

            <div class="video-wrapper">
                <b style="display:block; margin-bottom:8px;">Pré-visualização:</b>
                <video controls src="{{ link_final }}">
                    Seu navegador não suporta vídeo HTML5.
                </video>
            </div>

            <button
                type="button"
                class="download-btn"
                onclick="baixarVideo(this)"
                data-url="{{ link_final }}"
            >
                Download
            </button>

        </div>
        {% endif %}

        {% if debug %}
        <div class="debug-toggle" onclick="toggleDebug()">
            ▶ DEBUG (opcional)
        </div>
        <div id="debug-box" class="debug">{{ debug }}</div>
        {% endif %}
    </div>
</div>
</body>
</html>
"""


# ============================
# ROTA PRINCIPAL
# ============================
@app.route("/", methods=["GET", "POST"])
def index():
    erro = None
    link_final = None
    debug_log = ""

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        debug_log += f"URL RECEBIDA: {url}\n"

        url_norm, dbg_norm = normalizar_url(url)
        debug_log += f"URL NORMALIZADA: {url_norm}\n"
        debug_log += dbg_norm + "\n"

        try:
            r = requests.get(url_norm, timeout=10)
            debug_log += f"STATUS HTTP: {r.status_code}\n"
            debug_log += f"URL FINAL REQUESTS: {r.url}\n"

            if r.status_code != 200:
                erro = f"Erro ao acessar a página: {r.status_code}"
                return render_template_string(HTML, erro=erro, debug=debug_log)

            html = r.text

            json_text = extrair_json_next_data(html)
            if not json_text:
                erro = "Não encontrei JSON __NEXT_DATA__ na página."
                return render_template_string(HTML, erro=erro, debug=debug_log)

            match = re.search(r'"watermarkVideoUrl":"(.*?)"', json_text)
            if not match:
                erro = "Não encontrei o link do vídeo."
                return render_template_string(HTML, erro=erro, debug=debug_log)

            url_watermark = match.group(1).replace("\\/", "/")
            debug_log += f"WATERMARK URL: {url_watermark}\n"

            url_clean = limpar_watermark(url_watermark)
            debug_log += f"URL LIMPA: {url_clean}\n"

            link_final = url_clean

        except Exception as e:
            erro = f"Erro interno: {str(e)}"

    return render_template_string(HTML, link_final=link_final, erro=erro, debug=debug_log)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
