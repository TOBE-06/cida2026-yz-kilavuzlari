"""Aşama 3 – Ön puanlama ve eleme formu.

1. Her adayın sayfasını (etik kurallarla) indirir, ana metnini çıkarır ve şunları hesaplar:
   dil, YZ terimi sayısı, normatif işaret sayısı, metin uzunluğu, ön puan.
2. Aynı adrese yönlenen adayları birleştirir.
3. Araştırmacıya yardımcı işaretler ekler (ör. "metinde YZ terimi yok", "aynı kurumdan 5 aday").
4. `data/interim/adaylar_puanli.csv` ve `data/eleme/eleme_formu.xlsx` dosyalarını yazar.

ÖN PUAN KARAR DEĞİLDİR; yalnızca formdaki sıralamayı belirler. Betik `karar` ve `dislama_kodu`
sütunlarını her zaman boş bırakır ve hiçbir adayı dahil etmez veya dışlamaz.

Form zaten varsa yeniden üretilmez. `--force` verilirse önce tarihli bir yedeği alınır ve
araştırmacının daha önce girdiği değerler `aday_id` üzerinden yeni forma taşınır.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import form as f  # noqa: E402
from hat import puanlama as p  # noqa: E402
from hat.ag import TAMAM, Istemci, alan_adi, url_normallestir  # noqa: E402
from hat.ayarlar import ayarlari_yukle, eleme_olcutleri, yol  # noqa: E402
from hat.kayit import gunluk_kur, hata_yaz, utc_simdi  # noqa: E402

ASAMA = "03_on_puanlama"
PUAN_SUTUNLARI = [
    "aday_id", "kurum", "alan_adi", "url", "baslik", "bulunma_yolu", "eslesen_terimler", "bulunma_zamani_utc",
    "dil", "yz_terim_sayisi", "normatif_isaret_sayisi", "metin_uzunlugu", "on_puan", "erisim_durumu",
    "aktor_id", "son_url", "http_durumu", "erisim_aciklamasi", "erisim_zamani_utc", "metin_ozeti",
    "wayback_url", "mevcut_belge", "birlesen_adaylar", "isaretler",
]
YOL_ONCELIGI = {"tohum": 0, "arama": 1, "gezinme": 2, "sitemap": 3, "etik_kod": 4}
SUTUN_ACIKLAMALARI = [
    "on_puan: Yalnızca sıralama içindir (0–100); karar değildir. YZ terimi ve normatif işaret sayısından hesaplanır.",
    "isaretler: Betiğin gözlemleri. Dışlama kodu önermez; yalnızca dikkat edilecek noktaları gösterir.",
    "mevcut_belge: Adayın adresi önceden derlenen 47 belgeden biriyle aynıysa o belgenin kimliği.",
    "bulunma_yolu: tohum (bilinen adres), sitemap (site haritası), gezinme, arama, etik_kod (M grubunda genel etik kod sayfası).",
    "sarı sütunlar: Araştırmacı doldurur. ulke ve bolge evren listesinden öneri olarak gelir; değiştirilebilir.",
    "birlestir: Aynı kurumun tek belge sayılacak ikinci metni için, ana adayın aday_id değeri yazılır.",
]


def csv_oku(dosya: Path) -> pd.DataFrame:
    return pd.read_csv(dosya, dtype=str, keep_default_na=False, encoding="utf-8") if dosya.exists() else pd.DataFrame()


def adayi_puanla(aday: dict[str, str], istemci: Istemci, ayarlar: dict[str, Any], metin_klasoru: Path) -> dict[str, Any]:
    """Tek bir adayı indirir ve ölçümlerini hesaplar. Erişilemeyenlerde Wayback kopyasına bakar."""
    ayar = ayarlar["puanlama"]
    yanit = istemci.getir(aday["url"])
    sonuc: dict[str, Any] = dict(aday) | {
        "erisim_durumu": yanit.erisim_durumu, "son_url": yanit.son_url, "http_durumu": yanit.durum_kodu or "",
        "erisim_aciklamasi": yanit.aciklama, "erisim_zamani_utc": yanit.zaman_utc, "wayback_url": "",
        "dil": "", "yz_terim_sayisi": 0, "normatif_isaret_sayisi": 0, "metin_uzunlugu": 0, "on_puan": 0, "metin_ozeti": "",
    }
    if yanit.erisim_durumu != TAMAM:
        if ayarlar["arsiv"]["wayback_kontrol"]:
            sonuc["wayback_url"] = p.wayback_kopyasi(istemci, aday["url"], ayar["wayback_api"])
        return sonuc
    baslik, metin = p.metin_cikar(yanit)
    sonuc["baslik"] = baslik or aday["baslik"]
    sonuc.update(p.metin_olcumleri(yanit.son_url, sonuc["baslik"], metin, "" if yanit.pdf_mi else yanit.metin, ayar))
    (metin_klasoru / f"{aday['aday_id']}.txt").write_text(metin, encoding="utf-8")
    return sonuc


def alan_grubunu_puanla(adaylar: list[dict], istemci: Istemci, ayarlar: dict, metin_klasoru: Path) -> list[dict]:
    """Aynı alan adındaki adayları sırayla puanlar (alan başı bekleme kuralı böyle korunur)."""
    sonuclar = []
    for aday in adaylar:
        try:
            sonuclar.append(adayi_puanla(aday, istemci, ayarlar, metin_klasoru))
        except Exception as hata:  # tek adaydaki hata diğerlerini durdurmasın
            hata_yaz(ASAMA, aday["url"], type(hata).__name__, str(hata))
            sonuclar.append(dict(aday) | {"erisim_durumu": "hata", "erisim_aciklamasi": f"{type(hata).__name__}: {hata}",
                                          "erisim_zamani_utc": utc_simdi()})
    return sonuclar


def puanla(adaylar: pd.DataFrame, mevcut: pd.DataFrame, ayarlar: dict, gunluk, zorla: bool) -> pd.DataFrame:
    """Henüz puanlanmamış adayları (veya `zorla` ise hepsini) puanlar; tüm puanlı tabloyu döndürür."""
    metin_klasoru = yol("ara") / ayarlar["puanlama"]["metin_klasoru"]
    metin_klasoru.mkdir(parents=True, exist_ok=True)
    yapilmis = set() if zorla or mevcut.empty else set(mevcut["aday_id"])
    sirada = [a for a in adaylar.to_dict("records") if a["aday_id"] not in yapilmis]
    gunluk.info("%d aday; %d puanlanacak, %d atlanıyor (zaten puanlanmış).", len(adaylar), len(sirada), len(adaylar) - len(sirada))
    gruplar: dict[str, list[dict]] = {}
    for a in sirada:
        gruplar.setdefault(alan_adi(a["url"]), []).append(a)
    istemci = Istemci(ayarlar["ag"])
    yeni: list[dict] = []
    with ThreadPoolExecutor(max_workers=int(ayarlar["puanlama"]["es_zamanli_alan"])) as havuz:
        isler = {havuz.submit(alan_grubunu_puanla, g, istemci, ayarlar, metin_klasoru): alan for alan, g in gruplar.items()}
        for is_ in as_completed(isler):
            yeni.extend(is_.result())
            gunluk.info("%s: %d aday puanlandı", isler[is_], len(is_.result()))
    eski = [] if zorla or mevcut.empty else mevcut[mevcut["aday_id"].isin(set(adaylar["aday_id"]))].to_dict("records")
    return pd.DataFrame(eski + yeni).reindex(columns=PUAN_SUTUNLARI).fillna("").astype(str)


def yonlenenleri_birlestir(tablo: pd.DataFrame, gunluk) -> pd.DataFrame:
    """Yönlendirme sonrası aynı adrese varan adayları tek satırda birleştirir (öncelikli bulunma yolu kalır)."""
    tablo = tablo.copy()
    tablo["_anahtar"] = [url_normallestir(s or u) for s, u in zip(tablo["son_url"], tablo["url"])]
    tablo["_oncelik"] = tablo["bulunma_yolu"].map(YOL_ONCELIGI)
    tablo = tablo.sort_values(["_oncelik", "aday_id"])
    kalanlar = []
    for _, grup in tablo.groupby(["aktor_id", "_anahtar"], sort=False):
        ilk = grup.iloc[0].to_dict()
        onceki = [x for x in ilk["birlesen_adaylar"].split(", ") if x]
        ilk["birlesen_adaylar"] = ", ".join(dict.fromkeys(onceki + list(grup["aday_id"].iloc[1:])))
        kalanlar.append(ilk)
    gunluk.info("Aynı adrese yönlenen %d aday birleştirildi.", len(tablo) - len(kalanlar))
    return pd.DataFrame(kalanlar).drop(columns=["_anahtar", "_oncelik"])


def isaretleri_ekle(tablo: pd.DataFrame, ayarlar: dict) -> pd.DataFrame:
    """Mevcut 47 belge eşleşmesini ve yardımcı işaretleri hesaplar."""
    tohum = csv_oku(yol("seed") / ayarlar["evren"]["tohum_dosyasi"])
    tohum_adresleri = {url_normallestir(u.strip()): s["belge_id"]
                       for s in tohum.to_dict("records") for u in s["bilinen_url"].split(";") if u.strip()}
    evren = csv_oku(yol("ara") / ayarlar["evren"]["cikti_dosyasi"])
    yeniden = set(evren[evren["kaynak_turu"] == "yeniden değerlendirme"]["aktor_id"])
    metin_klasoru = yol("ara") / ayarlar["puanlama"]["metin_klasoru"]
    ayar = ayarlar["puanlama"]

    tablo = tablo.copy()
    tablo["mevcut_belge"] = [
        tohum_adresleri.get(url_normallestir(u)) or tohum_adresleri.get(url_normallestir(s or u)) or ""
        for u, s in zip(tablo["url"], tablo["son_url"])
    ]
    benzerler: dict[str, list[str]] = {}
    for _, grup in tablo.groupby("aktor_id"):
        metinler = {k: (metin_klasoru / f"{k}.txt").read_text(encoding="utf-8")
                    for k in grup["aday_id"] if (metin_klasoru / f"{k}.txt").exists()}
        benzerler.update(p.benzer_adaylar(metinler, ayar["benzerlik_esigi"], ayar["benzerlik_max_karakter"]))
    sayilar = tablo.groupby("aktor_id")["aday_id"].transform("size")
    tablo["isaretler"] = [
        p.isaretler(s, int(n), benzerler.get(s["aday_id"], []), s["aktor_id"] in yeniden, ayarlar["arsiv"]["min_metin_uzunlugu"])
        for s, n in zip(tablo.to_dict("records"), sayilar)
    ]
    return tablo


def adressiz_tohumlari_ekle(puanli: pd.DataFrame, ayarlar: dict) -> pd.DataFrame:
    """Tohum listesinde olup hiçbir adayla eşleşmeyen belgeleri (adresi bilinmeyenler) forma satır olarak ekler.

    Böylece önceden derlenen her belge için de karar formda verilebilir. Bu satırların adresi yoktur.
    """
    tohum = csv_oku(yol("seed") / ayarlar["evren"]["tohum_dosyasi"])
    eksik = tohum[~tohum["belge_id"].isin(set(puanli["mevcut_belge"]))]
    satirlar = [{s: "" for s in PUAN_SUTUNLARI} | {
        "aday_id": f"TOHUM-{s['belge_id']}", "kurum": s["kurum"], "alan_adi": s["alan_adi"], "baslik": s["not"],
        "bulunma_yolu": "tohum", "erisim_durumu": "adres_yok", "aktor_id": s["belge_id"], "mevcut_belge": s["belge_id"],
        "on_puan": "0", "yz_terim_sayisi": "0", "normatif_isaret_sayisi": "0", "metin_uzunlugu": "0",
        "isaretler": f"mevcut 47 belgeden biri: {s['belge_id']}; tohum listesinde adresi yok, taramada eşleşen aday bulunamadı",
    } for s in eksik.to_dict("records")]
    return pd.concat([puanli, pd.DataFrame(satirlar, columns=PUAN_SUTUNLARI)], ignore_index=True)


def form_tablosu(puanli: pd.DataFrame, ayarlar: dict, olcut: dict, onceki: dict[str, dict]) -> pd.DataFrame:
    """Puanlı adayları forma dönüştürür: evrenden ülke/bölge önerisi ekler, önceki girişleri taşır."""
    evren = csv_oku(yol("ara") / ayarlar["evren"]["cikti_dosyasi"]).set_index("aktor_id")
    tablo = puanli.copy()
    tablo["olasi_grup"] = tablo["aktor_id"].map(evren["olasi_grup"]).fillna("")
    for sutun in f.ARASTIRMACI_SUTUNLARI:
        tablo[sutun] = ""
    tablo["ulke"] = tablo["aktor_id"].map(evren["ulke"]).fillna("")
    tablo["bolge"] = [f.bolge_secenegi(b, olcut) for b in tablo["aktor_id"].map(evren["bolge"]).fillna("")]
    for i, aday_id in zip(tablo.index, tablo["aday_id"]):
        for sutun, deger in onceki.get(aday_id, {}).items():
            if deger != "":
                tablo.at[i, sutun] = deger
    for sutun in ("on_puan", "yz_terim_sayisi", "normatif_isaret_sayisi", "metin_uzunlugu"):
        tablo[sutun] = pd.to_numeric(tablo[sutun], errors="coerce").fillna(0).astype(int)
    esik = ayarlar["puanlama"].get("kismi_eleme_esigi")
    if esik is None:
        return tablo.sort_values(["on_puan", "kurum"], ascending=[False, True])
    # Kısmi eleme: karar bekleyen ve ön puanı eşiğin üstündeki adaylar en üstte, kuruma göre gruplu
    tablo["_sira"] = [0 if k == "" and puan >= esik else (1 if k != "" else 2) for k, puan in zip(tablo["karar"], tablo["on_puan"])]
    return tablo.sort_values(["_sira", "kurum", "on_puan"], ascending=[True, True, False]).drop(columns="_sira")


def ozet_yaz(puanli: pd.DataFrame, gunluk) -> None:
    gunluk.info("Puanlı aday: %d", len(puanli))
    for durum, adet in puanli["erisim_durumu"].value_counts().items():
        gunluk.info("  erişim %-12s %d", durum, adet)
    tamam = puanli[puanli["erisim_durumu"] == TAMAM]
    gunluk.info("  metninde YZ terimi olan: %d / %d", int((tamam["yz_terim_sayisi"].astype(int) > 0).sum()), len(tamam))
    gunluk.info("  mevcut 47 belgeyle eşleşen aday: %d", int((puanli["mevcut_belge"] != "").sum()))


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--dry-run", action="store_true", help="ne yapılacağını göster; ağa çıkma, dosya yazma")
    a.add_argument("--force", action="store_true", help="tüm adayları yeniden puanla ve formu (yedek alarak) yeniden üret")
    a.add_argument("--sadece", default="", help="yalnızca bu aktör kimliklerinin adaylarını puanla (form tüm adaylarla üretilir)")
    a.add_argument("--yalniz-form", action="store_true", help="ağa çıkmadan, var olan puanlardan formu yeniden üret (yedek alarak)")
    args = a.parse_args()

    ayarlar, olcut = ayarlari_yukle(), eleme_olcutleri()
    gunluk = gunluk_kur(ASAMA)
    puan_dosyasi = yol("ara") / ayarlar["puanlama"]["cikti_dosyasi"]
    form_dosyasi = yol("eleme") / ayarlar["puanlama"]["form_dosyasi"]
    adaylar = csv_oku(yol("ara") / ayarlar["kesif"]["cikti_dosyasi"])
    mevcut = csv_oku(puan_dosyasi)
    sadece = {s.strip() for s in args.sadece.split(",") if s.strip()}

    if args.dry_run:
        yapilmis = set() if mevcut.empty or args.force else set(mevcut["aday_id"])
        gunluk.info("%d aday; %d puanlanacak. Form %s.", len(adaylar), int((~adaylar["aday_id"].isin(yapilmis)).sum()),
                    "var (korunur; --force ile yedeklenip yenilenir)" if form_dosyasi.exists() else "yok (oluşturulacak)")
        gunluk.info("Deneme çalıştırması: ağa çıkılmadı, dosya yazılmadı.")
        return 0

    if args.yalniz_form:
        puanli = adressiz_tohumlari_ekle(mevcut[~mevcut["aday_id"].str.startswith("TOHUM-")], ayarlar)
        puanli.sort_values("aday_id").to_csv(puan_dosyasi, index=False, encoding="utf-8")
    else:
        mevcut = mevcut if mevcut.empty else mevcut[~mevcut["aday_id"].str.startswith("TOHUM-")]
        hedef = adaylar[adaylar["aktor_id"].isin(sadece)] if sadece else adaylar
        puanli = puanla(hedef, mevcut, ayarlar, gunluk, args.force)
        if sadece and not mevcut.empty:
            puanli = pd.concat([mevcut[~mevcut["aktor_id"].isin(sadece)], puanli], ignore_index=True)
        puanli = isaretleri_ekle(yonlenenleri_birlestir(puanli, gunluk), ayarlar)[PUAN_SUTUNLARI]
        puanli = adressiz_tohumlari_ekle(puanli, ayarlar)
        puan_dosyasi.parent.mkdir(parents=True, exist_ok=True)
        puanli.sort_values("aday_id").to_csv(puan_dosyasi, index=False, encoding="utf-8")
        gunluk.info("Yazıldı: %s", puan_dosyasi.name)
    ozet_yaz(puanli, gunluk)

    if form_dosyasi.exists() and not (args.force or args.yalniz_form):
        gunluk.info("Eleme formu zaten var; dokunulmadı (yenilemek için --force veya --yalniz-form).")
        return 0
    onceki = f.onceki_kararlar(form_dosyasi)
    if form_dosyasi.exists():
        yedek = form_dosyasi.with_name(f"{form_dosyasi.stem}_yedek_{utc_simdi().replace(':', '')}.xlsx")
        shutil.copy2(form_dosyasi, yedek)
        gunluk.info("Var olan form yedeklendi: %s (araştırmacı girişleri yeni forma taşınıyor)", yedek.name)
    f.form_yaz(form_tablosu(puanli, ayarlar, olcut, onceki), form_dosyasi, olcut, SUTUN_ACIKLAMALARI)
    gunluk.info("Eleme formu yazıldı: %s (%d aday). Karar sütunları boş; kararı araştırmacı verir.", form_dosyasi.name, len(puanli))
    return 0


if __name__ == "__main__":
    sys.exit(main())
