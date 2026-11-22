"""Rebuild the HD texture pack's index for a different stock game archive.

The pack appends its data to the end of windata\\alldata.bin and swaps in a new
windata\\alldata.psb.m. The appended data works on any stock archive whose size
is a multiple of 16; only the index is tied to one archive. This takes the
target's stock alldata.psb.m, adds the pack's entries shifted to start at the
target's stock size, and writes a matching alldata.psb.m and manifest.json.

Example (EU Steam depot 2131633):

    python rebase_index.py --pack MGSModernTextures ^
        --target-index "C:\\...\\MGS1\\windata\\alldata.psb.m" ^
        --target-size 11317041152 --psbuild C:\\FreeMote\\PsBuild.exe --out eu

  --pack         the MGSModernTextures folder from the release zip
  --target-index the STOCK alldata.psb.m of the game to target (before install)
  --target-size  the STOCK size in bytes of that game's windata\\alldata.bin
  --psbuild      PsBuild.exe from FreeMote (https://github.com/UlyssesWu/FreeMote)

Copy the two output files over MGSModernTextures\\alldata.psb.m and
MGSModernTextures\\manifest.json, then run INSTALL.bat as usual.

Nothing here reads or writes the game archive itself. Writes nothing if the
target index lacks a member the pack replaces or already has one it adds.

Needs Python 3.8+, no packages. The MDF and PSB readers below follow
m2archive.py from nuggslet/MGSM2Fix (MIT License, see LICENSES.txt).
"""
import argparse
import hashlib
import json
import random
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

INDEX_NAME = "alldata.psb.m"
KEY = "25G/xpvTbsb+6"


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- MDF

def keystream(name):
    digest = hashlib.md5((KEY + name.lower()).encode("ascii")).digest()
    engine = random.Random(int.from_bytes(digest, "little"))
    return b"".join(engine.getrandbits(32).to_bytes(4, "little") for _ in range(16))


def unmdf(blob, name):
    if blob[:4] != b"mdf\0":
        raise ValueError(f"{name}: not an MDF file")
    want = struct.unpack_from("<I", blob, 4)[0]
    key = keystream(name)
    out = zlib.decompress(bytes(b ^ key[i % 64] for i, b in enumerate(blob[8:])))
    if len(out) != want:
        raise ValueError(f"{name}: size mismatch after inflate")
    return out


def mdf(data, name):
    key = keystream(name)
    body = zlib.compress(data, 9)
    packed = b"mdf\0" + struct.pack("<I", len(data)) + bytes(b ^ key[i % 64] for i, b in enumerate(body))
    if unmdf(packed, name) != data:
        raise ValueError("MDF round trip failed")
    return packed


# ---------------------------------------------------------------- PSB (read only)

def _array(d, p):
    n = d[p] - 12
    p += 1
    count = int.from_bytes(d[p:p + n], "little")
    p += n
    m = d[p] - 12
    p += 1
    return [int.from_bytes(d[p + m * i:p + m * i + m], "little") for i in range(count)], p + m * count


class Psb:
    def __init__(self, data):
        if data[:4] != b"PSB\0":
            raise ValueError("not a PSB file")
        self.d = data
        head = struct.unpack_from("<8I", data, 8)
        self.off_strings, self.off_strdata, self.off_entries = head[2], head[3], head[7]
        p = head[1]
        self.n_offsets, p = _array(data, p)
        self.n_tree, p = _array(data, p)
        self.n_start, p = _array(data, p)
        self.s_offsets, _ = _array(data, self.off_strings)

    def name(self, index):
        node = self.n_tree[self.n_start[index]]
        out = bytearray()
        while node:
            parent = self.n_tree[node]
            out.append(node - self.n_offsets[parent])
            node = parent
        return bytes(reversed(out)).decode("utf-8", "replace")

    def string(self, index):
        at = self.off_strdata + self.s_offsets[index]
        return self.d[at:self.d.index(b"\0", at)].decode("utf-8", "replace")

    def value(self, p):
        d, t = self.d, self.d[p]
        p += 1
        if t <= 1:
            return None, p
        if t in (2, 3):
            return t == 3, p
        if 4 <= t <= 12:
            n = t - 4
            return int.from_bytes(d[p:p + n], "little"), p + n
        if 13 <= t <= 20:
            return _array(d, p - 1)
        if 21 <= t <= 24:
            n = t - 20
            return self.string(int.from_bytes(d[p:p + n], "little")), p + n
        if t == 29:
            return 0.0, p
        if t == 30:
            return struct.unpack_from("<f", d, p)[0], p + 4
        if t == 31:
            return struct.unpack_from("<d", d, p)[0], p + 8
        if t == 32:
            offsets, q = _array(d, p)
            return [self.value(q + o)[0] for o in offsets], q
        if t == 33:
            names, q = _array(d, p)
            offsets, q = _array(d, q)
            return {self.name(n): self.value(q + o)[0] for n, o in zip(names, offsets)}, q
        raise ValueError(f"unsupported PSB type {t}")

    def root(self):
        return self.value(self.off_entries)[0]


def read_index(path):
    raw = Path(path).read_bytes()
    return raw, Psb(unmdf(raw, INDEX_NAME)).root()


def compile_index(data, psbuild):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "index.json"
        src.write_text(json.dumps(data, ensure_ascii=True, separators=(",", ":")))
        done = subprocess.run([str(psbuild), "-ns", str(src)], cwd=tmp, capture_output=True, text=True, timeout=600)
        built = Path(tmp) / "index.psb"
        if done.returncode != 0 or not built.is_file():
            raise RuntimeError("PsBuild failed:\n" + done.stdout + done.stderr)
        out = built.read_bytes()
    if Psb(out).root() != data:
        raise RuntimeError("compiled index does not read back as the input")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--target-index", required=True)
    ap.add_argument("--target-size", required=True, type=int)
    ap.add_argument("--psbuild", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pack, out = Path(a.pack), Path(a.out)
    if out.exists():
        sys.exit(f"{out} already exists")

    manifest = json.loads((pack / "manifest.json").read_text())
    pack_raw, pack_idx = read_index(pack / INDEX_NAME)
    if sha(pack_raw) != manifest["installed_index_sha256"]:
        sys.exit("pack index does not match its manifest; download the release again")
    target_raw, target = read_index(a.target_index)
    if sha(target_raw) == manifest["installed_index_sha256"]:
        sys.exit("target index already has the pack installed; give the stock index")
    if a.target_size % 16:
        sys.exit(f"target size {a.target_size} is not a multiple of 16")

    base = manifest["stock_size"]
    pf, tf = pack_idx["file_info"], target["file_info"]
    delta = {n: v for n, v in pf.items() if v[0] >= base}
    added = [n for n in delta if n not in tf]
    replaced = [n for n in delta if n in tf]
    report = {
        "target_index_sha256": sha(target_raw), "target_size": a.target_size,
        "target_entries": len(tf), "pack_entries": len(delta),
        "added": len(added), "replaced": replaced,
        "target_max_end": max(o + s for o, s in tf.values()),
    }
    print(json.dumps(report, indent=1))
    if set(target) != set(pack_idx) or any(target[k] != pack_idx[k] for k in target if k != "file_info"):
        sys.exit("target index layout differs from the pack's")
    if report["target_max_end"] > a.target_size:
        sys.exit("target index points past --target-size; is that the stock size?")
    # The pack replaces exactly one stock member (the texture catalog); anything else
    # already present means the target is not stock or is laid out differently.
    if len(replaced) != 1 or not replaced[0].endswith("config/title_texdata.psb.m"):
        sys.exit(f"unexpected overlap with the target index: {replaced[:10]}")

    shift = a.target_size - base
    result = dict(target)
    result["file_info"] = dict(tf)
    for n, (o, s) in delta.items():
        result["file_info"][n] = [o + shift, s]
    installed_size = a.target_size + manifest["append_size"]
    if max(o + s for o, s in result["file_info"].values()) > installed_size:
        sys.exit("rebased entries run past the appended data")

    packed = mdf(compile_index(result, a.psbuild), INDEX_NAME)
    out.mkdir(parents=True)
    (out / INDEX_NAME).write_bytes(packed)
    new = dict(manifest)
    new.update(stock_size=a.target_size, stock_index_sha256=sha(target_raw),
               installed_size=installed_size, installed_index_sha256=sha(packed))
    (out / "manifest.json").write_text(json.dumps(new, indent=4))
    print(json.dumps({"out": str(out), "index_sha256": sha(packed),
                      "identical_to_pack_index": packed == pack_raw}, indent=1))


if __name__ == "__main__":
    main()
