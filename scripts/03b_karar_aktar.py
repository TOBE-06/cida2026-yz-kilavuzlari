"""Aşama 3b – Araştırmacının toplu kararını eleme formuna işler.

BU BETİK KARAR VERMEZ. Araştırmacının 9 Ekim 2026 tarihli sözlü talimatını forma yazar:
"Örneklem, elimde PDF'i bulunan ve önceden derlediğim belgelerden oluşur."

Yaptığı iş:
- Formda `mevcut_belge` değeri dolu olan (önceden derlenen belgelerle eşleşen) satırlarda
  `karar = Dahil` yazar; `grup`, `aktor_turu`, `ulke`, `bolge` alanlarını tohum listesindeki
  (araştırmacının önceki) sınıflamadan alır; `gerekce` alanına kararın kaynağını yazar.
- Yalnızca `karar` hücresi boş olan satırlara dokunur; araştırmacının elle girdiği değeri değiştirmez.
- Diğer adayların `karar` hücresine DOKUNMAZ; onlar "değerlendirilmedi" olarak kalır.
- `belge_bicimi`, `belge_statusu` ve `kodlama_kapsami` alanlarını doldurmaz (araştırmacı doldurur).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import form as f  # noqa: E402
from hat.ayarlar import ayarlari_yukle, eleme_olcutleri, yol  # noqa: E402
from hat.kayit import gunluk_kur, utc_simdi  # noqa: E402

GEREKCE = ("Araştırmacının önceden derlediği örneklemde yer alan belge ({belge_id}); araştırmacı kararıyla "
           "örneklemde tutuldu (toplu karar, {tarih}). Sınıflama tohum listesinden alındı.")
SUTUN_ACIKLAMALARI_BETIGI = "03_on_puanlama.py"


def kodlu(etiket: str, sozluk: dict) -> str:
    """Etiketi (`Ajans`) formdaki seçeneğe (`1 – Ajans`) çevirir; eşleşmezse boş döner."""
    return next((f"{kod} – {ad}" for kod, ad in sozluk.items() if ad == etiket), "")


def formu_kaydet(tablo: pd.DataFrame, form_dosyasi: Path, olcut: dict, gunluk) -> None:
    """Formu yedekleyip yeniden yazar; "Yönerge" sekmesindeki sütun açıklamalarını korur."""
    yedek = form_dosyasi.with_name(f"{form_dosyasi.stem}_yedek_{utc_simdi().replace(':', '')}.xlsx")
    shutil.copy2(form_dosyasi, yedek)
    for sutun in ("on_puan", "yz_terim_sayisi", "normatif_isaret_sayisi", "metin_uzunlugu"):
        tablo[sutun] = pd.to_numeric(tablo[sutun], errors="coerce").fillna(0).astype(int)
    yonerge = pd.read_excel(form_dosyasi, sheet_name="Yönerge", header=None, dtype=str, keep_default_na=False)
    baslangic = yonerge.index[yonerge[0] == "Sütunlar hakkında"]
    aciklamalar = [f"{a}: {b}" for a, b in yonerge.loc[baslangic[0] + 1:, [0, 1]].values] if len(baslangic) else []
    f.form_yaz(tablo, form_dosyasi, olcut, aciklamalar)
    gunluk.info("Form güncellendi (önceki hali: %s).", yedek.name)


def yeni_belgeleri_ertele(tablo: pd.DataFrame, form_dosyasi: Path, olcut: dict, args, gunluk) -> int:
    """Araştırmacının talimatı: esas örneklem önceden derlenen belgelerdir; yeni belgeler ertelenir.

    Bir satır "yeni belge"ye aitse ertelenir: `mevcut_belge` boş ve satır, önceden derlenen bir
    belgeye `birlestir` ile bağlanmamış. Önceden derlenen belgelere bağlanan ek metinlere dokunulmaz.
    Araştırmacının girdiği sınıflama ve gerekçe korunur; gerekçenin sonuna kararın kaynağı eklenir.
    """
    mevcut_adaylar = set(tablo.loc[tablo["mevcut_belge"] != "", "aday_id"])
    ana = tablo["birlestir"].where(tablo["birlestir"] != "", tablo["aday_id"])
    hedef = (tablo["karar"] == "Dahil") & (tablo["mevcut_belge"] == "") & ~ana.isin(mevcut_adaylar)
    ek = f"Araştırmacı kararıyla bu aşamadaki örnekleme alınmadı ({args.tarih})."
    tablo.loc[hedef, "karar"] = "Ertelendi"
    tablo.loc[hedef, "gerekce"] = [f"{g} | {ek}" if g else ek for g in tablo.loc[hedef, "gerekce"]]
    gunluk.info("Araştırmacının kararı işlendi: %d satır (%d belge) 'Ertelendi'. Karar dağılımı: %s",
                int(hedef.sum()), ana[hedef].nunique(), tablo["karar"].value_counts().to_dict())
    if not args.dry_run:
        formu_kaydet(tablo, form_dosyasi, olcut, gunluk)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--islem", choices=["mevcut-dahil", "yeni-ertele"], default="mevcut-dahil",
                   help="mevcut-dahil: önceden derlenen belgeleri 'Dahil' yap; yeni-ertele: önceden derlenen "
                        "örneklemde olmayan yeni belgelerin 'Dahil' kararını 'Ertelendi' yap")
    p.add_argument("--tarih", required=True, help="araştırmacının kararı verdiği tarih (YYYY-AA-GG)")
    p.add_argument("--dry-run", action="store_true", help="kaç satırın değişeceğini göster, dosya yazma")
    p.add_argument("--force", action="store_true", help="bu betikte kullanılmaz (dolu karar hücreleri hiçbir zaman değiştirilmez)")
    args = p.parse_args()

    ayarlar, olcut = ayarlari_yukle(), eleme_olcutleri()
    gunluk = gunluk_kur("03b_karar_aktar")
    form_dosyasi = yol("eleme") / ayarlar["puanlama"]["form_dosyasi"]
    tablo = f.form_oku(form_dosyasi)
    tohum = pd.read_csv(yol("seed") / ayarlar["evren"]["tohum_dosyasi"], dtype=str, keep_default_na=False).set_index("belge_id")
    esleme = ayarlar["evren"]["tohum_aktor_turu_eslemesi"]

    if args.islem == "yeni-ertele":
        return yeni_belgeleri_ertele(tablo, form_dosyasi, olcut, args, gunluk)
    hedef = (tablo["mevcut_belge"] != "") & (tablo["karar"] == "")
    for i in tablo.index[hedef]:
        s = tohum.loc[tablo.at[i, "mevcut_belge"]]
        tablo.at[i, "karar"] = "Dahil"
        tablo.at[i, "gerekce"] = GEREKCE.format(belge_id=s.name, tarih=args.tarih)
        tablo.at[i, "grup"] = s["grup"]
        tablo.at[i, "aktor_turu"] = kodlu(esleme.get(s["aktor_turu"], s["aktor_turu"]), olcut["siniflama"]["aktor_turu"])
        tablo.at[i, "ulke"] = s["ulke"]
        tablo.at[i, "bolge"] = kodlu(s["bolge"], olcut["siniflama"]["bolge"])
    gunluk.info("Araştırmacının toplu kararı işlendi: %d satır 'Dahil' (%d farklı belge). Kararı boş kalan aday: %d.",
                int(hedef.sum()), tablo.loc[hedef, "mevcut_belge"].nunique(), int((tablo["karar"] == "").sum()))
    if args.dry_run:
        gunluk.info("Deneme çalıştırması: dosya yazılmadı.")
        return 0
    yedek = form_dosyasi.with_name(f"{form_dosyasi.stem}_yedek_{utc_simdi().replace(':', '')}.xlsx")
    shutil.copy2(form_dosyasi, yedek)
    for sutun in ("on_puan", "yz_terim_sayisi", "normatif_isaret_sayisi", "metin_uzunlugu"):
        tablo[sutun] = pd.to_numeric(tablo[sutun], errors="coerce").fillna(0).astype(int)
    yonerge = pd.read_excel(form_dosyasi, sheet_name="Yönerge", header=None, dtype=str, keep_default_na=False)
    baslangic = yonerge.index[yonerge[0] == "Sütunlar hakkında"]
    aciklamalar = [f"{a}: {b}" for a, b in yonerge.loc[baslangic[0] + 1:, [0, 1]].values] if len(baslangic) else []
    f.form_yaz(tablo, form_dosyasi, olcut, aciklamalar)
    gunluk.info("Form güncellendi (önceki hali: %s).", yedek.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
