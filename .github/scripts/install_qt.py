"""Instala o Qt para MSVC direto do repositório online do Qt.

O aqtinstall 3.3.0 não entende o formato que o Qt passou a usar na 6.12
(qt6_6121/qt6_6121_msvc2022_64/Updates.xml). Este script lê os Updates.xml,
resolve as dependências e extrai os .7z com o 7z do Windows.

Uso: python install_qt.py 6.12.1 D:\\Qt modulo1 modulo2 ...
"""
import os, re, subprocess, sys, urllib.request, xml.etree.ElementTree as ET

HOST = os.environ.get("QT_HOST", "windows_x86")          # mac_x64 no Mac
BASE = f"https://download.qt.io/online/qtsdkrepository/{HOST}"
ALL_OS = "https://download.qt.io/online/qtsdkrepository/all_os"
ARCH = os.environ.get("QT_ARCH", "win64_msvc2022_64")    # clang_64 no Mac
SHORT = os.environ.get("QT_SHORT", "msvc2022_64")        # clang_64 no Mac
SEVENZIP = os.environ.get("SEVENZIP", "7z")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "subarashi-ci"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  tentativa {attempt + 1} falhou: {url} ({e})")
    raise SystemExit(f"Não consegui baixar {url}")


def read_repo(folder: str) -> dict:
    url = f"{folder}/Updates.xml"
    try:
        root = ET.fromstring(fetch(url))
    except SystemExit:
        print(f"(sem indice em {url})")
        return {}
    pkgs = {}
    for p in root.iter("PackageUpdate"):
        name = p.findtext("Name")
        pkgs[name] = {
            "folder": folder,
            "version": p.findtext("Version"),
            "archives": [a.strip() for a in (p.findtext("DownloadableArchives") or "").split(",") if a.strip()],
            "deps": [d.strip() for d in (p.findtext("Dependencies") or "").split(",") if d.strip()],
        }
    print(f"{url}: {len(pkgs)} pacotes")
    return pkgs


def main():
    version, outdir, modules = sys.argv[1], sys.argv[2], sys.argv[3:]
    vs = version.replace(".", "")
    pkgs = {}
    # Windows: qt6_6120/qt6_6120_msvc2022_64. No Mac o nome da subpasta varia,
    # então tenta os conhecidos e depois as subpastas listadas.
    top = f"{BASE}/desktop/qt6_{vs}"
    candidates = [f"qt6_{vs}_{SHORT}", f"qt6_{vs}"]
    try:
        listing = fetch(top + "/").decode("utf-8", "replace")
        candidates += sorted(set(d for d in re.findall(r'href="([^"?/:][^"]*)/"', listing)
                                 if d.startswith(f"qt6_{vs}") and d not in candidates))
    except SystemExit:
        pass
    for cand in candidates:
        found = read_repo(f"{top}/{cand}")
        if f"qt.qt6.{vs}.{ARCH}" in found:
            pkgs.update(found)
            # módulos extras podem estar em pastas irmãs (ex.: _qt5compat)
            for extra in candidates:
                if extra != cand and extra.startswith(cand):
                    pkgs.update(read_repo(f"{top}/{extra}"))
            break
    # Desde a 6.11, o QtWebEngine fica em all_os/extensions/qtwebengine/<versão>/,
    # com subpastas (versão do Chromium, depois plataforma). Desce pela
    # listagem até achar a pasta da MSVC 64 bits.
    def subdirs(url):
        listing = fetch(url + "/").decode("utf-8", "replace")
        return sorted(set(d for d in re.findall(r'href="([^"?/:][^"]*)/"', listing)
                          if "src_doc" not in d))

    def discover(url, depth):
        for sub in subdirs(url):
            if (SHORT in sub or sub == ARCH) and "arm64" not in sub:
                pkgs.update(read_repo(f"{url}/{sub}"))
            elif depth > 0 and re.fullmatch(r"\d+", sub):
                discover(f"{url}/{sub}", depth - 1)

    if "qtwebengine" in modules:
        # Binários: <host>/extensions/qtwebengine/<versão>/... A versão do
        # WebEngine pode ser diferente da base (QT_WEBENGINE_VERSION), porque
        # o Qt publica o WebEngine com atraso em relação às versões de correção.
        wv = os.environ.get("QT_WEBENGINE_VERSION", version).replace(".", "")
        discover(f"{BASE}/extensions/qtwebengine/{wv}", 2)

    if not pkgs:
        raise SystemExit("Nenhum índice do Qt encontrado")

    def find(mod):
        wv = os.environ.get("QT_WEBENGINE_VERSION", version).replace(".", "")
        pat = re.compile(rf"^(qt\.qt6\.{vs}\.(addons\.)?|extensions\.){re.escape(mod)}(\.({vs}|{wv}))?\.{ARCH}$")
        hits = [n for n in pkgs if pat.match(n)]
        return hits

    wanted = [f"qt.qt6.{vs}.{ARCH}"]
    for mod in modules:
        hits = find(mod)
        if not hits:
            print("Pacotes disponíveis:\n  " + "\n  ".join(sorted(n for n in pkgs if ARCH in n and "debug" not in n)))
            raise SystemExit(f"Módulo não encontrado: {mod}")
        wanted += hits

    chosen, stack = [], list(wanted)
    while stack:
        n = stack.pop()
        if n in chosen or n not in pkgs:
            continue
        chosen.append(n)
        stack += [d for d in pkgs[n]["deps"] if d in pkgs and "debug" not in d]

    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, "_downloads")
    os.makedirs(tmp, exist_ok=True)
    for n in chosen:
        p = pkgs[n]
        for arc in p["archives"]:
            url = f"{p['folder']}/{n}/{p['version']}{arc}"
            dest = os.path.join(tmp, arc)
            print(f"baixando {n}: {arc}")
            with open(dest, "wb") as f:
                f.write(fetch(url))
            subprocess.run([SEVENZIP, "x", "-y", "-bso0", "-bsp0", f"-o{outdir}", dest], check=True)
            os.remove(dest)

    core = None
    for root, dirs, _files in os.walk(outdir):
        if root.endswith(os.path.join("lib", "cmake")) and "Qt6Core" in dirs:
            core = os.path.dirname(os.path.dirname(root))
            break
    if not core:
        raise SystemExit("O Qt6Core não apareceu depois da extração")
    print("Qt instalado em", core)
    with open(os.environ.get("GITHUB_ENV", os.devnull), "a", encoding="utf-8") as env:
        env.write(f"QT_ROOT_DIR={core}\n")
    with open(os.path.join(core, "bin", "qt.conf"), "w", encoding="utf-8") as f:
        f.write("[Paths]\nPrefix=..\n")


if __name__ == "__main__":
    main()
