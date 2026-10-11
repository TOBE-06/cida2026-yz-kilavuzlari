"""Aşama 5 – Envanter ve manifest.

- `data/envanter/envanter.csv` ve `.xlsx`: araştırmacının `Dahil` dediği her belge için bir satır
  (şema: protokol §11). Sınıflama değişkenleri sayısal kodludur; anlamları Excel'deki "Kod defteri"
  sekmesinde ve `config/eleme_olcutleri.yaml` dosyasındadır.
- `reports/manifest.csv`: `archive/K` ve `archive/M` altındaki her dosyanın yolu, boyutu ve
  diskten hesaplanan SHA-256 özeti.

Bu betik ağa çıkmaz. Çıktılar her çalıştırmada girdilerden yeniden hesaplanır; var olan envanter
yalnızca `--force` ile yenilenir.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import envanter as e  # noqa: E402
from hat.ayarlar import ayarlari_yukle, eleme_olcutleri, yol  # noqa: E402
from hat.kayit import gunluk_kur  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="özeti göster, dosya yazma")
    p.add_argument("--force", action="store_true", help="var olan envanter ve manifestin üzerine yaz")
    p.add_argument("--sadece", default="", help="bu aşamada kullanılmaz (ana betikle uyum için)")
    args = p.parse_args()

    ayarlar = ayarlari_yukle()
    gunluk = gunluk_kur("05_envanter")
    hedef = yol("envanter") / "envanter.csv"
    if hedef.exists() and not (args.force or args.dry_run):
        gunluk.info("Envanter zaten var; atlandı (yenilemek için --force).")
        return 0
    envanter, manifest = e.envanter_olustur(ayarlar), e.manifest_olustur(ayarlar)
    gunluk.info("Envanter: %d belge (K: %d, M: %d). Toplama yöntemi: %s", len(envanter), int((envanter["grup"] == "K").sum()),
                int((envanter["grup"] == "M").sum()), envanter["toplama_yontemi"].value_counts().to_dict())
    for sutun in ("aktor_turu", "bolge", "belge_bicimi", "belge_statusu", "kodlama_kapsami", "sha256_pdf", "erisim_tarihi_utc"):
        bos = envanter[envanter[sutun] == ""]["belge_id"].tolist()
        if bos:
            gunluk.info("  '%s' boş olan %d belge: %s", sutun, len(bos), ", ".join(bos))
    uyumsuz = manifest[manifest["ust_veriyle_uyumlu"] == "hayır"]
    gunluk.info("Manifest: %d dosya, %.1f MB; üst veriyle uyuşmayan özet: %d", len(manifest),
                manifest["boyut_bayt"].sum() / 1e6, len(uyumsuz))
    if args.dry_run:
        gunluk.info("Deneme çalıştırması: dosya yazılmadı.")
        return 0
    csv, xlsx = e.envanter_yaz(envanter, ayarlar, eleme_olcutleri())
    yol("rapor").mkdir(parents=True, exist_ok=True)
    manifest.to_csv(yol("rapor") / "manifest.csv", index=False, encoding="utf-8")
    gunluk.info("Yazıldı: %s, %s, reports/manifest.csv", csv.name, xlsx.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
