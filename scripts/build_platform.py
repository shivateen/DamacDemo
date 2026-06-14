#!/usr/bin/env python3
"""
CloseIQ Platform — consolidated build
Assembles a single platform.html (the shell) plus three standalone app files,
injecting shell-navigation hooks into Evolution and Command Center.

Run:  python scripts/build_platform.py
Output: public/index.html (shell) + public/app-*.html (the three apps)
"""
import json, pathlib, re
from datetime import datetime

ROOT   = pathlib.Path(__file__).parent.parent
SRC    = ROOT / 'src'
APPS   = SRC / 'apps'
OUT    = ROOT / 'public'
SCRIPT = pathlib.Path(__file__).parent

def read(p):  return pathlib.Path(p).read_text(encoding='utf-8')
def write(p, s): pathlib.Path(p).write_text(s, encoding='utf-8')


# ── 1. Build the CloseIQ app (data + css + js + pptx bundle inline) ──────────
def build_closeiq():
    css     = read(SRC / 'css' / 'app.css')
    app_js  = read(SRC / 'js'  / 'app.js')
    data_js = json.dumps(json.loads(read(SRC / 'data' / 'closeiq_data.json')), separators=(',', ':'))
    bundle  = read(SCRIPT / 'pptxgen.bundle.js')
    body_html = read(SRC / 'html' / 'closeiq_body.html')
    app_js  = app_js.replace('__CLOSEIQ_DATA__', data_js)
    favicon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
               "%3Crect width='32' height='32' rx='7' fill='%23F08C1E'/%3E%3Ctext x='16' y='22' "
               "font-family='Poppins,Arial' font-size='17' font-weight='700' fill='white' "
               "text-anchor='middle'%3ET%3C/text%3E%3C/svg%3E")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloseIQ · Autonomous Month-End Close</title>
<link rel="icon" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
<style>
{css}
</style>
</head>
<body>
{body_html}
<script>
{bundle}
</script>
<script>
{app_js}
</script>
</body>
</html>"""


# ── 2. Inject shell hooks into Evolution ─────────────────────────────────────
def build_evolution():
    html = read(APPS / 'evolution.html')
    # Replace the CTA link to talk to the shell instead of a missing file
    html = html.replace(
        '<a class="btn" href="damac-command-center_v3.html"><i class="ti ti-arrow-right"></i> Open the command center</a>',
        '<a class="btn" href="#" onclick="if(window.parent!==window){window.parent.postMessage({__navTo:\'command\'},\'*\');return false;}"><i class="ti ti-arrow-right"></i> Open the command center</a>'
    )
    # Inject: reveal the platform bar once the user scrolls past the hero
    inject = """
<script>
(function(){
  if(window.parent===window) return;  // only when embedded in shell
  var sent=false;
  window.addEventListener('scroll', function(){
    if(!sent && window.scrollY>400){ sent=true; window.parent.postMessage({__showBar:true},'*'); }
  }, {passive:true});
})();
</script>
"""
    return html.replace('</body>', inject + '</body>')


# ── 3. Inject shell hooks into Command Center ────────────────────────────────
def build_command():
    html = read(APPS / 'command-center.html')
    # Inject a script that adds an "Open CloseIQ" launcher when the controllership
    # tower page is shown, and routes the Wave 1 TB-scrutiny action to CloseIQ.
    inject = """
<script>
(function(){
  if(window.parent===window) return;  // only when embedded in shell

  function addCloseIQLauncher(){
    var main = document.getElementById('main');
    if(!main) return;
    // Only on the controllership tower page
    var isControllership = /Controllership/.test(main.textContent||'') &&
                           /day 7|continuous close|trial-balance/i.test(main.textContent||'');
    if(!isControllership){ return; }
    if(document.getElementById('__closeiqLauncher')) return;

    var banner = document.createElement('div');
    banner.id = '__closeiqLauncher';
    banner.style.cssText = 'margin:14px 0;padding:16px 18px;border-radius:12px;'
      + 'background:linear-gradient(135deg,#1C1C1C,#262624);border:1px solid #F08C1E;'
      + 'display:flex;align-items:center;gap:14px;cursor:pointer;transition:.15s';
    banner.onmouseover=function(){banner.style.transform='translateY(-2px)';};
    banner.onmouseout =function(){banner.style.transform='none';};
    banner.innerHTML =
      '<div style="width:42px;height:42px;border-radius:10px;background:#F08C1E;display:flex;'
      + 'align-items:center;justify-content:center;font-weight:700;color:#fff;font-size:20px;flex:none">T</div>'
      + '<div style="flex:1"><div style="font-size:14px;font-weight:600;color:#fff">'
      + 'CloseIQ — Autonomous Month-End Close <span style="font-size:10px;color:#F5A93E;'
      + 'background:rgba(240,140,30,.16);padding:2px 8px;border-radius:10px;margin-left:6px">WAVE 1 · LIVE</span></div>'
      + '<div style="font-size:12px;color:#B4B2A9;margin-top:3px">Open the full close cockpit — TB scrutiny, '
      + 'variance, intercompany recon, and the Sage assistant. Day 7 → day 3.</div></div>'
      + '<div style="color:#F5A93E;font-size:13px;font-weight:600;white-space:nowrap">Open CloseIQ &rarr;</div>';
    banner.onclick = function(){ window.parent.postMessage({__navTo:'closeiq'},'*'); };

    // Insert near the top of the tower page content
    main.insertBefore(banner, main.firstChild ? main.firstChild.nextSibling : null);
  }

  // Watch for screen changes (the app re-renders #main on navigation)
  var mo = new MutationObserver(function(){ setTimeout(addCloseIQLauncher, 60); });
  function start(){
    var main = document.getElementById('main');
    if(main){ mo.observe(main, {childList:true, subtree:false}); addCloseIQLauncher(); }
    else setTimeout(start, 300);
  }
  start();

  // Also: a voice/chat query about the close can route to CloseIQ
  window.__openCloseIQ = function(){ window.parent.postMessage({__navTo:'closeiq'},'*'); };
})();
</script>
"""
    return html.replace('</body>', inject + '</body>')


# ── 4. Build the shell ───────────────────────────────────────────────────────
def build_shell():
    shell = read(APPS / 'shell.html')
    shell = shell.replace('__EVOLUTION_SRC__', 'app-evolution.html')
    shell = shell.replace('__COMMAND_SRC__',   'app-command.html')
    shell = shell.replace('__CLOSEIQ_SRC__',   'app-closeiq.html')
    return shell


def main():
    print("Building consolidated DAMAC × Tiger platform…")
    OUT.mkdir(parents=True, exist_ok=True)

    write(OUT / 'app-closeiq.html',   build_closeiq());    print("  ✓ app-closeiq.html")
    write(OUT / 'app-evolution.html', build_evolution());  print("  ✓ app-evolution.html")
    write(OUT / 'app-command.html',   build_command());    print("  ✓ app-command.html")
    write(OUT / 'index.html',         build_shell());       print("  ✓ index.html (shell)")

    total = sum((OUT / f).stat().st_size for f in
                ['index.html','app-closeiq.html','app-evolution.html','app-command.html'])
    print(f"\n✓ Platform built — {total//1024} KB total across 4 files")
    print(f"  Built {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == '__main__':
    main()
