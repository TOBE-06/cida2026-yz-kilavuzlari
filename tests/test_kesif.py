"""Keşif yardımcıları ve aktör taraması testleri. Gerçek ağa çıkılmaz."""
from __future__ import annotations

import gzip
import importlib.util
from pathlib import Path

from hat import kesif as k
from hat.ag import Istemci
from hat.ayarlar import ayarlari_yukle
from hat.metin import etik_kod_eslesmesi, yz_izi_var
from tests.test_ag import AYAR, SahteOturum, SahteSaat, SahteYanit

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("kesif_betigi", KOK / "scripts" / "02_kesif.py")
betik = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(betik)

DIZIN = b"""<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>https://ornek.com/sitemap-news-2024.xml</loc></sitemap>
<sitemap><loc>https://ornek.com/sitemap-pages.xml</loc></sitemap></sitemapindex>"""
LISTE = b"""<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://ornek.com/about/ai-policy</loc></url>
<url><loc>https://ornek.com/sport/final</loc></url>
<url><loc>https://ornek.com/tech/new-ai-chip</loc></url></urlset>"""


def test_sitemap_dizini_ve_listesi_ayristirilir():
    alt, sayfalar = k.sitemap_ayristir(DIZIN)
    assert alt == ["https://ornek.com/sitemap-news-2024.xml", "https://ornek.com/sitemap-pages.xml"] and not sayfalar
    alt, sayfalar = k.sitemap_ayristir(gzip.compress(LISTE))
    assert not alt and len(sayfalar) == 3


def test_kurumsal_harita_tarihli_arsivden_once():
    assert k.harita_sirala(k.sitemap_ayristir(DIZIN)[0])[0].endswith("sitemap-pages.xml")


def test_baglantilar_yalnizca_ayni_alan():
    html = """<a href="/about/ai-policy">AI policy</a> <a href="https://baska.com/x">dış</a>
              <a href="https://alt.ornek.com/y#bolum">Alt alan</a> <a href="mailto:a@ornek.com">posta</a>"""
    sonuc = dict(k.baglantilar(html, "https://ornek.com/", "ornek.com"))
    assert sonuc == {"https://ornek.com/about/ai-policy": "AI policy", "https://alt.ornek.com/y": "Alt alan"}


def test_izleme_onceligi():
    assert k.izleme_onceligi("https://ornek.com/about/ai-policy", "AI policy") == 0
    assert k.izleme_onceligi("https://ornek.com/about-us", "About us") == 1
    assert k.izleme_onceligi("https://ornek.com/sport/final", "Final") == 2


def test_gorsel_ve_pdf_gezinmede_indirilmez():
    assert not k.sayfa_mi("https://ornek.com/a.PDF") and not k.sayfa_mi("https://ornek.com/a.jpg")
    assert k.sayfa_mi("https://ornek.com/about")


def test_hizli_yz_suzgeci_ve_etik_kod():
    assert yz_izi_var("https://ornek.com/about/ai-policy") and not yz_izi_var("https://ornek.com/email-policy")
    assert etik_kod_eslesmesi("https://konsey.org/code-of-ethics") == ["code of ethics"]
    assert not etik_kod_eslesmesi("https://konsey.org/complaints/2024/12")


def _tara(aktor: dict, sayfalar: dict, tohumlar=(), aramalar=()):
    oturum, saat = SahteOturum(sayfalar), SahteSaat()
    istemci = Istemci(AYAR, oturum=oturum, uyku=saat.uyku, saat=saat.saat)
    tarama = betik.AktorTaramasi(aktor, list(tohumlar), list(aramalar), istemci, ayarlari_yukle()["kesif"])
    adaylar, durum = tarama.calistir()
    return {a["url"]: a for a in adaylar}, durum, oturum, saat


def test_aktor_taramasi_dort_katman():
    ana = '<title>Örnek</title><a href="/about">About</a> <a href="/sport">Sport</a> <a href="/gizli/ai-policy">x</a>'
    hakkinda = '<title>About</title><a href="/about/our-approach-to-generative-ai">Our approach to generative AI</a>'
    sayfalar = {
        "https://ornek.com/robots.txt": SahteYanit("", govde="User-agent: *\nDisallow: /gizli/\n"),
        "https://ornek.com/": SahteYanit("https://ornek.com/", govde=ana),
        "https://ornek.com/about": SahteYanit("https://ornek.com/about", govde=hakkinda),
        "https://ornek.com/sitemap.xml": SahteYanit("https://ornek.com/sitemap.xml", govde=LISTE.decode(), tur="text/xml"),
        "https://ornek.com/eski-politika": SahteYanit("https://ornek.com/eski-politika", 403),
    }
    aktor = {"aktor_id": "K99", "kurum": "Örnek", "alan_adi": "ornek.com", "olasi_grup": "K"}
    adaylar, durum, oturum, saat = _tara(
        aktor, sayfalar, tohumlar=["https://ornek.com/eski-politika"],
        aramalar=[{"url": "https://ornek.com/standards/ai-guidelines.pdf", "baslik": "AI guidelines"}],
    )
    yollar = {u: a["bulunma_yolu"] for u, a in adaylar.items()}
    assert yollar["https://ornek.com/eski-politika"] == "tohum"
    assert adaylar["https://ornek.com/eski-politika"]["erisim_durumu"] == "engellendi"
    assert yollar["https://ornek.com/standards/ai-guidelines.pdf"] == "arama"
    assert yollar["https://ornek.com/about/our-approach-to-generative-ai"] == "gezinme"
    assert yollar["https://ornek.com/about/ai-policy"] == "sitemap"
    assert "https://ornek.com/tech/new-ai-chip" not in adaylar           # belge terimi yok
    assert "https://ornek.com/gizli/ai-policy" not in oturum.istekler      # robots yasağı: istenmedi
    assert durum["ana_sayfa_durumu"] == "ornek.com: tamam" and durum["sitemap_dosya"] == 1
    assert all(sure >= 5 for sure in saat.uykular)                         # istekler arası bekleme korunur


def test_engellenen_alan_zorlanmaz():
    sayfalar = {"https://ornek.com/robots.txt": SahteYanit("", govde="User-agent: *\nDisallow: /\n")}
    aktor = {"aktor_id": "K98", "kurum": "Kapalı", "alan_adi": "ornek.com", "olasi_grup": "K"}
    adaylar, durum, oturum, _ = _tara(aktor, sayfalar)
    assert not adaylar and "engellendi" in durum["ana_sayfa_durumu"]
    assert oturum.istekler == ["https://ornek.com/robots.txt"]


def test_m_grubunda_etik_kod_sayfasi_aday_olur():
    ana = '<a href="/code-of-ethics">Code of Ethics</a> <a href="/complaints">Complaints</a>'
    sayfalar = {
        "https://konsey.org/robots.txt": SahteYanit("", 404),
        "https://konsey.org/": SahteYanit("https://konsey.org/", govde=ana),
    }
    aktor = {"aktor_id": "M99", "kurum": "Konsey", "alan_adi": "konsey.org", "olasi_grup": "M"}
    adaylar, _, _, _ = _tara(aktor, sayfalar)
    assert adaylar["https://konsey.org/code-of-ethics"]["bulunma_yolu"] == "etik_kod"
    assert "https://konsey.org/complaints" not in adaylar
