"""Confere se cada DLL/EXE do pacote acha, nas DLLs do Qt ao lado, todas as
funções que importa. Foi assim que apareceu o erro "Ponto de entrada não
encontrado" no Windows; esta checagem impede publicar um pacote assim.

Uso: python check_imports.py <pasta do pacote>
"""
import os, struct, sys
import pefile


def exports(path):
    pe = pefile.PE(path, fast_load=True)
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[0]
    if not d.VirtualAddress:
        return set()
    raw = pe.__data__
    off = pe.get_offset_from_rva(d.VirtualAddress)
    n = struct.unpack_from("<I", raw, off + 24)[0]
    names = pe.get_offset_from_rva(struct.unpack_from("<I", raw, off + 32)[0])
    out = set()
    for i in range(n):
        no = pe.get_offset_from_rva(struct.unpack_from("<I", raw, names + 4 * i)[0])
        out.add(raw[no:raw.find(b"\0", no)].decode("latin1"))
    return out


def main(folder):
    present = {f.lower(): f for f in os.listdir(folder)}
    cache, problems = {}, 0
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith((".dll", ".exe")):
            continue
        pe = pefile.PE(os.path.join(folder, f), fast_load=True)
        pe.parse_data_directories([pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        for imp in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            dll = imp.dll.decode()
            if dll.lower() not in present:
                continue
            if dll.lower() not in cache:
                cache[dll.lower()] = exports(os.path.join(folder, present[dll.lower()]))
            missing = [i.name.decode() for i in imp.imports
                       if i.name and i.name.decode() not in cache[dll.lower()]]
            if missing:
                problems += 1
                print(f"ERRO: {f} precisa de {len(missing)} função(ões) que {dll} não tem: {missing[:3]}")
    if problems:
        raise SystemExit(f"{problems} incompatibilidade(s) de DLL no pacote")
    print("Todas as DLLs do pacote batem entre si.")


if __name__ == "__main__":
    main(sys.argv[1])
