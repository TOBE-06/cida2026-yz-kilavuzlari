"""Anahtar sözcük eşleştirme ve metin çıkarımı testleri."""
from pathlib import Path

from hat.metin import (
    aday_eslesmesi, aday_mi, dil_tahmin, html_baslik, html_metin, terim_say, tum_terimler, url_metni,
)

ORNEKLER = Path(__file__).parent / "ornekler"


def oku(ad: str) -> str:
    return (ORNEKLER / ad).read_text(encoding="utf-8")


# --- eşleştirme -------------------------------------------------------------

def test_kisa_terim_yalnizca_tam_sozcuk():
    yz = tum_terimler("yz_terimi")
    assert not terim_say("Sign up to our email and retail newsletters, she said", yz)
    assert terim_say("How we use AI in the newsroom", yz)["ai"] == 1


def test_tireli_terim_sozcuk_basinda():
    yz = tum_terimler("yz_terimi")
    assert terim_say("AI-generated images", yz)["ai-"] == 1
    assert "ai-" not in terim_say("email-newsletter", yz)


def test_turkce_buyuk_harf_ve_ekler():
    assert terim_say("YAPAY ZEKÂ İLKELERİ", tum_terimler("yz_terimi"))
    assert terim_say("YAPAY ZEKÂ İLKELERİ", tum_terimler("belge_terimi"))["ilke"] == 1
    assert terim_say("yapay zekanın kullanımı", tum_terimler("yz_terimi"))["yapay zeka"] == 1


def test_turkce_normatif_ek_sozcuk_sonunda():
    normatif = tum_terimler("normatif_isaret")
    sayim = terim_say("İçerik denetlenmeli ve bildirilmelidir. Görsel kullanılamaz.", normatif)
    assert sayim["-meli"] == 1          # "bildirilmelidir" sözcük sonu değil, sayılmaz
    assert sayim["kullanılamaz"] == 1


def test_sozcuk_ortasindaki_terim_sayilmaz():
    assert "etik" not in terim_say("kozmetik ürünler", tum_terimler("belge_terimi"))


def test_url_sozcuklere_ayrilir():
    assert url_metni("https://ornek.com/about/AI-Policy_2026/") == "https ornek com about ai policy 2026"


def test_aday_kosulu_yz_ve_belge_terimi_ister():
    assert aday_mi("https://ornek.com/about/ai-policy")
    assert aday_mi("https://ornek.de/redaktion/123", baslik="Künstliche Intelligenz: fünf Leitlinien")
    assert not aday_mi("https://ornek.com/tech/new-ai-chip-launched")      # belge terimi yok
    assert not aday_mi("https://ornek.com/about/code-of-ethics")           # YZ terimi yok
    assert not aday_mi("https://ornek.com/email-policy")                   # "email" YZ terimi değil


def test_url_kaliplari_ikiye_ayrilir():
    e = aday_eslesmesi("https://ornek.com/inteligencia-artificial/kodeks")
    assert "inteligencia-artificial" in e["yz"]
    assert "kodeks" in e["belge"]


# --- metin çıkarımı ---------------------------------------------------------

def test_html_ana_metin_cikarilir():
    metin = html_metin(oku("kilavuz_en.html"))
    assert "must not publish text produced by generative AI" in metin
    assert "bu metin çıkarılmamalı" not in metin


def test_html_baslik():
    assert html_baslik(oku("kilavuz_en.html")) == "Our approach to generative AI | Example News"


def test_turkce_ornekte_terimler_sayilir():
    metin = html_metin(oku("rehber_tr.html"))
    assert sum(terim_say(metin, tum_terimler("yz_terimi")).values()) >= 4
    assert terim_say(metin, tum_terimler("normatif_isaret"))["sorumlu"] == 1


def test_dil_tahmini():
    assert dil_tahmin("", oku("kilavuz_en.html")) == "en"                 # lang özniteliğinden
    tr_html = oku("rehber_tr.html")
    assert dil_tahmin(html_metin(tr_html), tr_html) == "tr"               # terimlerden
    assert dil_tahmin("12345") == "bilinmiyor"
