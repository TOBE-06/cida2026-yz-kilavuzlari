"""Veri toplama hattının aşamalarını çalıştırır.

Örnek:
    python scripts/run_pipeline.py --asama 1
    python scripts/run_pipeline.py --asama 2 --dry-run
    python scripts/run_pipeline.py --asama 4 --sadece K01,M03 --force
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

ASAMALAR: dict[int, tuple[str, str]] = {
    1: ("01_evren.py", "Evren: aktör listesi (örnekleme çerçevesi)"),
    2: ("02_kesif.py", "Keşif: aday URL'lerin bulunması"),
    3: ("03_on_puanlama.py", "Ön puanlama ve eleme formu"),
    4: ("04_arsivle.py", "Arşivleme (yalnızca araştırmacının 'Dahil' dedikleri)"),
    5: ("05_envanter.py", "Envanter ve manifest"),
    6: ("06_uzlastir.py", "Mevcut örneklemle uzlaştırma"),
    7: ("07_rapor.py", "Rapor ve akış şeması"),
}


def arguman_ayristirici() -> argparse.ArgumentParser:
    aciklama = "CIDA 2026 YZ kılavuzları veri toplama hattı. Aşamalar:\n" + "\n".join(
        f"  {no}  {ad}" for no, (_, ad) in ASAMALAR.items()
    )
    p = argparse.ArgumentParser(description=aciklama, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--asama", type=int, choices=sorted(ASAMALAR), required=True, help="çalıştırılacak aşama (1–7)")
    p.add_argument("--dry-run", action="store_true", help="ne yapılacağını göster; dosya yazma, ağa çıkma")
    p.add_argument("--force", action="store_true", help="var olan çıktıyı yeniden üret")
    p.add_argument("--sadece", default="", help="yalnızca bu kimlikler (virgülle): K01,M03")
    p.add_argument("--test-atla", action="store_true", help="aşamadan önce pytest çalıştırma")
    return p


def testleri_calistir() -> bool:
    """Aşamadan önce testleri çalıştırır; hepsi geçerse True döner."""
    return subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=KOK).returncode == 0


def main() -> int:
    args = arguman_ayristirici().parse_args()
    betik_adi, baslik = ASAMALAR[args.asama]
    betik = KOK / "scripts" / betik_adi
    if not betik.exists():
        print(f"Aşama {args.asama} betiği henüz yazılmadı: scripts/{betik_adi}")
        return 2
    if not args.test_atla and not testleri_calistir():
        print("Testler başarısız; aşama çalıştırılmadı.")
        return 1
    komut = [sys.executable, str(betik)]
    komut += ["--dry-run"] if args.dry_run else []
    komut += ["--force"] if args.force else []
    komut += ["--sadece", args.sadece] if args.sadece else []
    print(f"== Aşama {args.asama}: {baslik} ==")
    return subprocess.run(komut, cwd=KOK).returncode


if __name__ == "__main__":
    sys.exit(main())
