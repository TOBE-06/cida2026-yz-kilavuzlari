"""Aşama 2 – Keşif: YZ kılavuzu olabilecek aday adreslerin bulunması.

Her aktör için protokol §8'deki dört katman uygulanır ve sonuç `data/interim/adaylar.csv`
dosyasına yazılır:
  1. tohum    – tohum listesindeki bilinen adresler doğrudan kontrol edilir (koşulsuz aday)
  2. sitemap  – robots.txt ve /sitemap.xml içindeki site haritaları okunur, adresler süzülür
  3. gezinme  – ana sayfa ve tipik kurumsal sayfalardan başlayarak en fazla 2 derinlikte gezilir
  4. arama    – web arama aracıyla bulunup `arama_sonuclari.csv` dosyasına yazılmış adresler

Aday olma koşulu: adres, başlık veya bağlantı metninde en az bir YZ terimi ve bir belge terimi.
M grubu aktörlerde genel etik kod sayfaları ayrıca `etik_kod` etiketiyle aday olur.

Bu betik karar vermez; yalnızca aday listeler. robots.txt izin vermeyen, 403 veren veya bot
koruması olan sayfalar alınmaz ve `engellendi` olarak işaretlenir. Aktör başına sonuç
`kesif_alan_durumu.csv` dosyasına yazılır; betik yeniden çalıştırıldığında taranmış aktörler
atlanır (`--force` ile yeniden taranır).
"""
from __future__ import annotations

import argparse
import heapq
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import kesif as k  # noqa: E402
from hat.ag import ENGELLENDI, HATA, TAMAM, Istemci, Yanit, url_normallestir  # noqa: E402
from hat.ayarlar import anahtar_sozcukler, ayarlari_yukle, yol  # noqa: E402
from hat.kayit import gunluk_kur, hata_yaz, utc_simdi  # noqa: E402
from hat.metin import aday_eslesmesi, etik_kod_eslesmesi, html_baslik, yz_izi_var  # noqa: E402

ADAY_SUTUNLARI = [
    "aday_id", "kurum", "alan_adi", "url", "baslik", "bulunma_yolu", "eslesen_terimler",
    "bulunma_zamani_utc", "erisim_durumu", "aktor_id", "son_url",
]
DURUM_SUTUNLARI = [
    "aktor_id", "kurum", "alan_adi", "ana_sayfa_durumu", "robots", "sitemap_dosya", "sitemap_url",
    "gezilen_sayfa", "aday_sayisi", "kesilen_aday", "notlar", "zaman_utc",
]
YOL_ONCELIGI = {"tohum": 0, "arama": 1, "gezinme": 2, "sitemap": 3, "etik_kod": 4}
ASAMA = "02_kesif"


def csv_oku(dosya: Path, sutunlar: list[str] | None = None) -> pd.DataFrame:
    """CSV'yi metin olarak okur; dosya yoksa verilen sütunlarla boş tablo döndürür."""
    if not dosya.exists():
        return pd.DataFrame(columns=sutunlar or [])
    return pd.read_csv(dosya, dtype=str, keep_default_na=False, encoding="utf-8")


def parcala(deger: str) -> list[str]:
    """`a ; b` biçimindeki hücreyi parçalarına ayırır."""
    return [p.strip() for p in deger.split(";") if p.strip()]


def terim_ozeti(eslesme: dict[str, list[str]]) -> str:
    return f"yz: {', '.join(eslesme['yz'])} | belge: {', '.join(eslesme['belge'])}"


class AktorTaramasi:
    """Tek bir aktörün dört katmanlı keşfi."""

    def __init__(self, aktor: dict[str, str], tohumlar: list[str], aramalar: list[dict[str, str]],
                 istemci: Istemci, kesif: dict[str, Any]) -> None:
        self.aktor, self.tohumlar, self.aramalar = aktor, tohumlar, aramalar
        self.istemci, self.kesif = istemci, kesif
        self.alanlar = parcala(aktor["alan_adi"])
        self.m_benzeri = aktor["olasi_grup"] != "K"       # M veya henüz belirsiz
        self.adaylar: dict[str, dict[str, str]] = {}
        self.etik_kod_sayisi = 0
        self.durum = {s: "" for s in DURUM_SUTUNLARI} | {
            "aktor_id": aktor["aktor_id"], "kurum": aktor["kurum"], "alan_adi": aktor["alan_adi"],
            "sitemap_dosya": 0, "sitemap_url": 0, "gezilen_sayfa": 0, "kesilen_aday": 0,
        }
        self.notlar: list[str] = []

    # --- aday ekleme ---------------------------------------------------------

    def ekle(self, url: str, baslik: str, yol_adi: str, terimler: str, erisim: str = "", son_url: str = "") -> None:
        """Adayı ekler; aynı adres daha önce eklendiyse öncelikli bulunma yolunu korur."""
        anahtar = url_normallestir(son_url or url)
        mevcut = self.adaylar.get(anahtar)
        if mevcut:
            if YOL_ONCELIGI[yol_adi] < YOL_ONCELIGI[mevcut["bulunma_yolu"]]:
                mevcut["bulunma_yolu"] = yol_adi
            mevcut["baslik"] = mevcut["baslik"] or baslik
            mevcut["erisim_durumu"] = mevcut["erisim_durumu"] or erisim
            return
        self.adaylar[anahtar] = {
            "kurum": self.aktor["kurum"], "alan_adi": k.alan_adi(son_url or url), "url": url,
            "baslik": baslik, "bulunma_yolu": yol_adi, "eslesen_terimler": terimler,
            "bulunma_zamani_utc": utc_simdi(), "erisim_durumu": erisim,
            "aktor_id": self.aktor["aktor_id"], "son_url": son_url,
        }

    def degerlendir(self, url: str, baslik: str, baglanti_metni: str, yol_adi: str,
                    erisim: str = "", son_url: str = "") -> bool:
        """Adres aday koşulunu sağlıyorsa ekler. M benzeri aktörde etik kod sayfalarını da ekler."""
        e = aday_eslesmesi(url, baslik, baglanti_metni)
        if e["yz"] and e["belge"]:
            self.ekle(url, baslik or baglanti_metni, yol_adi, terim_ozeti(e), erisim, son_url)
            return True
        if self.m_benzeri and self.etik_kod_sayisi < self.kesif["etik_kod_max_aday"]:
            etik = etik_kod_eslesmesi(url, f"{baslik} {baglanti_metni}")
            if etik and url_normallestir(son_url or url) not in self.adaylar:
                self.etik_kod_sayisi += 1
                self.ekle(url, baslik or baglanti_metni, "etik_kod", "etik kod: " + ", ".join(etik), erisim, son_url)
                return True
        return False

    # --- katman 1 ve 4 -------------------------------------------------------

    def tohum_katmani(self) -> None:
        for url in self.tohumlar:
            yanit = self.istemci.getir(url)
            baslik = html_baslik(yanit.metin) if yanit.erisim_durumu == TAMAM and yanit.html_mi else ""
            self.ekle(url, baslik, "tohum", terim_ozeti(aday_eslesmesi(url, baslik)),
                      yanit.erisim_durumu, yanit.son_url)
            if yanit.erisim_durumu != TAMAM:
                self.notlar.append(f"tohum adresi {yanit.erisim_durumu}: {yanit.aciklama}")

    def arama_katmani(self) -> None:
        for s in self.aramalar:
            if not self.degerlendir(s["url"], s.get("baslik", ""), "", "arama"):
                self.notlar.append(f"arama sonucu aday koşulunu sağlamadı: {s['url']}")

    # --- katman 2: site haritası --------------------------------------------

    def sitemap_katmani(self, alan: str, taban: str) -> None:
        if not self.kesif["sitemap_kullan"]:
            return
        kural = self.istemci.robots_kurali(taban)
        kuyruk = list(kural.site_haritalari) or [urljoin(taban, "/sitemap.xml")]
        gorulen: set[str] = set()
        while kuyruk and self.durum["sitemap_dosya"] < self.kesif["sitemap_max_dosya"]:
            adres = kuyruk.pop(0)
            if adres in gorulen:
                continue
            gorulen.add(adres)
            yanit = self.istemci.getir(adres)
            if yanit.erisim_durumu != TAMAM:
                continue
            self.durum["sitemap_dosya"] += 1
            alt, sayfalar = k.sitemap_ayristir(yanit.icerik)
            kuyruk.extend(k.harita_sirala([a for a in alt if a not in gorulen]))
            for url in sayfalar:
                if self.durum["sitemap_url"] >= self.kesif["sitemap_max_url"]:
                    break
                self.durum["sitemap_url"] += 1
                if k.ayni_alan(url, alan) and (yz_izi_var(url) or self.m_benzeri):
                    self.degerlendir(url, "", "", "sitemap")
        if kuyruk:
            self.notlar.append(f"{alan}: site haritası üst sınırı; {len(kuyruk)} dosya okunmadı")

    # --- katman 3: sınırlı gezinme ------------------------------------------

    def gezinme_katmani(self, alan: str, ana: Yanit) -> None:
        taban = ana.son_url
        yigin: list[tuple[int, int, int, str]] = []      # (öncelik, derinlik, sıra, adres)
        gorulen = {url_normallestir(taban)}
        sira = 0

        def kuyruga(url: str, oncelik: int, derinlik: int) -> None:
            nonlocal sira
            anahtar = url_normallestir(url)
            if anahtar not in gorulen and k.sayfa_mi(url) and self.istemci.izinli(url):
                gorulen.add(anahtar)
                sira += 1
                heapq.heappush(yigin, (oncelik, derinlik, sira, url))

        for baslangic in anahtar_sozcukler()["baslangic_yollari"]:
            kuyruga(urljoin(taban, baslangic), 1, 0)
        self.sayfayi_isle(alan, ana, 0, kuyruga)
        self.durum["gezilen_sayfa"] += 1
        while yigin and self.durum["gezilen_sayfa"] < self.kesif["alan_basi_max_sayfa"]:
            _, derinlik, _, url = heapq.heappop(yigin)
            yanit = self.istemci.getir(url)
            self.durum["gezilen_sayfa"] += 1
            if yanit.erisim_durumu == TAMAM and yanit.html_mi and k.ayni_alan(yanit.son_url, alan):
                self.sayfayi_isle(alan, yanit, derinlik, kuyruga)

    def sayfayi_isle(self, alan: str, yanit: Yanit, derinlik: int, kuyruga) -> None:
        """İndirilen sayfanın kendisini ve bağlantılarını aday koşuluna göre değerlendirir."""
        html = yanit.metin
        self.degerlendir(yanit.son_url, html_baslik(html), "", "gezinme", TAMAM, yanit.son_url)
        for url, metin in k.baglantilar(html, yanit.son_url, alan):
            self.degerlendir(url, "", metin, "gezinme")
            if derinlik < self.kesif["max_derinlik"]:
                kuyruga(url, k.izleme_onceligi(url, metin), derinlik + 1)

    # --- alan adı ve sonuç ---------------------------------------------------

    def alani_tara(self, alan: str) -> str:
        """Bir alan adını tarar; ana sayfa durumunu döndürür."""
        ana = self.istemci.getir(f"https://{alan}/")
        if ana.erisim_durumu == HATA and not alan.startswith("www."):
            ana = self.istemci.getir(f"https://www.{alan}/")
        if ana.erisim_durumu == ENGELLENDI:
            self.notlar.append(f"{alan}: engellendi ({ana.aciklama}); site haritası ve gezinme yapılmadı")
            return f"{alan}: engellendi"
        if ana.erisim_durumu != TAMAM:
            self.notlar.append(f"{alan}: ana sayfa alınamadı ({ana.aciklama})")
            return f"{alan}: {ana.erisim_durumu}"
        self.sitemap_katmani(alan, ana.son_url)
        if ana.html_mi:
            self.gezinme_katmani(alan, ana)
        return f"{alan}: tamam"

    def sinirla(self) -> list[dict[str, str]]:
        """Aday üst sınırını uygular: öncelikli bulunma yolları ve çok terim eşleşenler korunur."""
        sinir = self.kesif["alan_basi_max_aday"] * max(1, len(self.alanlar))
        sirali = sorted(self.adaylar.values(),
                        key=lambda a: (YOL_ONCELIGI[a["bulunma_yolu"]], -a["eslesen_terimler"].count(",")))
        self.durum["kesilen_aday"] = max(0, len(sirali) - sinir)
        return sirali[:sinir]

    def calistir(self) -> tuple[list[dict[str, str]], dict[str, Any]]:
        self.tohum_katmani()
        self.arama_katmani()
        ana_durumlari = [self.alani_tara(alan) for alan in self.alanlar]
        if not self.alanlar:
            self.notlar.append("alan adı yok; yalnızca tohum ve arama katmanı uygulandı")
        adaylar = self.sinirla()
        self.durum.update({
            "ana_sayfa_durumu": "; ".join(ana_durumlari),
            "robots": "; ".join(f"{a}: {self.istemci.robots_kurali(f'https://{a}/').aciklama}" for a in self.alanlar),
            "aday_sayisi": len(adaylar), "notlar": " | ".join(self.notlar), "zaman_utc": utc_simdi(),
        })
        return adaylar, self.durum


def girdileri_hazirla(ayarlar: dict[str, Any], sadece: set[str]) -> tuple[list[dict], dict, dict]:
    """Evren, tohum adresleri ve arama sonuçlarını okur."""
    evren = csv_oku(yol("ara") / ayarlar["evren"]["cikti_dosyasi"]).to_dict("records")
    if sadece:
        evren = [a for a in evren if a["aktor_id"] in sadece]
    tohum = csv_oku(yol("seed") / ayarlar["evren"]["tohum_dosyasi"])
    tohumlar = {s["belge_id"]: parcala(s["bilinen_url"]) for s in tohum.to_dict("records")}
    arama = csv_oku(yol("ara") / ayarlar["kesif"]["arama_sonuclari_dosyasi"], ["kurum", "url", "baslik", "sorgu"])
    aramalar: dict[str, list[dict]] = {}
    for s in arama.to_dict("records"):
        aramalar.setdefault(s["kurum"], []).append(s)
    return evren, tohumlar, aramalar


def kaydet(adaylar: pd.DataFrame, durumlar: pd.DataFrame, ayarlar: dict[str, Any]) -> None:
    yol("ara").mkdir(parents=True, exist_ok=True)
    adaylar[ADAY_SUTUNLARI].to_csv(yol("ara") / ayarlar["kesif"]["cikti_dosyasi"], index=False, encoding="utf-8")
    durumlar[DURUM_SUTUNLARI].to_csv(yol("ara") / ayarlar["kesif"]["alan_durumu_dosyasi"], index=False, encoding="utf-8")


def sonraki_aday_no(adaylar: pd.DataFrame) -> int:
    sayilar = adaylar["aday_id"].str.extract(r"(\d+)")[0].dropna().astype(int)
    return int(sayilar.max()) + 1 if len(sayilar) else 1


def ozet_yaz(adaylar: pd.DataFrame, durumlar: pd.DataFrame, gunluk) -> None:
    gunluk.info("Toplam aday: %d (%d aktör tarandı)", len(adaylar), len(durumlar))
    for yol_adi, adet in adaylar["bulunma_yolu"].value_counts().items():
        gunluk.info("  bulunma yolu %-9s %d", yol_adi, adet)
    engelli = durumlar[durumlar["ana_sayfa_durumu"].str.contains("engellendi|hata|bulunamadi", na=False)]
    gunluk.info("Ana sayfası alınamayan veya engellenen aktör: %d", len(engelli))
    for s in engelli.to_dict("records"):
        gunluk.info("  %s %s – %s", s["aktor_id"], s["kurum"], s["ana_sayfa_durumu"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="taranacak aktörleri göster; ağa çıkma, dosya yazma")
    p.add_argument("--force", action="store_true", help="daha önce taranmış aktörleri yeniden tara")
    p.add_argument("--sadece", default="", help="yalnızca bu aktör kimlikleri (virgülle): K01,M09,A045")
    args = p.parse_args()

    ayarlar = ayarlari_yukle()
    gunluk = gunluk_kur(ASAMA)
    sadece = {s.strip() for s in args.sadece.split(",") if s.strip()}
    evren, tohumlar, aramalar = girdileri_hazirla(ayarlar, sadece)
    adaylar = csv_oku(yol("ara") / ayarlar["kesif"]["cikti_dosyasi"], ADAY_SUTUNLARI)
    durumlar = csv_oku(yol("ara") / ayarlar["kesif"]["alan_durumu_dosyasi"], DURUM_SUTUNLARI)

    taranmis = set(durumlar["aktor_id"])
    sirada = [a for a in evren if args.force or a["aktor_id"] not in taranmis]
    gunluk.info("Evrende %d aktör; %d taranacak, %d atlanıyor (zaten taranmış).",
                len(evren), len(sirada), len(evren) - len(sirada))
    if args.dry_run:
        for a in sirada:
            gunluk.info("  %s %-45s alan: %-35s tohum: %d arama: %d", a["aktor_id"], a["kurum"][:45],
                        a["alan_adi"] or "(yok)", len(tohumlar.get(a["aktor_id"], [])), len(aramalar.get(a["kurum"], [])))
        gunluk.info("Deneme çalıştırması: ağa çıkılmadı, dosya yazılmadı.")
        return 0
    if not sirada:
        ozet_yaz(adaylar, durumlar, gunluk)
        return 0

    istemci = Istemci(ayarlar["ag"])
    kilit = threading.Lock()

    def tara(aktor: dict[str, str]) -> tuple[dict, list[dict], dict]:
        tarama = AktorTaramasi(aktor, tohumlar.get(aktor["aktor_id"], []), aramalar.get(aktor["kurum"], []),
                               istemci, ayarlar["kesif"])
        try:
            return (aktor, *tarama.calistir())
        except Exception as hata:  # tek aktördeki hata diğerlerini durdurmasın
            hata_yaz(ASAMA, aktor["alan_adi"], type(hata).__name__, str(hata))
            tarama.durum.update({"ana_sayfa_durumu": "hata", "notlar": f"{type(hata).__name__}: {hata}",
                                 "aday_sayisi": 0, "zaman_utc": utc_simdi()})
            return aktor, [], tarama.durum

    with ThreadPoolExecutor(max_workers=int(ayarlar["kesif"]["es_zamanli_aktor"])) as havuz:
        for gelecek in as_completed([havuz.submit(tara, a) for a in sirada]):
            aktor, yeni, durum = gelecek.result()
            with kilit:
                adaylar = adaylar[adaylar["aktor_id"] != aktor["aktor_id"]]
                durumlar = durumlar[durumlar["aktor_id"] != aktor["aktor_id"]]
                no = sonraki_aday_no(adaylar)
                for i, aday in enumerate(yeni):
                    aday["aday_id"] = f"AD{no + i:04d}"
                adaylar = pd.concat([adaylar, pd.DataFrame(yeni, columns=ADAY_SUTUNLARI)], ignore_index=True)
                durumlar = pd.concat([durumlar, pd.DataFrame([durum])], ignore_index=True).astype(str)
                kaydet(adaylar, durumlar, ayarlar)
            gunluk.info("%s %s: %d aday (%s)", aktor["aktor_id"], aktor["kurum"], len(yeni), durum["ana_sayfa_durumu"])

    ozet_yaz(adaylar, durumlar, gunluk)
    return 0


if __name__ == "__main__":
    sys.exit(main())
