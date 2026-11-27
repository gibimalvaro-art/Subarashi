"""Aplica a marca Subarashi no app de iPhone do Jami (jami-client-ios).

Roda na raiz de um clone do jami-client-ios, no robô de compilação do GitHub
(.github/workflows/ios.yml). Só mexe no que a pessoa vê (nome, textos, ícone,
cores) e nos identificadores do app; a rede continua sendo a do Jami.

Uso: python3 rebrand_ios.py <pasta do jami-client-ios> <pasta ios/ do Subarashi>
"""
import json
import pathlib
import re
import shutil
import sys

NEW = "Subarashi"
BUNDLE_ID = "io.github.gibimalvaro-art.subarashi"
WORD = re.compile(r"\bJami\b")


def safe(text):
    # URLs, domínios e identificadores ficam como estão
    return not re.search(r"://|jami\.net|savoirfairelinux|\.jac\b", text)


def rebrand_strings(path):
    """Troca 'Jami' só nos valores ("chave" = "valor";), nunca nas chaves."""
    raw = path.read_bytes()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    text = raw.decode(enc)
    line = re.compile(r'^(\s*"(?:[^"\\]|\\.)*"\s*=\s*")((?:[^"\\]|\\.)*)(";.*)$', re.M)

    def fix(m):
        value = m.group(2)
        # Doações e créditos continuam apontando para o projeto Jami
        if re.search(r"support|donat|contribut|credit|about", m.group(1), re.I) and "Jami" in value \
                and re.search(r"project|projeto|donat|doa|support|apoi", value, re.I):
            return m.group(0)
        if not safe(value):
            return m.group(0)
        return m.group(1) + WORD.sub(NEW, value) + m.group(3)

    new = line.sub(fix, text)
    if new != text:
        path.write_bytes(new.encode("utf-8" if enc == "utf-8-sig" else enc))
        return 1
    return 0


def main(repo, assets):
    repo, assets = pathlib.Path(repo), pathlib.Path(assets)
    app = repo / "Ring" / "Ring"
    changed = 0

    # 1. Nome na tela inicial e textos de permissão
    plist = app / "Info.plist"
    s = plist.read_text(encoding="utf-8")
    s = s.replace("<key>CFBundleDisplayName</key>\n\t<string>Jami</string>",
                  f"<key>CFBundleDisplayName</key>\n\t<string>{NEW}</string>")
    s = re.sub(r"(<string>)([^<]*)(</string>)",
               lambda m: m.group(1) + (WORD.sub(NEW, m.group(2)) if safe(m.group(2)) else m.group(2)) + m.group(3), s)
    assert f"<string>{NEW}</string>" in s, "CFBundleDisplayName não trocado"
    plist.write_text(s, encoding="utf-8")

    # 2. Textos traduzidos (todas as línguas)
    for f in (app / "Resources").rglob("*.strings"):
        changed += rebrand_strings(f)
    for f in (app / "Resources").rglob("*.stringsdict"):
        t = f.read_text(encoding="utf-8")
        n = re.sub(r"(<string>)([^<]*)(</string>)",
                   lambda m: m.group(1) + (WORD.sub(NEW, m.group(2)) if safe(m.group(2)) else m.group(2)) + m.group(3), t)
        if n != t:
            f.write_text(n, encoding="utf-8")
            changed += 1
    print("arquivos de texto alterados:", changed)

    # 3. Identificador do app (o instalador gratuito troca de novo, se precisar)
    pbx = repo / "Ring" / "Ring.xcodeproj" / "project.pbxproj"
    s = pbx.read_text(encoding="utf-8")
    s = s.replace("PRODUCT_BUNDLE_IDENTIFIER = com.savoirfairelinux.ring;",
                  f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE_ID};")
    s = s.replace("PRODUCT_BUNDLE_IDENTIFIER = com.savoirfairelinux.ring.",
                  f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE_ID}.")
    s = s.replace("DEVELOPMENT_TEAM = MSHYCBXK85;", 'DEVELOPMENT_TEAM = "";')
    pbx.write_text(s, encoding="utf-8")

    # 4. Ícone: os dois formatos que o projeto tem
    iconset = app / "Resources" / "Images.xcassets" / "AppIcon.appiconset"
    for png in iconset.glob("*.png"):
        shutil.copyfile(assets / "icons" / png.name, png)
    icon = app / "Resources" / "AppIcon.icon"
    if icon.exists():
        shutil.copyfile(assets / "icons" / "icon-1024.png", icon / "Assets" / "icon1.png")
        meta = json.loads((icon / "icon.json").read_text(encoding="utf-8"))
        for group in meta.get("groups", []):
            for layer in group.get("layers", []):
                layer["position"] = {"scale": 1.0, "translation-in-points": [0, 0]}
                layer["glass-specializations"] = [{"value": False}, {"appearance": "dark", "value": False}]
        (icon / "icon.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # 5. Cores da marca: azul do Jami -> verde-floresta
    colors = app / "Resources" / "Colors.xcassets"
    swaps = {
        "jami.colorset": [('"blue" : "0x5F"', '"blue" : "0x38"'), ('"green" : "0x34"', '"green" : "0x4D"'), ('"red" : "0x00"', '"red" : "0x07"'),
                          ('"blue" : "0.769"', '"blue" : "0.627"'), ('"green" : "0.612"', '"green" : "0.769"'), ('"red" : "0.012"', '"red" : "0.180"')],
        "jamiButtonPrimary.colorset": [('"blue" : "0x99"', '"blue" : "0x4F"'), ('"green" : "0x55"', '"green" : "0x6E"'), ('"red" : "0x00"', '"red" : "0x0B"'),
                                       ('"blue" : "0xCF"', '"blue" : "0x7A"'), ('"green" : "0x7B"', '"green" : "0xA6"')],
    }
    for name, pairs in swaps.items():
        f = colors / name / "Contents.json"
        t = f.read_text(encoding="utf-8")
        for a, b in pairs:
            t = t.replace(a, b)
        f.write_text(t, encoding="utf-8")
    # o vermelho escuro do botão no modo escuro era 0x00: depois das trocas acima
    # ele já virou 0x07 no jami.colorset; no botão, garantir o tom do modo escuro
    f = colors / "jamiButtonPrimary.colorset" / "Contents.json"
    t = f.read_text(encoding="utf-8")
    f.write_text(t.replace('"red" : "0x00"', '"red" : "0x21"'), encoding="utf-8")

    print("Marca Subarashi aplicada.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
