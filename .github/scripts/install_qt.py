"""Instala o Qt para MSVC direto do repositório online do Qt.

O aqtinstall 3.3.0 não entende o formato que o Qt passou a usar na 6.12
(qt6_6121/qt6_6121_msvc2022_64/Updates.xml). Este script lê os Updates.xml,
resolve as dependências e extrai os .7z com o 7z do Windows.

Uso: python install_qt.py 6.12.1 D:\\Qt modulo1 modulo2 ...
"""
import os, re, subprocess, sys, urllib.request, xml.etree.ElementTree as ET

BASE = "https://download.qt.io/online/qtsdkrepository/windows_x86"
ARCH = "win64_msvc2022_64"
SHORT = "msvc2022_64"


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
        print(f"(sem índice em {url})")
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
    pkgs.update(read_repo(f"{BASE}/desktop/qt6_{vs}/qt6_{vs}_{SHORT}"))
    for ext in ("qtwebengine", "qtpdf"):
        if "qtwebengine" in modules or ext == "qtwebengine":
            pkgs.update(read_repo(f"{BASE}/extensions/{ext}/{vs}/{ARCH}"))
    if not pkgs:
        raise SystemExit("Nenhum índice do Qt encontrado")

    def find(mod):
        pat = re.compile(rf"^(qt\.qt6\.{vs}\.(addons\.)?|extensions\.){re.escape(mod)}(\.{vs})?\.{ARCH}$")
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
            subprocess.run(["7z", "x", "-y", "-bso0", "-bsp0", f"-o{outdir}", dest], check=True)
            os.remove(dest)

    core = None
    for root, _dirs, files in os.walk(outdir):
        if "Qt6Core.dll" in files and root.endswith("bin"):
            core = os.path.dirname(root)
            break
    if not core:
        raise SystemExit("Qt6Core.dll não apareceu depois da extração")
    print("Qt instalado em", core)
    with open(os.environ.get("GITHUB_ENV", os.devnull), "a", encoding="utf-8") as env:
        env.write(f"QT_ROOT_DIR={core}\n")
    with open(os.path.join(core, "bin", "qt.conf"), "w", encoding="utf-8") as f:
        f.write("[Paths]\nPrefix=..\n")


if __name__ == "__main__":
    main()
