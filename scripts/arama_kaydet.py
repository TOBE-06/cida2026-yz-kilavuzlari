"""Yapılan bir web aramasını `logs/arama_gunlugu.csv` dosyasına kaydeder.

Aramaları betikler yapmaz; Claude Code'un web arama aracı yapar. Bu betik her sorgunun
günlüğe aynı biçimde yazılmasını sağlar.

Örnek:
    python scripts/arama_kaydet.py --arac WebSearch --sorgu "site:ornek.com ai policy" \\
        --sonuc 8 --eklenen "Örnek Gazete" --not "politika sayfası bulundu"
    python scripts/arama_kaydet.py --toplu aramalar.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat.kayit import arama_yaz  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arac", default="WebSearch", help="kullanılan araç (WebSearch, WebFetch)")
    p.add_argument("--sorgu", help="arama sorgusu veya açılan adres")
    p.add_argument("--sonuc", type=int, default=0, help="dönen sonuç sayısı")
    p.add_argument("--eklenen", default="", help="bu aramayla evrene eklenen aktör(ler)")
    p.add_argument("--not", dest="not_", default="", help="kısa açıklama")
    p.add_argument("--toplu", help="her satırı bir arama olan JSONL dosyası (arac, sorgu, sonuc, eklenen, not)")
    p.add_argument("--dry-run", action="store_true", help="yazılacak satırları göster, dosyaya yazma")
    args = p.parse_args()

    if args.toplu:
        satirlar = [json.loads(s) for s in Path(args.toplu).read_text(encoding="utf-8").splitlines() if s.strip()]
    elif args.sorgu:
        satirlar = [{"arac": args.arac, "sorgu": args.sorgu, "sonuc": args.sonuc,
                     "eklenen": args.eklenen, "not": args.not_}]
    else:
        p.error("--sorgu veya --toplu gerekli")
    for s in satirlar:
        if args.dry_run:
            print(s)
        else:
            arama_yaz(s.get("arac", "WebSearch"), s["sorgu"], int(s.get("sonuc", 0)),
                      s.get("eklenen", ""), s.get("not", ""))
    print(f"{len(satirlar)} arama {'gösterildi' if args.dry_run else 'günlüğe yazıldı'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
