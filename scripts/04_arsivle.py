"""Aşama 4 – Arşivleme.

Yalnızca eleme formunda araştırmacının `karar = Dahil` dediği adayları arşivler. Her belge
(parçası) için protokol §10'daki dosyalar `archive/K/` veya `archive/M/` altına yazılır:
  .pdf  sayfanın işlenmiş görüntüsü (Playwright, A4, ekran medyası); kaynak PDF ise özgün dosya
  .html ham HTML          .txt çıkarılmış ana metin          .png tam sayfa ekran görüntüsü
  .json üst veri (adresler, HTTP durumu, erişim zamanı, başlık, dil, SHA-256 özetleri, Wayback kopyası)

Etik kurallar: robots.txt izin vermeyen, 403 veren veya bot koruması olan sayfalar zorlanmaz.
Bu belgeler için sırayla şunlara bakılır:
  1. `archive/manuel/` içinde araştırmacının bu belge kimliğiyle kaydettiği PDF
  2. (ayar açıksa) `data/mevcut_arsiv/` içindeki, araştırmacının önceden elle kaydettiği PDF
İkisi de yoksa belge `archive/manuel/BEKLENEN_DOSYALAR.md` listesine yazılır.

Belge kimlikleri: önceden derlenen belgeler kimliğini korur; yeni belgeler sıradaki numarayı alır.
Aynı belgenin birden çok adresi varsa parçalar `K03a`, `K03b` biçiminde adlandırılır.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from playwright.sync_api import Browser, Error as PlaywrightHatasi, TimeoutError as PlaywrightZamanAsimi, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import form as f  # noqa: E402
from hat.adlandirma import dosya_adi, sonraki_kimlik  # noqa: E402
from hat.ag import TAMAM, Istemci  # noqa: E402
from hat.ayarlar import KOK, ayarlari_yukle, yol  # noqa: E402
from hat.kayit import gunluk_kur, hata_yaz, sha256_dosya, utc_simdi  # noqa: E402
from hat.metin import dil_tahmin, html_metin, pdf_metin, terim_say, tum_terimler  # noqa: E402
from hat.puanlama import wayback_kopyasi  # noqa: E402

ASAMA = "04_arsivle"
DURUM_SUTUNLARI = ["belge_id", "parca", "aday_id", "kurum", "grup", "url", "toplama_yontemi", "durum",
                   "gorsel_kontrol_gerekli", "aciklama", "ust_veri", "zaman_utc"]
MEVCUT_AD_DESENI = re.compile(r"^([KM]\d+)_(.+)_([^_]+)_(\d{4}-\d{2}-\d{2})\.pdf$")


# --- hazırlık -----------------------------------------------------------------

def mevcut_arsiv_dosyalari() -> dict[str, dict[str, Any]]:
    """`data/mevcut_arsiv` içindeki PDF'leri belge kimliğine göre dizinler (yalnızca okur)."""
    kok, sonuc = yol("mevcut_arsiv"), {}
    for dosya in sorted(kok.rglob("*.pdf")) if kok.exists() else []:
        if (m := MEVCUT_AD_DESENI.match(dosya.name)):
            sonuc[m.group(1)] = {"dosya": dosya, "kurum": m.group(2), "kisa_ad": m.group(3), "tarih": m.group(4)}
    return sonuc


def kisa_ad_uret(kurum: str) -> str:
    """Kurum adından kısa ad üretir: parantez içindeki kısaltma, yoksa baş harfler."""
    if (m := re.search(r"\(([A-ZÇĞİÖŞÜ0-9&/.-]{2,12})\)", kurum)):      # yalnızca büyük harfli kısaltmalar: (SJF), (RTDNA)
        return m.group(1)
    sozcukler = re.findall(r"\w+", re.sub(r"\([^)]*\)", "", kurum))
    return sozcukler[0] if len(sozcukler) == 1 else "".join(s[0] for s in sozcukler)[:8].upper()


def kimlikleri_ata(dahil: pd.DataFrame, ayarlar: dict, yaz: bool = True) -> pd.DataFrame:
    """Her dahil satırına belge kimliği ve parça harfi verir; yeni kimlikleri kalıcı dosyada saklar."""
    dosya = yol("ara") / ayarlar["arsiv"]["kimlik_dosyasi"]
    kayitli = pd.read_csv(dosya, dtype=str, keep_default_na=False) if dosya.exists() else pd.DataFrame(columns=["aday_id", "belge_id"])
    harita = dict(zip(kayitli["aday_id"], kayitli["belge_id"]))
    tohum = pd.read_csv(yol("seed") / ayarlar["evren"]["tohum_dosyasi"], dtype=str, keep_default_na=False)
    kullanilan = list(tohum["belge_id"]) + list(harita.values())
    dahil = dahil.sort_values("aday_id").copy()
    kimlikler = {}
    for s in dahil.to_dict("records"):                      # önce ana belgeler
        if s["mevcut_belge"]:
            kimlikler[s["aday_id"]] = s["mevcut_belge"]
        elif not s["birlestir"]:
            if s["aday_id"] not in harita:
                harita[s["aday_id"]] = sonraki_kimlik(kullanilan, s["grup"])
                kullanilan.append(harita[s["aday_id"]])
            kimlikler[s["aday_id"]] = harita[s["aday_id"]]
    for s in dahil.to_dict("records"):                      # sonra ana belgeye bağlananlar
        if s["aday_id"] not in kimlikler:
            kimlikler[s["aday_id"]] = kimlikler.get(s["birlestir"], "")
    dahil["belge_id"] = dahil["aday_id"].map(kimlikler)
    dahil["_bagli"] = (dahil["birlestir"] != "").astype(int)          # ana metin önce (a), bağlananlar sonra (b, c ...)
    dahil = dahil.sort_values(["belge_id", "_bagli", "aday_id"]).drop(columns="_bagli")
    sira = dahil.groupby("belge_id").cumcount()
    adet = dahil.groupby("belge_id")["aday_id"].transform("size")
    dahil["parca"] = [chr(ord("a") + i) if n > 1 else "" for i, n in zip(sira, adet)]
    if harita and yaz:
        dosya.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(sorted(harita.items()), columns=["aday_id", "belge_id"]).to_csv(dosya, index=False, encoding="utf-8")
    return dahil


# --- tarayıcı -----------------------------------------------------------------

def cerezi_reddet(sayfa, metinler: list[str]) -> str:
    """Yalnızca "reddet / yalnızca gerekli" türü bir düğme görünüyorsa tıklar; tıklanan metni döndürür."""
    desen = re.compile(r"^\s*(" + "|".join(re.escape(m) for m in metinler) + r")\s*$", re.IGNORECASE)
    for cerceve in sayfa.frames:
        try:
            dugme = cerceve.get_by_role("button", name=desen).first
            if dugme.count() and dugme.is_visible():
                metin = dugme.inner_text().strip()
                dugme.click(timeout=3000)
                sayfa.wait_for_timeout(1000)
                return metin
        except PlaywrightHatasi:
            continue
    return ""


def tarayicida_kaydet(tarayici: Browser, url: str, istemci: Istemci, ayarlar: dict, pdf: Path, png: Path) -> dict[str, Any]:
    """Sayfayı tarayıcıda açıp PDF ve tam sayfa PNG olarak kaydeder. Engel yanıtı gelirse kaydetmez."""
    arsiv = ayarlar["arsiv"]
    baglam = tarayici.new_context(user_agent=istemci.user_agent, viewport=arsiv["gorunum"])
    try:
        sayfa = baglam.new_page()
        istemci.bekle(url)
        try:
            yanit = sayfa.goto(url, wait_until="networkidle", timeout=arsiv["sayfa_zaman_asimi_sn"] * 1000)
        except PlaywrightZamanAsimi:        # arka plan istekleri bitmeyen sayfa: yüklenen haliyle devam
            yanit = None
        if yanit is not None and yanit.status in ayarlar["ag"]["engel_durum_kodlari"]:
            return {"engel": f"tarayıcıda HTTP {yanit.status}"}
        cerez = cerezi_reddet(sayfa, arsiv["cerez_red_metinleri"])
        sayfa.emulate_media(media=arsiv["medya"])
        if arsiv["tam_sayfa_png"]:
            sayfa.screenshot(path=str(png), full_page=True)
        sayfa.pdf(path=str(pdf), format=arsiv["pdf_bicimi"], print_background=True)
        return {"baslik": sayfa.title(), "html": sayfa.content(), "cerez_dugmesi": cerez}
    finally:
        baglam.close()


# --- tek belge parçası --------------------------------------------------------

class Parca:
    """Arşivlenecek tek belge parçası (çoğu belgede tek parça vardır)."""

    def __init__(self, satir: dict[str, str], mevcut: dict[str, dict], ayarlar: dict) -> None:
        self.s, self.ayarlar = satir, ayarlar
        self.belge_id, self.kimlik = satir["belge_id"], satir["belge_id"] + satir["parca"]
        self.mevcut = mevcut.get(self.belge_id)
        self.kurum = self.mevcut["kurum"] if self.mevcut else re.sub(r"\s*\([^)]*\)", "", satir["kurum"])
        self.kisa_ad = self.mevcut["kisa_ad"] if self.mevcut else kisa_ad_uret(satir["kurum"])
        self.klasor = yol("arsiv") / satir["grup"]
        self.notlar: list[str] = []

    def yol(self, tarih: str, uzanti: str) -> Path:
        return self.klasor / dosya_adi(self.kimlik, self.kurum, self.kisa_ad, tarih, uzanti)

    def eski_tek_parcayi_ayir(self) -> list[str]:
        """Belge sonradan çok parçalı olduysa, harfsiz adla kaydedilmiş önceki dosyaları `eski_surum` klasörüne taşır.

        Dosyalar silinmez; yalnızca arşiv içinde ayrı klasöre alınır ki envanter ve manifest çift saymasın.
        """
        if not self.s["parca"]:
            return []
        hedef = yol("arsiv") / self.ayarlar["arsiv"]["eski_surum_klasoru"] / self.s["grup"]
        tasinan = []
        for dosya in sorted(self.klasor.glob(f"{self.belge_id}_*")):
            hedef.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dosya), str(hedef / dosya.name))
            tasinan.append(dosya.name)
        return tasinan

    def var_olan_ust_veri(self) -> Path | None:
        return next(iter(sorted(self.klasor.glob(f"{self.kimlik}_*.json"))), None)

    def durum(self, yontem: str, durum: str, aciklama: str = "", ust_veri: Path | None = None, gorsel: bool = False) -> dict:
        return {"belge_id": self.belge_id, "parca": self.s["parca"], "aday_id": self.s["aday_id"], "kurum": self.s["kurum"],
                "grup": self.s["grup"], "url": self.s["url"], "toplama_yontemi": yontem, "durum": durum,
                "gorsel_kontrol_gerekli": "evet" if gorsel else "hayır", "aciklama": aciklama,
                "ust_veri": str(ust_veri.relative_to(KOK)) if ust_veri else "", "zaman_utc": utc_simdi()}

    def ust_veri_yaz(self, tarih: str, dosyalar: dict[str, Path], metin: str, alanlar: dict[str, Any]) -> tuple[Path, bool]:
        """Metni ve üst veriyi yazar; özetleri diskteki dosyalardan hesaplar. (üst veri yolu, görsel kontrol) döndürür."""
        txt = self.yol(tarih, "txt")
        txt.write_text(metin, encoding="utf-8")
        dosyalar = dosyalar | {"txt": txt}
        yz = sum(terim_say(metin, tum_terimler("yz_terimi")).values())
        gorsel = len(metin) < self.ayarlar["arsiv"]["min_metin_uzunlugu"] or yz == 0
        veri = {
            "belge_id": self.belge_id, "parca": self.s["parca"], "aday_id": self.s["aday_id"], "kurum": self.s["kurum"],
            "grup": self.s["grup"], "istenen_url": self.s["url"], "dil": dil_tahmin(metin, alanlar.pop("_html", "")) if metin else "",
            "metin_uzunlugu": len(metin), "yz_terim_sayisi": yz, "gorsel_kontrol_gerekli": gorsel,
            "user_agent": self.ayarlar["ag"]["user_agent"], "notlar": self.notlar,
        } | alanlar | {
            "dosyalar": {uz: {"ad": d.name, "boyut": d.stat().st_size, "sha256": sha256_dosya(d)} for uz, d in dosyalar.items()},
        }
        ust = self.yol(tarih, "json")
        ust.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
        return ust, gorsel

    # --- otomatik ---

    def otomatik(self, istemci: Istemci, tarayici: Browser) -> dict | None:
        """Sayfayı siteden arşivler. Erişilemiyorsa None döner (manuel yola geçilir)."""
        url = self.s["url"]
        if not url:
            self.notlar.append("tohum listesinde adres yok")
            return None
        yanit = istemci.getir(url)
        if yanit.erisim_durumu != TAMAM:
            self.notlar.append(f"otomatik erişim: {yanit.erisim_durumu} ({yanit.aciklama})")
            return None
        tarih = yanit.zaman_utc[:10]
        self.klasor.mkdir(parents=True, exist_ok=True)
        alanlar: dict[str, Any] = {"son_url": yanit.son_url, "http_durumu": yanit.durum_kodu, "erisim_zamani_utc": yanit.zaman_utc,
                                   "toplama_yontemi": "otomatik"}
        if yanit.pdf_mi:
            pdf = self.yol(tarih, "pdf")
            pdf.write_bytes(yanit.icerik)
            metin, dosyalar = pdf_metin(yanit.icerik), {"pdf": pdf}
            alanlar |= {"baslik": self.s["baslik"], "kaynak_bicimi": "pdf"}
            self.notlar.append("kaynak PDF: özgün dosya indirildi; HTML ve PNG üretilmedi")
        else:
            html_dosyasi, pdf, png = self.yol(tarih, "html"), self.yol(tarih, "pdf"), self.yol(tarih, "png")
            sonuc = tarayicida_kaydet(tarayici, yanit.son_url, istemci, self.ayarlar, pdf, png)
            if "engel" in sonuc:                            # tarayıcıya engel yanıtı geldi: zorlanmaz, manuel yola geçilir
                self.notlar.append(f"otomatik erişim: {sonuc['engel']}")
                return None
            html_dosyasi.write_bytes(yanit.icerik)
            metin = html_metin(yanit.metin)
            if len(metin) < self.ayarlar["arsiv"]["min_metin_uzunlugu"]:
                islenmis = html_metin(sonuc["html"])
                if len(islenmis) > len(metin):
                    metin = islenmis
                    self.notlar.append("metin, tarayıcıda işlenmiş sayfadan çıkarıldı (ham HTML'de metin kısa)")
            dosyalar = {"html": html_dosyasi, "pdf": pdf} | ({"png": png} if png.exists() else {})
            alanlar |= {"baslik": sonuc["baslik"], "kaynak_bicimi": "html", "cerez_dugmesi": sonuc["cerez_dugmesi"], "_html": yanit.metin}
        if self.ayarlar["arsiv"]["wayback_kontrol"]:
            alanlar["wayback_url"] = wayback_kopyasi(istemci, url, self.ayarlar["puanlama"]["wayback_api"])
        ust, gorsel = self.ust_veri_yaz(tarih, dosyalar, metin, alanlar)
        return self.durum("otomatik", "arşivlendi", "; ".join(self.notlar), ust, gorsel)

    # --- manuel ---

    def manuel(self, istemci: Istemci) -> dict:
        """Araştırmacının elle kaydettiği PDF'i arşive alır; yoksa belgeyi beklenenler listesine bırakır."""
        arsiv = self.ayarlar["arsiv"]
        elle = sorted((yol("arsiv") / arsiv["manuel_klasoru"]).glob(f"{self.kimlik}_*.pdf"))
        if elle:
            kaynak, m = elle[0], re.search(r"(\d{4}-\d{2}-\d{2})\.pdf$", elle[0].name)
            tarih, kaynak_notu = (m.group(1) if m else utc_simdi()[:10]), "archive/manuel klasöründen"
        elif arsiv["mevcut_arsivi_manuel_say"] and self.mevcut and self.s["parca"] in ("", "a"):
            kaynak, tarih = self.mevcut["dosya"], self.mevcut["tarih"]
            kaynak_notu = "araştırmacının önceden elle kaydettiği dosya (data/mevcut_arsiv)"
        else:
            return self.durum("manuel", "bekliyor", "; ".join(self.notlar))
        self.klasor.mkdir(parents=True, exist_ok=True)
        pdf = self.yol(tarih, "pdf")
        shutil.copy2(kaynak, pdf)
        try:
            metin = pdf_metin(pdf.read_bytes())
        except Exception as hata:
            metin = ""
            self.notlar.append(f"PDF metni çıkarılamadı: {type(hata).__name__}")
        self.notlar.append(f"manuel kopya: {kaynak_notu}; erişim tarihi dosya adından alındı (saat bilinmiyor)")
        alanlar = {"son_url": "", "http_durumu": None, "erisim_zamani_utc": tarih, "baslik": self.s["baslik"],
                   "kaynak_bicimi": "pdf", "toplama_yontemi": "manuel", "kaynak_dosya": kaynak.name,
                   "ust_veri_yazim_zamani_utc": utc_simdi()}
        if arsiv["wayback_kontrol"] and self.s["url"]:
            alanlar["wayback_url"] = wayback_kopyasi(istemci, self.s["url"], self.ayarlar["puanlama"]["wayback_api"])
        ust, gorsel = self.ust_veri_yaz(tarih, {"pdf": pdf}, metin, alanlar)
        return self.durum("manuel", "arşivlendi", "; ".join(self.notlar), ust, gorsel)


# --- çıktı ve ana akış --------------------------------------------------------

def beklenenleri_yaz(durumlar: pd.DataFrame, parcalar: dict[str, Parca], ayarlar: dict) -> None:
    """Elle kaydedilmesi gereken belgeleri, hangi adla ve hangi adresten kaydedileceğiyle listeler."""
    klasor = yol("arsiv") / ayarlar["arsiv"]["manuel_klasoru"]
    klasor.mkdir(parents=True, exist_ok=True)
    bekleyen = durumlar[durumlar["durum"] == "bekliyor"]
    satirlar = ["# Elle kaydedilmesi beklenen belgeler", "",
                f"Güncelleme: {utc_simdi()} · Bekleyen: {len(bekleyen)}", "",
                "Her sayfayı tarayıcınızda açın, **Yazdır → PDF olarak kaydet** ile aşağıdaki adla bu klasöre",
                "(`archive/manuel/`) kaydedin; dosya adındaki tarihi kaydettiğiniz günün tarihi yapın. Sonra",
                "`python scripts/run_pipeline.py --asama 4` komutunu yeniden çalıştırın.", ""]
    for s in bekleyen.to_dict("records"):
        p = parcalar[s["belge_id"] + s["parca"]]
        ad = dosya_adi(p.kimlik, p.kurum, p.kisa_ad, utc_simdi()[:10], "pdf")
        satirlar += [f"- **{p.kimlik}** {s['kurum']}", f"  - Adres: {s['url'] or 'bilinmiyor (tohum listesinde adres yok)'}",
                     f"  - Kaydedilecek ad: `{ad}`", f"  - Neden: {s['aciklama']}"]
    (klasor / ayarlar["arsiv"]["beklenen_dosyasi"]).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def ertelenenleri_ayir(durumlar: pd.DataFrame, gecerli: set[str], ayarlar: dict, gunluk) -> pd.DataFrame:
    """Kararı artık "Dahil" olmayan belgelerin arşiv dosyalarını `ertelenen` klasörüne taşır (silmez)."""
    tasinan: dict[str, int] = {}
    for grup in ("K", "M"):
        for dosya in sorted((yol("arsiv") / grup).glob("*")) if (yol("arsiv") / grup).exists() else []:
            kimlik = dosya.name.split("_")[0]
            if dosya.is_file() and re.fullmatch(r"[KM]\d+[a-z]?", kimlik) and kimlik not in gecerli:
                hedef = yol("arsiv") / ayarlar["arsiv"]["ertelenen_klasoru"] / grup
                hedef.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dosya), str(hedef / dosya.name))
                tasinan[kimlik] = tasinan.get(kimlik, 0) + 1
    if tasinan:
        gunluk.info("Kararı artık 'Dahil' olmayan %d belge parçasının %d dosyası %s klasörüne taşındı: %s", len(tasinan),
                    sum(tasinan.values()), ayarlar["arsiv"]["ertelenen_klasoru"], ", ".join(sorted(tasinan)))
    return durumlar[(durumlar["belge_id"] + durumlar["parca"]).isin(gecerli)]


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--dry-run", action="store_true", help="arşivlenecek belgeleri göster; ağa çıkma, dosya yazma")
    a.add_argument("--force", action="store_true", help="daha önce arşivlenmiş belgeleri yeniden arşivle (eski dosyalar silinmez)")
    a.add_argument("--sadece", default="", help="yalnızca bu belge kimlikleri (virgülle): K01,M03")
    args = a.parse_args()

    ayarlar = ayarlari_yukle()
    gunluk = gunluk_kur(ASAMA)
    tablo = f.form_oku(yol("eleme") / ayarlar["puanlama"]["form_dosyasi"])
    dahil = tablo[tablo["karar"] == "Dahil"]
    gunluk.info("Formda %d aday; karar: %s", len(tablo), tablo["karar"].replace("", "(boş)").value_counts().to_dict())
    if dahil.empty:
        gunluk.info("Formda 'Dahil' kararı yok; arşivlenecek belge bulunmuyor.")
        return 0
    eksik_grup = dahil[~dahil["grup"].isin(["K", "M"])]
    if len(eksik_grup):
        gunluk.error("Şu dahil adaylarda grup (K/M) boş; arşiv klasörü belirlenemiyor: %s", ", ".join(eksik_grup["aday_id"]))
        return 1
    dahil = kimlikleri_ata(dahil, ayarlar, yaz=not args.dry_run)
    sadece = {s.strip() for s in args.sadece.split(",") if s.strip()}
    mevcut = mevcut_arsiv_dosyalari()
    parcalar = {s["belge_id"] + s["parca"]: Parca(s, mevcut, ayarlar) for s in dahil.to_dict("records")}
    durum_dosyasi = yol("ara") / ayarlar["arsiv"]["durum_dosyasi"]
    durumlar = (pd.read_csv(durum_dosyasi, dtype=str, keep_default_na=False) if durum_dosyasi.exists()
                else pd.DataFrame(columns=DURUM_SUTUNLARI))
    if not args.dry_run:
        durumlar = ertelenenleri_ayir(durumlar, set(parcalar), ayarlar, gunluk)
        durumlar.to_csv(durum_dosyasi, index=False, encoding="utf-8")
    sirada = [p for k, p in parcalar.items()
              if (not sadece or p.belge_id in sadece) and (args.force or p.var_olan_ust_veri() is None)]
    gunluk.info("%d belge parçası (%d belge); %d işlenecek, %d zaten arşivde.", len(parcalar), dahil["belge_id"].nunique(),
                len(sirada), len(parcalar) - len(sirada))
    if args.dry_run:
        for p in sirada:
            gunluk.info("  %s %-40s %s", p.kimlik, p.s["kurum"][:40], p.s["url"] or "(adres yok → manuel)")
        gunluk.info("Deneme çalıştırması: ağa çıkılmadı, dosya yazılmadı.")
        return 0

    istemci = Istemci(ayarlar["ag"])
    with sync_playwright() as pw:
        tarayici = pw.chromium.launch()
        for p in sirada:
            if (tasinan := p.eski_tek_parcayi_ayir()):
                gunluk.info("%s artık çok parçalı; harfsiz adlı %d önceki dosya eski_surum klasörüne taşındı.", p.belge_id, len(tasinan))
            try:
                sonuc = p.otomatik(istemci, tarayici) or p.manuel(istemci)
            except Exception as hata:  # tek belgedeki hata diğerlerini durdurmasın
                hata_yaz(ASAMA, p.s["url"], type(hata).__name__, str(hata))
                sonuc = p.durum("otomatik", "başarısız", f"{type(hata).__name__}: {hata}")
            eski_satir = (durumlar["belge_id"] == p.belge_id) & (durumlar["parca"].isin([p.s["parca"]] + ([""] if p.s["parca"] else [])))
            durumlar = durumlar[~eski_satir]
            durumlar = pd.concat([durumlar, pd.DataFrame([sonuc])], ignore_index=True)
            durumlar.sort_values(["belge_id", "parca"]).to_csv(durum_dosyasi, index=False, encoding="utf-8")
            gunluk.info("%s %s: %s / %s%s", p.kimlik, p.s["kurum"][:35], sonuc["toplama_yontemi"], sonuc["durum"],
                        " [görsel kontrol]" if sonuc["gorsel_kontrol_gerekli"] == "evet" else "")
        tarayici.close()

    beklenenleri_yaz(durumlar, parcalar, ayarlar)
    ozet = durumlar.groupby(["toplama_yontemi", "durum"]).size()
    gunluk.info("Özet: %s", {f"{y}/{d}": int(n) for (y, d), n in ozet.items()})
    gunluk.info("Görsel kontrol gereken: %d", int((durumlar["gorsel_kontrol_gerekli"] == "evet").sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
