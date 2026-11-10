#!/usr/bin/env python3
"""Sincronização conservadora: somente comunicados verificáveis; preserva histórico."""
import json
import pathlib
import re
import urllib.request
from html.parser import HTMLParser

URL = "https://pxgtools.com.br/news"
OUTPUT = pathlib.Path("data/pxg-news.json")
POKEMON = {
    "Vikavolt": 738, "Galvantula": 596, "Heatran": 485, "Togekiss": 468,
    "Magmortar": 467, "Toxicroak": 454, "Lucario": 448, "Riolu": 447,
    "Raichu": 26, "Electabuzz": 125, "Arcanine": 59, "Typhlosion": 157,
    "Sylveon": 700, "Blaziken": 257, "Camerupt": 323, "Granbull": 210,
    "Manectric": 310, "Electrode": 101, "Pachirisu": 417, "Toxtricity": 849,
    "Magnezone": 462, "Gengar": 94, "Charizard": 6, "Dragonite": 149,
}
RULES = [
    ("Dimensional Zone", r"dimensional|master|giant|revives|boss|dungeon"),
    ("Hunts e respawns", r"respawn|shiny|selvag|spawn|hunt|catch|captur"),
    ("Quests e mapas", r"quest|missão|missões|mapa|caminho|npc|transporte"),
    ("Profissões e economia", r"profiss|coleta|diamond|shop|custo|preço"),
    ("Builds e mecânicas", r"held|ataque|habilidade|buff|nerf|runas|star sign|star path"),
]
class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self.skip += 1
        if tag in ("p", "li", "div", "article", "h1", "h2", "h3", "h4", "br"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self.skip:
            self.skip -= 1
        if tag in ("p", "li", "div", "article", "h1", "h2", "h3", "h4"):
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip:
            t = " ".join(data.split())
            if t:
                self.parts.append(t + " ")

def sections_from_body(body):
    # Separar em mudanças reais sem inventar efeitos, chances ou taxas.
    lines = [re.sub(r"\s+", " ", x).strip(" •-") for x in body.splitlines()]
    lines = [x for x in lines if len(x) >= 24]
    result = []
    for line in lines[:35]:
        low = line.lower()
        group = next((label for label, pattern in RULES if re.search(pattern, low)), "Outras mudanças")
        matched = next(((name, num) for name, num in POKEMON.items() if name.lower() in low), None)
        title = matched[0] if matched else group
        result.append({
            "title": title, "kind": group,
            "pokemon": matched[0] if matched else None,
            "num": matched[1] if matched else None,
            "change": line,
            "impact": "Verificar aplicabilidade ao Raibolt nível 598, levando em conta tipo, perigo, acesso e redução de XP/loot. Não há taxa ou rendimento presumido."
        })
    return result

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; EldertheusPXGHub/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = Parser()
    parser.feed(html)
    text = re.sub(r"[ \t]+", " ", "".join(parser.parts))
    text = re.sub(r"\n\s*\n+", "\n", text)
    markers = list(re.finditer(r"Notas de Atualização\s*[·•:-]\s*(\d{2}/\d{2}/\d{4})", text, re.I))
    if not markers:
        raise RuntimeError("Não foi possível validar as datas na fonte; mantendo histórico anterior.")
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {"notes": []}
    by_id = {n["id"]: n for n in old.get("notes", [])}
    added = 0
    for i, match in enumerate(markers[:25]):
        date = match.group(1)
        id_ = "pxg-" + date.replace("/", "-")
        if id_ in by_id:
            continue
        end = markers[i+1].start() if i+1 < len(markers) else min(len(text), match.end()+14000)
        body = text[match.end():end].strip()
        body = re.split(r"\n\s*(?:Leia mais|Voltar ao topo|Notícias anteriores)", body, maxsplit=1, flags=re.I)[0].strip()
        if len(body) < 60:
            continue
        sections = sections_from_body(body)
        if not sections:
            continue
        by_id[id_] = {"id": id_, "date": date, "title": "Atualização PXG · " + date,
            "body": body, "sections": sections, "source": URL,
            "sourceType": "Comunicado público reproduzido"}
        added += 1
    if not added:
        print("Nenhuma nova atualização verificável.")
        return
    def key(n):
        try:
            d,m,y = map(int, n["date"].split("/"))
            return (y,m,d)
        except (ValueError, KeyError):
            return (0,0,0)
    notes = sorted(by_id.values(), key=key, reverse=True)
    payload = {"source": URL, "notes": notes}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"{added} novas notas publicadas, {len(notes)} no histórico.")

if __name__ == "__main__":
    main()
