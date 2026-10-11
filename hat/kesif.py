"""Keşif aşamasının ağdan bağımsız yardımcıları: site haritası okuma, bağlantı çıkarma, önceliklendirme."""
from __future__ import annotations

import gzip
import re
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup
from lxml import etree

from hat.ag import alan_adi
from hat.ayarlar import ayarlari_yukle
from hat.metin import aday_eslesmesi, kucult, url_metni

# Gezinmede indirilmeyen dosya türleri (sayfa değil; görsel, ses, arşiv vb.)
ATLANAN_UZANTILAR = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".mp3", ".mp4", ".avi", ".mov", ".zip",
    ".gz", ".css", ".js", ".xml", ".rss", ".json", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
)
HARITA_ONCELIK_IPUCLARI = ("page", "static", "about", "corporate", "misc", "info", "general", "post", "main")


def ayni_alan(url: str, alan: str) -> bool:
    """URL bu alan adına veya onun bir alt alan adına mı ait?"""
    konak = alan_adi(url)
    return konak == alan or konak.endswith("." + alan)


def sitemap_ayristir(icerik: bytes) -> tuple[list[str], list[str]]:
    """Site haritası dosyasını okur; (alt site haritaları, sayfa adresleri) döndürür.

    XML dizin dosyası, XML adres listesi, gzip ile sıkıştırılmış dosya ve satır satır düz metin desteklenir.
    """
    if icerik[:2] == b"\x1f\x8b":
        try:
            icerik = gzip.decompress(icerik)
        except OSError:
            return [], []
    try:
        kok = etree.fromstring(icerik, parser=etree.XMLParser(recover=True, resolve_entities=False, no_network=True))
    except etree.XMLSyntaxError:
        kok = None
    if kok is None:
        satirlar = icerik.decode("utf-8", errors="ignore").split()
        return [], [s for s in satirlar if s.startswith("http")]
    alt, sayfalar = [], []
    for loc in kok.iter("{*}loc"):
        adres = (loc.text or "").strip()
        ebeveyn = etree.QName(loc.getparent()).localname if loc.getparent() is not None else ""
        if adres and ebeveyn == "sitemap":
            alt.append(adres)
        elif adres and ebeveyn == "url":
            sayfalar.append(adres)
    return alt, sayfalar


def harita_sirala(haritalar: list[str]) -> list[str]:
    """Alt site haritalarını sıralar: kurumsal/sabit sayfa haritaları önce, tarihli haber arşivleri sonra."""
    def puan(adres: str) -> tuple[int, int]:
        kucuk = adres.lower()
        ipucu = 0 if any(i in kucuk for i in HARITA_ONCELIK_IPUCLARI) else 1
        tarihli = 1 if re.search(r"(19|20)\d{2}", kucuk) else 0
        return (ipucu + tarihli, 0)
    return sorted(haritalar, key=puan)


def baglantilar(html: str, taban_url: str, alan: str) -> list[tuple[str, str]]:
    """Sayfadaki aynı alan adına giden bağlantıları (adres, bağlantı metni) olarak döndürür."""
    corba = BeautifulSoup(html, "lxml")
    gorulen: dict[str, str] = {}
    for a in corba.find_all("a", href=True):
        adres = urldefrag(urljoin(taban_url, a["href"].strip())).url
        if urlsplit(adres).scheme not in ("http", "https") or not ayni_alan(adres, alan):
            continue
        metin = re.sub(r"\s+", " ", a.get_text(" ")).strip()
        if adres not in gorulen or (metin and not gorulen[adres]):
            gorulen[adres] = metin
    return list(gorulen.items())


def sayfa_mi(url: str) -> bool:
    """Gezinmede indirilebilecek bir sayfa mı? (görsel, arşiv vb. dosyalar ve PDF indirilmez)"""
    yol = urlsplit(url).path.lower()
    return not yol.endswith(ATLANAN_UZANTILAR) and not yol.endswith(".pdf")


def izleme_onceligi(url: str, baglanti_metni: str) -> int:
    """Gezinmede bağlantının izlenme önceliği: 0 aday, 1 kurumsal/ilgili, 2 diğer."""
    e = aday_eslesmesi(url, baglanti_metni=baglanti_metni)
    if e["yz"] and e["belge"]:
        return 0
    birlesik = url_metni(url) + " " + kucult(baglanti_metni) + " " + url.lower()
    ipuclari = ayarlari_yukle()["kesif"]["kurumsal_ipuclari"]
    if e["yz"] or e["belge"] or any(i in birlesik for i in ipuclari):
        return 1
    return 2
