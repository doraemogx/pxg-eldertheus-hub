#!/usr/bin/env python3
"""Importa notas públicas PXG sem gerar informações por IA."""
import json, re, pathlib, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

URL = "https://pxgtools.com.br/news"
OUTPUT = pathlib.Path("data/pxg-news.json")
class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self.skip += 1
        if tag in ("li", "p", "h1", "h2", "h3", "h4", "br", "div"):
            self.lines.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self.skip:
            self.skip -= 1
        if tag in ("li", "p", "h1", "h2", "h3", "h4", "div"):
            self.lines.append("\n")
    def handle_data(self, data):
        if not self.skip:
            value = " ".join(data.split())
            if value:
                self.lines.append(value + " ")

def main():
    req = urllib.request.Request(URL, headers={"User-Agent":"EldertheusPXGHub/1.0 (+public changelog reader)"})
    with urllib.request.urlopen(req, timeout=25) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = TextParser()
    parser.feed(html)
    text = re.sub(r"[ \t]+", " ", "".join(parser.lines))
    text = re.sub(r"\n\s*\n+", "\n", text)
    matches = list(re.finditer(r"Notas de Atualização\s*[·•-]\s*(\d{2}/\d{2}/\d{4})", text, re.I))
    if not matches:
        raise RuntimeError("Não foram encontradas notas oficiais no espelho; preservando arquivo anterior.")
    items = []
    for i, m in enumerate(matches[:12]):
        end = matches[i+1].start() if i+1 < len(matches) else min(len(text), m.end()+15000)
        body = text[m.end():end].strip()
        body = re.split(r"\n\s*\d{2}/\d{2}\s*[·•]", body)[0]
        body = body[:13000].strip()
        if len(body) < 40:
            continue
        items.append({"id":"pxg-"+m.group(1).replace("/","-"),"date":m.group(1),"title":"Notas de Atualização · "+m.group(1),"body":body,"source":URL,"sourceType":"Comunicado oficial reproduzido por PXG Tools"})
    if not items:
        raise RuntimeError("Extração vazia; preservando dados.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # A data da consulta fica fora do arquivo para evitar commits sem novidades.
    payload = {"source":URL,"notes":items}
    new = json.dumps(payload,ensure_ascii=False,indent=2)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != new:
        OUTPUT.write_text(new,encoding="utf-8")
        print(f"Atualizado: {len(items)} notas.")
    else:
        print("Sem alterações desde a última execução.")
if __name__ == "__main__":
    main()
