# -*- coding: utf-8 -*-
"""Merge bag + photo HTML experiences into one index.html."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
PADLET_URL = "https://padlet.com/ipad838015/padlet-tkseorwbkplmmust"

CHAPTERS = [
    {
        "file": "1950_busan_pirangabang_mission.html",
        "id": "chapter-bag",
        "prefix": "bag",
        "title": "피란길 기억가방",
    },
    {
        "file": "1950 부산 피란수도 부산 사진.html",
        "id": "chapter-photos",
        "prefix": "photo",
        "title": "역사 사진 카드",
    },
]

NAV_CSS = """
  .chapter { display: none; }
  .chapter.active { display: block; }
  .chapter-dots {
    position: fixed; top: 14px; left: 50%; transform: translateX(-50%);
    display: flex; gap: 10px; z-index: 100;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--brass);
    letter-spacing: 0.08em;
  }
  .chapter-dots button {
    background: none; border: none; padding: 4px 6px; margin: 0;
    font: inherit; color: inherit; letter-spacing: inherit;
    cursor: pointer; opacity: 0.35;
    transition: opacity 0.2s ease, color 0.2s ease;
  }
  .chapter-dots button:hover { opacity: 0.7; }
  .chapter-dots button.active { opacity: 1; color: var(--amber); }
  .chapter-next-btn, .chapter-ghost-btn, .chapter-padlet-btn {
    font-family: 'IBM Plex Mono', monospace; font-size: 14px; letter-spacing: 0.04em;
    background: transparent; border: 1.5px solid var(--amber); color: var(--amber);
    padding: 13px 28px; border-radius: 30px; cursor: pointer;
    transition: background 0.25s ease, color 0.25s ease;
    text-decoration: none; display: inline-block;
  }
  .chapter-next-btn:hover, .chapter-next-btn:focus-visible,
  .chapter-ghost-btn:hover, .chapter-ghost-btn:focus-visible,
  .chapter-padlet-btn:hover, .chapter-padlet-btn:focus-visible {
    background: var(--amber); color: #1A1408;
  }
  .chapter-ghost-btn {
    border-color: var(--kraft-light); color: var(--kraft-light);
  }
  .chapter-ghost-btn:hover, .chapter-ghost-btn:focus-visible {
    background: var(--kraft-light); color: #1A1408;
  }
  .chapter-padlet-btn {
    border-color: var(--oxblood); color: var(--oxblood);
  }
  .chapter-padlet-btn:hover, .chapter-padlet-btn:focus-visible {
    background: var(--oxblood); color: var(--parchment);
  }
  .bag-nav-row, .chapter-nav-row {
    display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 16px;
  }
"""


def extract_parts(filepath: Path):
    text = filepath.read_text(encoding="utf-8")
    style_m = re.search(r"<style>(.*?)</style>", text, re.DOTALL)
    body_m = re.search(r"<body>(.*?)</body>", text, re.DOTALL)
    scripts = re.findall(r"<script>(.*?)</script>", text, re.DOTALL)
    if not style_m or not body_m:
        raise ValueError(f"Could not parse {filepath}")
    body = re.sub(r"<script>.*?</script>", "", body_m.group(1), flags=re.DOTALL).strip()
    return style_m.group(1), body, scripts


def collect_ids(*contents: str) -> set[str]:
    ids: set[str] = set()
    for content in contents:
        ids.update(re.findall(r'\bid="([^"]+)"', content))
        ids.update(re.findall(r"""getElementById\(['"]([^'"]+)['"]\)""", content))
    return ids


def prefix_content(content: str, prefix: str, ids: set[str]) -> str:
    out = content
    for id_name in sorted(ids, key=len, reverse=True):
        if id_name.startswith(f"{prefix}-"):
            continue
        prefixed = f"{prefix}-{id_name}"
        out = out.replace(f'id="{id_name}"', f'id="{prefixed}"')
        out = out.replace(f"getElementById('{id_name}')", f"getElementById('{prefixed}')")
        out = out.replace(f'getElementById("{id_name}")', f'getElementById("{prefixed}")')
    return out


def scope_script(script: str, chapter_id: str) -> str:
    script = script.strip()
    if not script.startswith("(function()"):
        return script
    return script.replace(
        "(function(){",
        f"(function(){{\n  var chapterEl = document.getElementById('{chapter_id}');",
        1,
    )


def inject_bag_nav(body: str) -> str:
    body = body.replace(
        '<button class="confirm-btn" id="bag-confirmBtn" disabled>가방 속 마음 확인하기</button>',
        '<button class="confirm-btn" id="bag-confirmBtn" disabled>가방 속 마음 확인하기</button>'
        '\n    <div class="chapter-nav-row">'
        '<button type="button" class="chapter-ghost-btn" id="bag-goPhotosBtn">역사 사진 →</button>'
        "</div>",
        1,
    )
    old = '<button class="reset-btn" id="bag-resetBtn">다시 골라보기</button>'
    new = (
        '<div class="bag-nav-row">'
        '<button class="reset-btn" id="bag-resetBtn">다시 골라보기</button>'
        f'<a class="chapter-padlet-btn" id="bag-padletBtn" href="{PADLET_URL}" '
        'target="_blank" rel="noopener noreferrer">피란 가방 공유하기</a>'
        '<button type="button" class="chapter-next-btn" id="bag-nextBtn">역사 사진 →</button>'
        "</div>"
    )
    return body.replace(old, new, 1)


def inject_photo_nav(body: str) -> str:
    body = body.replace(
        "이제 활동3에서는 그 시절 사람들의 목소리를 더 가까이 들어보겠습니다.",
        "여러분이 살펴본 사진들은 1950년 부산을 살아간 사람들의 진짜 증거입니다.",
    )
    body = body.replace(
        '<div class="nav-row">\n      <button class="nav-btn ghost" id="photo-prevBtn">← 이전</button>\n'
        '      <button class="nav-btn" id="photo-nextBtn" disabled>다음 →</button>\n    </div>',
        '<div class="nav-row">\n'
        '      <button class="nav-btn ghost" id="photo-backToBagBtn">← 피란 가방</button>\n'
        '      <button class="nav-btn ghost" id="photo-prevBtn">← 이전</button>\n'
        '      <button class="nav-btn" id="photo-nextBtn" disabled>다음 →</button>\n'
        '    </div>',
        1,
    )
    old = '<button class="nav-btn ghost" id="photo-backToCardsBtn">← 카드 다시 보기</button>'
    new = (
        '<button class="nav-btn ghost" id="photo-backToBagBtn2">← 피란 가방</button>'
        '<button class="nav-btn ghost" id="photo-backToCardsBtn">← 카드 다시 보기</button>'
        '<button class="nav-btn" id="photo-restartBtn">처음부터 다시</button>'
    )
    return body.replace(old, new, 1)


def patch_bag_script(script: str) -> str:
    script = script.replace(
        "  resetBtn.addEventListener('click', function(){",
        "  var bagGoPhotosBtn = document.getElementById('bag-goPhotosBtn');\n"
        "  var bagNextBtn = document.getElementById('bag-nextBtn');\n"
        "  if(bagGoPhotosBtn){\n"
        "    bagGoPhotosBtn.addEventListener('click', function(){ window.goToChapter('chapter-photos'); });\n"
        "  }\n"
        "  if(bagNextBtn){\n"
        "    bagNextBtn.addEventListener('click', function(){ window.goToChapter('chapter-photos'); });\n"
        "  }\n\n"
        "  resetBtn.addEventListener('click', function(){",
    )
    return script


def patch_photo_script(script: str) -> str:
    script = script.replace(
        "  renderCard();\n})();",
        "  function goBackToBag(){\n"
        "    window.goToChapter('chapter-bag');\n"
        "  }\n"
        "  var backToBagBtn = document.getElementById('photo-backToBagBtn');\n"
        "  var backToBagBtn2 = document.getElementById('photo-backToBagBtn2');\n"
        "  var restartBtn = document.getElementById('photo-restartBtn');\n"
        "  if(backToBagBtn){ backToBagBtn.addEventListener('click', goBackToBag); }\n"
        "  if(backToBagBtn2){ backToBagBtn2.addEventListener('click', goBackToBag); }\n"
        "  if(restartBtn){\n"
        "    restartBtn.addEventListener('click', function(){ location.reload(); });\n"
        "  }\n\n"
        "  renderCard();\n})();",
    )
    return script


def main():
    all_styles = []
    chapter_html_parts = []
    all_scripts = []

    injectors = {"bag": inject_bag_nav, "photo": inject_photo_nav}
    patchers = {"bag": patch_bag_script, "photo": patch_photo_script}

    for i, ch in enumerate(CHAPTERS):
        path = ROOT / ch["file"]
        style, body, scripts = extract_parts(path)
        all_styles.append(f"/* --- {ch['title']} --- */\n" + style)

        ids = collect_ids(body, *scripts)
        body = prefix_content(body, ch["prefix"], ids)
        if ch["prefix"] in injectors:
            body = injectors[ch["prefix"]](body)

        ids = collect_ids(body, *scripts)
        for script in scripts:
            s = prefix_content(script, ch["prefix"], ids)
            if s.strip().startswith("(function()"):
                s = scope_script(s, ch["id"])
                if ch["prefix"] in patchers:
                    s = patchers[ch["prefix"]](s)
            all_scripts.append(s)

        active = " active" if i == 0 else ""
        chapter_html_parts.append(
            f'<section class="chapter{active}" id="{ch["id"]}" data-step="{i + 1}">\n{body}\n</section>'
        )

    dots = "".join(
        f'<button type="button" id="dot-{ch["prefix"]}" data-chapter="{ch["id"]}"'
        f'{" class=\"active\"" if i == 0 else ""}>{i + 1}. {ch["title"]}</button>'
        for i, ch in enumerate(CHAPTERS)
    )

    nav_js = """
(function(){
  var chapters = ['chapter-bag', 'chapter-photos'];
  var dots = {
    'chapter-bag': document.getElementById('dot-bag'),
    'chapter-photos': document.getElementById('dot-photo')
  };

  window.goToChapter = function(id){
    chapters.forEach(function(cid){
      var el = document.getElementById(cid);
      if(el){
        if(cid !== id){
          el.querySelectorAll('audio').forEach(function(a){ a.pause(); });
        }
        el.classList.toggle('active', cid === id);
      }
      if(dots[cid]) dots[cid].classList.toggle('active', cid === id);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  document.querySelectorAll('.chapter-dots button[data-chapter]').forEach(function(btn){
    btn.addEventListener('click', function(){
      window.goToChapter(btn.getAttribute('data-chapter'));
    });
  });
})();
"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1950년 부산 · 역사 체험</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{NAV_CSS}
{"".join(all_styles)}
</style>
</head>
<body>
<div class="chapter-dots" role="tablist" aria-label="체험 단계">{dots}</div>
{"".join(chapter_html_parts)}
<script>
{nav_js}
{"".join(all_scripts)}
</script>
</body>
</html>
"""

    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"Created {out} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
