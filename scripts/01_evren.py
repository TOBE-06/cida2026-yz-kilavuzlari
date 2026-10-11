"""Aşama 1 – Evren (örnekleme çerçevesi).

Üç kaynağı birleştirip `data/interim/evren.csv` dosyasını üretir:
  1. Tohum listesi (`data/seed/kurumlar_seed.csv`, yalnızca okunur)
  2. Önceki derlemede dışlanıp yeniden değerlendirilecek aktörler (`dislanan_aktorler.csv`)
  3. Literatür, dizin ve web aramasıyla bulunan aktörler (`data/interim/evren_ek_aktorler.csv`)

Bu betik ağa çıkmaz ve arama yapmaz. Aramalar Claude Code'un web arama aracıyla yapılır,
`logs/arama_gunlugu.csv` dosyasına yazılır ve bulunan aktörler (3) numaralı dosyaya kaynağıyla
işlenir. `evrene_al` değeri `evet` olmayan satırlar evrene alınmaz; karar araştırmacınındır.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat.ayarlar import ayarlari_yukle, yol  # noqa: E402
from hat.kayit import gunluk_kur  # noqa: E402

SUTUNLAR = [
    "aktor_id", "kurum", "olasi_grup", "olasi_aktor_turu", "ulke", "bolge", "alan_adi",
    "kaynak", "eklenme_nedeni", "kaynak_turu", "alan_adi_kaynagi",
]


def csv_oku(dosya: Path) -> pd.DataFrame:
    """CSV dosyasını tüm hücreler metin, boşlar boş metin olacak biçimde okur."""
    return pd.read_csv(dosya, dtype=str, keep_default_na=False, encoding="utf-8")


def alan_adi_ekleri(ayar: dict) -> dict[str, dict[str, str]]:
    """Alan adı ek dosyasını `aktör → satır` sözlüğüne çevirir (dosya yoksa boş)."""
    dosya = yol("ara") / ayar["alan_adi_ek_dosyasi"]
    if not dosya.exists():
        return {}
    return {s["aktor"]: s for s in csv_oku(dosya).to_dict("records")}


def tohum_satirlari(ayar: dict, ekler: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """Tohum listesindeki her belgeyi bir evren satırına çevirir; eksik alan adlarını tamamlar."""
    esleme = ayar["tohum_aktor_turu_eslemesi"]
    satirlar = []
    for s in csv_oku(yol("seed") / ayar["tohum_dosyasi"]).to_dict("records"):
        ek = ekler.get(s["belge_id"])
        satirlar.append({
            "aktor_id": s["belge_id"], "kurum": s["kurum"], "olasi_grup": s["grup"],
            "olasi_aktor_turu": esleme.get(s["aktor_turu"], s["aktor_turu"]),
            "ulke": s["ulke"], "bolge": s["bolge"],
            "alan_adi": ek["alan_adi"] if ek else s["alan_adi"],
            "kaynak": f"tohum listesi ({ayar['tohum_dosyasi']})",
            "eklenme_nedeni": "Önceden derlenen örneklemde yer alıyor" + (f"; {ek['not']}" if ek else ""),
            "kaynak_turu": "tohum",
            "alan_adi_kaynagi": ek["alan_adi_kaynagi"] if ek else "tohum listesi",
        })
    return satirlar


def yeniden_degerlendirilenler(ayar: dict, ekler: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """Dışlanan aktörlerden `yeniden_degerlendir` alanı 'evet' ile başlayanları evren satırına çevirir."""
    esleme = ayar["tohum_aktor_turu_eslemesi"]
    dislanan = csv_oku(yol("seed") / ayar["dislanan_dosyasi"])
    secilen = dislanan[dislanan["yeniden_degerlendir"].str.lower().str.startswith(ayar["yeniden_degerlendir_oneki"])]
    satirlar = []
    for sira, s in enumerate(secilen.to_dict("records"), start=1):
        ek = ekler.get(s["aktor"], {})
        satirlar.append({
            "aktor_id": f"Y{sira:02d}", "kurum": s["aktor"], "olasi_grup": "",
            "olasi_aktor_turu": esleme.get(s["tur"], s["tur"]), "ulke": "", "bolge": "",
            "alan_adi": ek.get("alan_adi", ""),
            "kaynak": f"dışlanan aktörler listesi ({ayar['dislanan_dosyasi']})",
            "eklenme_nedeni": (
                f"Yeniden değerlendirilecek (önceki kod {s['dislama_kodu']}): {s['yeniden_degerlendir']}"
                + (f"; {ek['not']}" if ek.get("not") else "")
            ),
            "kaynak_turu": "yeniden değerlendirme",
            "alan_adi_kaynagi": ek.get("alan_adi_kaynagi", "bulunamadı"),
        })
    return satirlar


def ek_aktorler(ayar: dict) -> tuple[list[dict[str, str]], pd.DataFrame]:
    """Arama ve literatürle bulunan aktörleri okur; (evrene alınanlar, karar bekleyenler) döndürür."""
    dosya = yol("ara") / ayar["ek_aktor_dosyasi"]
    if not dosya.exists():
        return [], pd.DataFrame()
    tumu = csv_oku(dosya)
    alinan = tumu[tumu["evrene_al"].str.lower() == "evet"]
    satirlar = [{**s, "aktor_id": f"A{sira:03d}"} for sira, s in enumerate(alinan.to_dict("records"), start=1)]
    return satirlar, tumu[tumu["evrene_al"].str.lower() == "bekliyor"]


def evren_olustur(ayar: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Üç kaynağı birleştirir; (evren tablosu, karar bekleyen aktörler) döndürür."""
    ekler = alan_adi_ekleri(ayar)
    yeni, bekleyen = ek_aktorler(ayar)
    satirlar = tohum_satirlari(ayar, ekler) + yeniden_degerlendirilenler(ayar, ekler) + yeni
    return pd.DataFrame(satirlar)[SUTUNLAR], bekleyen


def ozet_yaz(evren: pd.DataFrame, bekleyen: pd.DataFrame, gunluk) -> None:
    """Durma noktası özeti: kaynak türüne ve olası gruba göre aktör sayıları."""
    gunluk.info("Toplam aktör: %d", len(evren))
    for tur, adet in evren["kaynak_turu"].value_counts().items():
        gunluk.info("  kaynak türü %-22s %d", tur, adet)
    for grup, adet in evren["olasi_grup"].replace("", "(belirsiz)").value_counts().items():
        gunluk.info("  olası grup %-23s %d", grup, adet)
    gunluk.info("Alan adı bulunamayan aktör: %d", int((evren["alan_adi"] == "").sum()))
    gunluk.info("Evrene alınması araştırmacı kararını bekleyen aktör: %d", len(bekleyen))
    for s in bekleyen.to_dict("records"):
        gunluk.info("  bekliyor: %s – %s", s["kurum"], s["eklenme_nedeni"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="özeti göster, dosya yazma")
    p.add_argument("--force", action="store_true", help="var olan evren.csv dosyasının üzerine yaz")
    p.add_argument("--sadece", default="", help="bu aşamada kullanılmaz (ana betikle uyum için)")
    args = p.parse_args()

    ayar = ayarlari_yukle()["evren"]
    gunluk = gunluk_kur("01_evren")
    cikti = yol("ara") / ayar["cikti_dosyasi"]
    if cikti.exists() and not args.force and not args.dry_run:
        gunluk.info("%s zaten var; atlandı (yenilemek için --force).", cikti.name)
        return 0

    evren, bekleyen = evren_olustur(ayar)
    if evren["aktor_id"].duplicated().any():
        gunluk.error("Yinelenen aktör kimliği var; dosya yazılmadı.")
        return 1
    ozet_yaz(evren, bekleyen, gunluk)
    if args.dry_run:
        gunluk.info("Deneme çalıştırması: dosya yazılmadı.")
        return 0
    cikti.parent.mkdir(parents=True, exist_ok=True)
    evren.to_csv(cikti, index=False, encoding="utf-8")
    gunluk.info("Yazıldı: %s", cikti.relative_to(cikti.parents[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
