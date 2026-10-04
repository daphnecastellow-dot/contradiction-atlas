#!/usr/bin/env python3
"""Map conflicting claims without forcing premature resolution.\n\nContradiction is preserved as evidence state, not treated as an error.\n"""

from __future__ import annotations
import argparse, datetime as dt, json, re, sys
from pathlib import Path
from typing import Any

FORMAT="contradiction-atlas/0.1"
SOURCE_KINDS=("primary","contemporary-report","later-retelling","reference","analysis","other")
DIMENSIONS=("date","time","location","count","identity","sequence","wording","causation","interpretation","other")
STATUSES=("open","narrowed","resolved","insufficient-evidence")

class AtlasError(Exception): pass

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def valid_date(v):
    if re.fullmatch(r"\d{4}",v): return True
    try:
        if re.fullmatch(r"\d{4}-\d{2}",v): dt.date.fromisoformat(v+"-01"); return True
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}",v): dt.date.fromisoformat(v); return True
    except ValueError: pass
    return False

def new_project(title):
    title=title.strip()
    if not title: raise AtlasError("title cannot be empty")
    return {"format":FORMAT,"title":title,"created_at":now(),"sources":[],"claims":[],"conflicts":[]}

def next_id(items,prefix):
    nums=[int(x["id"][len(prefix):]) for x in items if x.get("id","").startswith(prefix) and x["id"][len(prefix):].isdigit()]
    return f"{prefix}{(max(nums) if nums else 0)+1:03d}"

def find(items,item_id,kind):
    for item in items:
        if item["id"]==item_id: return item
    raise AtlasError(f"{kind} not found: {item_id}")

def validate(d):
    if not isinstance(d,dict) or d.get("format")!=FORMAT: raise AtlasError("unsupported project format")
    if not isinstance(d.get("title"),str) or not d["title"].strip(): raise AtlasError("project requires a title")
    for k in ("sources","claims","conflicts"):
        if not isinstance(d.get(k),list): raise AtlasError(f"project requires a {k} list")
    sids=set()
    for s in d["sources"]:
        if not s.get("id") or s["id"] in sids: raise AtlasError("invalid or duplicate source id")
        sids.add(s["id"])
        if s.get("kind") not in SOURCE_KINDS: raise AtlasError(f"{s['id']}: invalid source kind")
        if not s.get("label","").strip(): raise AtlasError(f"{s['id']}: source label cannot be empty")
        if s.get("date") and not valid_date(s["date"]): raise AtlasError(f"{s['id']}: invalid date")
    cids=set()
    for c in d["claims"]:
        if not c.get("id") or c["id"] in cids: raise AtlasError("invalid or duplicate claim id")
        cids.add(c["id"])
        if not c.get("text","").strip(): raise AtlasError(f"{c['id']}: claim text cannot be empty")
        if any(s not in sids for s in c.get("sources",[])): raise AtlasError(f"{c['id']}: unknown source")
    xids,pairs=set(),set()
    for x in d["conflicts"]:
        if not x.get("id") or x["id"] in xids: raise AtlasError("invalid or duplicate conflict id")
        xids.add(x["id"])
        if x.get("left") not in cids or x.get("right") not in cids or x["left"]==x["right"]: raise AtlasError(f"{x['id']}: invalid claim pair")
        pair=frozenset((x["left"],x["right"]))
        if pair in pairs: raise AtlasError(f"{x['id']}: duplicate claim-pair conflict")
        pairs.add(pair)
        if x.get("dimension") not in DIMENSIONS or x.get("status") not in STATUSES: raise AtlasError(f"{x['id']}: invalid conflict metadata")
        if not x.get("history"): raise AtlasError(f"{x['id']}: conflict requires history")

def load(path):
    p=Path(path)
    if not p.exists(): raise AtlasError(f"project not found: {p}")
    try: d=json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e: raise AtlasError(f"invalid JSON: {e}") from e
    validate(d); return d

def save(path,d):
    validate(d); Path(path).write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def add_source(d,label,kind,date=None,url=None,note=None):
    if kind not in SOURCE_KINDS: raise AtlasError("invalid source kind")
    if date and not valid_date(date): raise AtlasError("date must be YYYY, YYYY-MM, or YYYY-MM-DD")
    if not label.strip(): raise AtlasError("source label cannot be empty")
    sid=next_id(d["sources"],"S")
    d["sources"].append({"id":sid,"label":label.strip(),"kind":kind,"date":date or "","url":url or "","note":note or ""})
    return sid

def add_claim(d,text,sources=None,scope=None,note=None):
    if not text.strip(): raise AtlasError("claim text cannot be empty")
    refs=list(dict.fromkeys(sources or []))
    for sid in refs: find(d["sources"],sid,"source")
    cid=next_id(d["claims"],"C")
    d["claims"].append({"id":cid,"text":text.strip(),"scope":scope or "","sources":refs,"note":note or ""})
    return cid

def attach(d,cid,sid):
    c=find(d["claims"],cid,"claim"); find(d["sources"],sid,"source")
    if sid not in c["sources"]: c["sources"].append(sid)

def add_conflict(d,left,right,dimension,note=None):
    find(d["claims"],left,"claim"); find(d["claims"],right,"claim")
    if left==right: raise AtlasError("a claim cannot conflict with itself")
    if dimension not in DIMENSIONS: raise AtlasError("invalid conflict dimension")
    pair=frozenset((left,right))
    if any(frozenset((x["left"],x["right"]))==pair for x in d["conflicts"]): raise AtlasError("that claim pair already has a conflict")
    xid=next_id(d["conflicts"],"X")
    d["conflicts"].append({"id":xid,"left":left,"right":right,"dimension":dimension,"status":"open","note":note or "","resolution":"","history":[{"at":now(),"action":"created","status":"open","reason":note or ""}]})
    return xid

def change_status(d,xid,status,reason,resolution=None):
    x=find(d["conflicts"],xid,"conflict")
    if status not in STATUSES: raise AtlasError("invalid conflict status")
    if not reason.strip(): raise AtlasError("status change requires a reason")
    old=x["status"]; x["status"]=status
    if resolution is not None: x["resolution"]=resolution.strip()
    x["history"].append({"at":now(),"action":"status","status":status,"previous_status":old,"reason":reason.strip(),"resolution":x.get("resolution","")})

def render_matrix(d):
    ids=[c["id"] for c in d["claims"]]
    if not ids: return "_No claims yet._\n"
    edges={frozenset((x["left"],x["right"])):x for x in d["conflicts"]}
    lines=["| | "+" | ".join(ids)+" |","|---|"+"|".join(["---"]*len(ids))+"|"]
    for a in ids:
        cells=[f"**{a}**"]
        for b in ids:
            if a==b: cells.append("·")
            else:
                x=edges.get(frozenset((a,b))); cells.append(f"{x['id']} · {x['status']}" if x else "")
        lines.append("| "+" | ".join(cells)+" |")
    return "\n".join(lines)+"\n"

def render_markdown(d):
    labels={s["id"]:s["label"] for s in d["sources"]}
    out=[f"# {d['title']}","",f"_Contradiction Atlas format: `{FORMAT}`_","","## Claims",""]
    if not d["claims"]: out+=["_No claims yet._",""]
    for c in d["claims"]:
        out += [f"### {c['id']}","",c["text"],""]
        if c.get("scope"): out += [f"**Scope:** {c['scope']}",""]
        if c.get("sources"): out += ["**Sources:** "+", ".join(f"{s} · {labels[s]}" for s in c["sources"]),""] 
        if c.get("note"): out += [f"**Note:** {c['note']}",""]
    out += ["## Conflicts",""]
    if not d["conflicts"]: out+=["_No conflicts recorded._",""]
    for x in d["conflicts"]:
        a=find(d["claims"],x["left"],"claim"); b=find(d["claims"],x["right"],"claim")
        out += [f"### {x['id']} · {x['dimension']} · {x['status']}","",f"**{a['id']}:** {a['text']}","",f"**{b['id']}:** {b['text']}",""]
        if x.get("note"): out += [f"**Conflict note:** {x['note']}",""]
        if x.get("resolution"): out += [f"**Resolution note:** {x['resolution']}",""]
        out += ["**History:**",""]
        for h in x["history"]:
            line=f"- {h['at']} · **{h['status']}** · {h['action']}"
            if h.get("reason"): line+=f" · {h['reason']}"
            out.append(line)
        out.append("")
    out += ["## Conflict matrix","",render_matrix(d).rstrip(),""]
    return "\n".join(out).rstrip()+"\n"

def render_mermaid(d):
    out=["flowchart LR"]
    for c in d["claims"]:
        label=c["text"].replace('"',"'").replace("\n"," ")
        out.append(f'  {c["id"]}["{c["id"]} · {label}"]')
    for x in d["conflicts"]:
        out.append(f'  {x["left"]} <-->|"{x["id"]} · {x["dimension"]} · {x["status"]}"| {x["right"]}')
    return "\n".join(out)+"\n"

def summary(d):
    return f"{d['title']}: {len(d['claims'])} claim(s), {len(d['conflicts'])} conflict(s), {sum(x['status']=='open' for x in d['conflicts'])} open"

def parser():
    p=argparse.ArgumentParser(prog="contradiction-atlas",description="Map conflicting claims without forcing premature resolution.")
    sub=p.add_subparsers(dest="command",required=True)
    q=sub.add_parser("new"); q.add_argument("file"); q.add_argument("--title",required=True)
    q=sub.add_parser("source"); q.add_argument("file"); q.add_argument("label"); q.add_argument("--kind",choices=SOURCE_KINDS,default="other"); q.add_argument("--date"); q.add_argument("--url"); q.add_argument("--note")
    q=sub.add_parser("claim"); q.add_argument("file"); q.add_argument("text"); q.add_argument("--source",action="append",default=[]); q.add_argument("--scope"); q.add_argument("--note")
    q=sub.add_parser("attach"); q.add_argument("file"); q.add_argument("claim_id"); q.add_argument("source_id")
    q=sub.add_parser("conflict"); q.add_argument("file"); q.add_argument("left_id"); q.add_argument("right_id"); q.add_argument("--dimension",choices=DIMENSIONS,required=True); q.add_argument("--note")
    q=sub.add_parser("status"); q.add_argument("file"); q.add_argument("conflict_id"); q.add_argument("status",choices=STATUSES); q.add_argument("--reason",required=True); q.add_argument("--resolution")
    for name in ("show","check"): q=sub.add_parser(name); q.add_argument("file")
    for name in ("render","matrix","mermaid"): q=sub.add_parser(name); q.add_argument("file"); q.add_argument("-o","--output")
    return p

def main(argv=None):
    a=parser().parse_args(argv)
    try:
        if a.command=="new":
            if Path(a.file).exists(): raise AtlasError("refusing to overwrite existing file")
            save(a.file,new_project(a.title)); print(f"created {a.file}"); return 0
        d=load(a.file)
        if a.command=="source": print(add_source(d,a.label,a.kind,a.date,a.url,a.note)); save(a.file,d)
        elif a.command=="claim": print(add_claim(d,a.text,a.source,a.scope,a.note)); save(a.file,d)
        elif a.command=="attach": attach(d,a.claim_id,a.source_id); save(a.file,d); print(f"{a.claim_id}:{a.source_id}")
        elif a.command=="conflict": print(add_conflict(d,a.left_id,a.right_id,a.dimension,a.note)); save(a.file,d)
        elif a.command=="status": change_status(d,a.conflict_id,a.status,a.reason,a.resolution); save(a.file,d); print(a.conflict_id)
        elif a.command=="show": print(summary(d))
        elif a.command=="check": print(f"ok: {a.file}")
        else:
            text={"render":render_markdown,"matrix":render_matrix,"mermaid":render_mermaid}[a.command](d)
            if a.output: Path(a.output).write_text(text,encoding="utf-8"); print(a.output)
            else: print(text,end="")
        return 0
    except AtlasError as e:
        print(f"contradiction-atlas: {e}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
