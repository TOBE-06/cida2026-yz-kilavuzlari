"""Aşama 6 – Mevcut örneklemle uzlaştırma.

Araştırmacının önceden elle topladığı belgeleri (`data/mevcut_arsiv/`, YALNIZCA OKUNUR) yeni
taramayla karşılaştırır ve `reports/uzlastirma.csv` dosyasını yazar. Her belge üç durumdan birini alır:
  eşleşen      önceki belge taramada bilinen adresiyle bulundu
  bulunamayan  önceki belge için taramada eşleşen aday belirlenemedi (ör. tohum listesinde adres yok)
  yeni aday    taramada bulunan, ölçütleri karşıladığı araştırmacıca belirlenen, önceki örneklemde olmayan belge

Eşleşen ve siteden otomatik arşivlenen belgelerde önceki PDF'in metni ile yeni arşiv metni
karşılaştırılır (rapidfuzz, sözcük kümesi benzerliği, 0–100). Benzerlik eşiğin altındaysa
`surum_degisikligi = evet` yazılır. Fark, metin çıkarma yönteminden de kaynaklanabilir; bu sütun
bir uyarıdır, sürümün değiştiğini kesin olarak göstermez.

`data/mevcut_arsiv/` yoksa aşama atlanır. Betik ağa çıkmaz; sonunda envanterin iki uzlaştırma
sütununu günceller.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import envanter as e  # noqa: E402
from hat import form as f  # noqa: E402
from hat.ayarlar import KOK, ayarlari_yukle, eleme_olcutleri, yol  # noqa: E402
from hat.kayit import gunluk_kur  # noqa: E402
from hat.metin import pdf_metin  # noqa: E402

SUTUNLAR = ["belge_id", "kurum", "durum", "mevcut_dosya", "mevcut_dosya_tarihi", "yeni_toplama_yontemi",
            "yeni_erisim_tarihi", "benzerlik", "surum_degisikligi", "aciklama"]
AD_DESENI = re.compile(r"^([KM]\d+)_.+_(\d{4}-\d{2}-\d{2})\.pdf$")


def sade(metin: str, sinir: int) -> str:
    return re.sub(r"\s+", " ", metin).strip().lower()[:sinir]


def yeni_metin(belge_id: str, grup: str) -> str:
    """Yeni arşivdeki metni (çok parçalıysa parçaları sırayla birleştirerek) okur."""
    dosyalar = sorted((yol("arsiv") / grup).glob(f"{belge_id}*_*.txt"))
    return "\n".join(d.read_text(encoding="utf-8") for d in dosyalar if re.match(rf"{belge_id}[a-z]?_", d.name))


def eski_belgeler(envanter: pd.DataFrame, form: pd.DataFrame, ayar: dict) -> list[dict]:
    """Önceki örneklemdeki her PDF için uzlaştırma satırı üretir."""
    env = envanter.set_index("belge_id")
    adressiz = set(form[form["aday_id"].str.startswith("TOHUM-")]["mevcut_belge"])
    satirlar = []
    for pdf in sorted(yol("mevcut_arsiv").rglob("*.pdf")):
        if not (m := AD_DESENI.match(pdf.name)):
            continue
        belge_id, tarih = m.groups()
        s = {k: "" for k in SUTUNLAR} | {"belge_id": belge_id, "mevcut_dosya": str(pdf.relative_to(KOK)), "mevcut_dosya_tarihi": tarih}
        if belge_id not in env.index:
            satirlar.append(s | {"durum": "bulunamayan", "aciklama": "envanterde yok (araştırmacı bu belgeyi dahil etmedi veya arşivlenemedi)"})
            continue
        b = env.loc[belge_id]
        s |= {"kurum": b["kurum"], "yeni_toplama_yontemi": b["toplama_yontemi"], "yeni_erisim_tarihi": b["erisim_tarihi_utc"]}
        if belge_id in adressiz:
            s |= {"durum": "bulunamayan", "surum_degisikligi": "hesaplanamadı",
                  "aciklama": "tohum listesinde adres yok; taramada eşleşen aday belirlenemedi; arşivde araştırmacının önceki PDF'i kullanıldı"}
        elif "otomatik" not in b["toplama_yontemi"]:
            s |= {"durum": "eşleşen", "surum_degisikligi": "hesaplanamadı",
                  "aciklama": "bilinen adres taramada bulundu ancak otomatik erişilemedi; arşivde araştırmacının önceki PDF'i kullanıldı"}
        else:
            eski, yeni = sade(pdf_metin(pdf.read_bytes()), ayar["max_karakter"]), sade(yeni_metin(belge_id, b["grup"]), ayar["max_karakter"])
            if not eski or not yeni:
                s |= {"durum": "eşleşen", "surum_degisikligi": "hesaplanamadı", "aciklama": "metinlerden biri çıkarılamadı"}
            else:
                oran = round(fuzz.token_set_ratio(eski, yeni), 1)
                s |= {"durum": "eşleşen", "benzerlik": oran, "surum_degisikligi": "evet" if oran < ayar["benzerlik_esigi"] else "hayır",
                      "aciklama": "önceki PDF metni ile yeni arşiv metni karşılaştırıldı" + ("; çok parçalı belge" if " ; " in b["url"] else "")}
        satirlar.append(s)
    return satirlar


def yeni_adaylar(form: pd.DataFrame) -> list[dict]:
    """Önceki örneklemde olmayan, araştırmacının ölçütlere uygun bulduğu belgeleri listeler."""
    yeni = form[form["karar"].isin(["Dahil", "Ertelendi"]) & (form["mevcut_belge"] == "") & (form["birlestir"] == "")]
    bagli = form[form["birlestir"].isin(set(yeni["aday_id"]))].groupby("birlestir")["aday_id"].apply(list).to_dict()
    eski_adaylar = set(form[form["mevcut_belge"] != ""]["aday_id"])
    return [{k: "" for k in SUTUNLAR} | {
        "belge_id": s["aday_id"], "kurum": s["kurum"], "durum": "yeni aday",
        "aciklama": f"karar: {s['karar']}; adres: {s['url']}" + (f"; bağlı metinler: {', '.join(bagli[s['aday_id']])}" if s["aday_id"] in bagli else ""),
    } for s in yeni.to_dict("records") if s["aday_id"] not in eski_adaylar]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="özeti göster, dosya yazma")
    p.add_argument("--force", action="store_true", help="var olan uzlaştırma tablosunun üzerine yaz")
    p.add_argument("--sadece", default="", help="bu aşamada kullanılmaz (ana betikle uyum için)")
    args = p.parse_args()

    ayarlar = ayarlari_yukle()
    gunluk = gunluk_kur("06_uzlastir")
    cikti = yol("rapor") / ayarlar["uzlastirma"]["cikti_dosyasi"]
    if not yol("mevcut_arsiv").exists() or not any(yol("mevcut_arsiv").rglob("*.pdf")):
        gunluk.info("data/mevcut_arsiv klasörü yok veya boş; uzlaştırma aşaması atlandı.")
        return 0
    if cikti.exists() and not (args.force or args.dry_run):
        gunluk.info("Uzlaştırma tablosu zaten var; atlandı (yenilemek için --force).")
        return 0
    form = f.form_oku(yol("eleme") / ayarlar["puanlama"]["form_dosyasi"])
    tablo = pd.DataFrame(eski_belgeler(e.envanter_olustur(ayarlar), form, ayarlar["uzlastirma"]) + yeni_adaylar(form), columns=SUTUNLAR)
    gunluk.info("Uzlaştırma: %s", tablo["durum"].value_counts().to_dict())
    gunluk.info("Sürüm değişikliği: %s", tablo[tablo["durum"] != "yeni aday"]["surum_degisikligi"].value_counts().to_dict())
    for s in tablo[tablo["surum_degisikligi"] == "evet"].to_dict("records"):
        gunluk.info("  olası sürüm farkı: %s %s (benzerlik %s)", s["belge_id"], s["kurum"][:40], s["benzerlik"])
    if args.dry_run:
        gunluk.info("Deneme çalıştırması: dosya yazılmadı.")
        return 0
    cikti.parent.mkdir(parents=True, exist_ok=True)
    tablo.to_csv(cikti, index=False, encoding="utf-8")
    e.envanter_yaz(e.envanter_olustur(ayarlar), ayarlar, eleme_olcutleri())
    gunluk.info("Yazıldı: %s; envanterin uzlaştırma sütunları güncellendi.", cikti.relative_to(KOK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
