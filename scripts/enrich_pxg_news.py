#!/usr/bin/env python3
"""Etapa 2: enriquecimento editorial verificável, sem inventar números."""
import json
import pathlib
import re
import urllib.parse
import urllib.request

FILE = pathlib.Path("data/pxg-news.json")
POKEMON = {"Vikavolt":738,"Galvantula":596,"Heatran":485,"Togekiss":468,"Magmortar":467,"Toxicroak":454,"Lucario":448,"Riolu":447,"Raichu":26,"Electabuzz":125,"Arcanine":59,"Typhlosion":157,"Sylveon":700,"Blaziken":257,"Camerupt":323,"Granbull":210,"Manectric":310,"Electrode":101,"Pachirisu":417,"Toxtricity":849,"Magnezone":462}
WIKI = "https://wiki.pokexgames.com/api.php"
def wiki_image(name):
    # Usa apenas URLs retornadas pela API oficial da Wiki; sem adivinhar caminho.
    params = urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":name,"gsrnamespace":6,"gsrlimit":5,"prop":"imageinfo","iiprop":"url","format":"json"})
    try:
        req = urllib.request.Request(WIKI+"?"+params,headers={"User-Agent":"EldertheusHub/1.0 (public wiki image resolver)"})
        with urllib.request.urlopen(req,timeout=12) as r:
            obj=json.load(r)
        pages=obj.get("query",{}).get("pages",{})
        for page in pages.values():
            title=page.get("title","").lower()
            if name.lower() in title and page.get("imageinfo"):
                url=page["imageinfo"][0].get("url","")
                if url.startswith("https://wiki.pokexgames.com/"):
                    return url
    except (OSError,ValueError,KeyError):
        pass
    return None

def enrich(s):
    change=s.get("change","")
    title=s.get("title","")
    low=(change+" "+title).lower()
    name=next((n for n in POKEMON if re.search(r"\b"+re.escape(n.lower())+r"\b",low)),None)
    if name and not s.get("pokemon"):
        s["pokemon"]=name
        s["num"]=POKEMON[name]
    if name and not s.get("imageUrl"):
        image=wiki_image(name)
        if image:
            s["imageUrl"]=image
            s["imageCredit"]="Wiki PokeXGames"
    if re.search(r"mapa|rota|caminho|respawn",low,re.I):
        s["mapStatus"]="Mapa oficial ainda não vinculado" if not s.get("mapUrl") else "Mapa oficial verificado"
    if re.search(r"galvantula|heatran|sylveon|dimensional|master",low,re.I):
        s["category"]="Conteúdo de alta dificuldade"
    elif re.search(r"nightmare|quest|transporte",low,re.I):
        s["category"]="Conteúdo especial / quest"
    else:
        s["category"]=s.get("kind","Mudanças gerais")
    # Não substituir análises editoriais já revisadas.
    if not s.get("impact"):
        s["impact"]="Avaliar o efeito para Eldertheus nível 598, considerando vantagem de tipo, risco e penalidades documentadas de XP/loot."
    return s

def main():
    if not FILE.exists():
        print("Sem feed; nada a analisar.")
        return
    obj=json.loads(FILE.read_text(encoding="utf-8"))
    changed=False
    for note in obj.get("notes",[]):
        sections=note.get("sections",[])
        if not sections:
            continue
        old=json.dumps(sections,sort_keys=True,ensure_ascii=False)
        note["sections"]=[enrich(s) for s in sections]
        changed|=(old!=json.dumps(note["sections"],sort_keys=True,ensure_ascii=False))
    if changed:
        FILE.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Análise enriquecida." if changed else "Sem novas alterações de análise.")
if __name__=="__main__":
    main()
