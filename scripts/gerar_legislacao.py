#!/usr/bin/env python3
"""Gera o anexo de legislação para estudo, a partir das versões consolidadas da PGR Lisboa.
Não substitui a consulta da publicação oficial no Diário da República.
"""
import re
import html
import pathlib
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

HEADERS={"User-Agent":"Mozilla/5.0 (compatible; SMAS-Estudo/1.0)"}
SOURCES=[
("Lei n.º 102/2009, de 10 de setembro — segurança e saúde no trabalho",
 "https://www.pgdlisboa.pt/leis/lei_mostra_articulado.php?nid=1158&tabela=leis",[17]),
("Lei n.º 35/2014, de 20 de junho — Lei Geral do Trabalho em Funções Públicas",
 "https://www.pgdlisboa.pt/leis/lei_mostra_articulado.php?nid=2171&tabela=leis",list(range(45,52))+list(range(70,77)))
]
def fetch(url):
    response=requests.get(url,headers=HEADERS,timeout=35)
    response.raise_for_status()
    response.encoding=response.apparent_encoding or response.encoding
    soup=BeautifulSoup(response.text,"html.parser")
    for el in soup(["script","style","nav","footer","header"]): el.decompose()
    text=soup.get_text("\n",strip=True).replace("\xa0"," ")
    text=re.sub(r"[ \t]+"," ",text)
    return text

def extract(text,n):
    # A paginação da PGRL pode variar; procurar o artigo e delimitar pelo artigo seguinte.
    norm=re.sub(r"\n{3,}","\n\n",text)
    rx=re.compile(r"(?m)^Artigo\s+"+str(n)+r"\s*\.\s*º\s*$",re.I)
    starts=list(rx.finditer(norm))
    if not starts: raise ValueError(f"Artigo {n} não encontrado")
    start=starts[-1].start()
    nextart=re.search(r"(?m)^Artigo\s+\d+\s*\.\s*º\s*$",norm[starts[-1].end():],re.I)
    end=starts[-1].end()+nextart.start() if nextart else len(norm)
    body=norm[start:end]
    body=re.split(r"\n\s*Contém as alterações dos seguintes diplomas:",body)[0]
    body=re.split(r"\n\s*Consultar versões anteriores deste artigo:",body)[0]
    if not (100<=len(body)<=24000): raise ValueError(f"Artigo {n}: comprimento suspeito: {len(body)}")
    return body.strip()
blocks=[]
for title,url,numbers in SOURCES:
    raw=fetch(url)
    if len(raw)<3000: raise RuntimeError(f"Conteúdo muito curto em {url}")
    blocks.append("<h2>"+html.escape(title)+"</h2><p>Fonte de transcrição: <a href='"+html.escape(url,quote=True)+"'>PGR Lisboa — versão consolidada</a>. Validar sempre contra o <a href='https://diariodarepublica.pt/'>Diário da República</a>.</p>")
    for n in numbers:
        article=extract(raw,n)
        blocks.append("<section class='article' id='artigo-"+str(n)+("-sst" if "102" in title else "-ltfp")+"'><pre>"+html.escape(article)+"</pre></section>")
css="""body{margin:0;background:#f4f8fa;color:#16334a;font:16px/1.65 system-ui,sans-serif}main{max-width:950px;margin:0 auto;padding:30px 18px 80px}h1{line-height:1.2}h2{margin-top:40px}a{color:#086b98}.article{background:white;border:1px solid #dce8ef;border-radius:12px;padding:20px;margin:18px 0}pre{font:inherit;white-space:pre-wrap;overflow-wrap:break-word}.note{background:#eaf4f7;padding:15px;border-left:4px solid #0c7ca5;border-radius:8px}@media print{body{background:white}.article{break-inside:avoid}}"""
date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
out="<!doctype html><html lang='pt'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Legislação integral | Preparação SMAS Almada</title><style>"+css+"</style></head><body><main><p><a href='index.html'>← Voltar ao manual de estudo</a></p><h1>Legislação exigida na prova — texto integral dos artigos</h1><div class='note'>Transcrição automática de versões consolidadas, obtida em "+date+". Apenas os artigos indicados no programa. Consulte a fonte oficial para confirmar redação e vigência. Não confundir texto legal com resumos de estudo.</div>"+''.join(blocks)+"</main></body></html>"
pathlib.Path("legislacao.html").write_text(out,encoding="utf-8")
print(f"Gerado legislacao.html com {sum(len(x) for x in blocks)} caracteres")
