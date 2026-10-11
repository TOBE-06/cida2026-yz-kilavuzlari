"""Ağ yardımcısı testleri. Gerçek ağa çıkılmaz; sahte oturum ve sahte saat kullanılır."""
from __future__ import annotations

import requests

from hat.ag import BULUNAMADI, ENGELLENDI, HATA, TAMAM, Istemci, alan_adi, url_kodla, url_normallestir

AYAR = {
    "user_agent": "CIDA2026-Test/1.0 (test)",
    "alan_basi_bekleme_sn": 5,
    "zaman_asimi_sn": 30,
    "yeniden_deneme": 3,
    "robots_txt_uy": True,
    "engel_durum_kodlari": [401, 403, 429],
    "bot_korumasi_isaretleri": ["captcha", "just a moment..."],
    "bot_korumasi_max_uzunluk": 20000,
}


class SahteYanit:
    def __init__(self, url: str, kod: int = 200, govde: str = "", tur: str = "text/html"):
        self.url, self.status_code = url, kod
        self.content = govde.encode("utf-8")
        self.text = govde
        self.headers = {"Content-Type": tur}


class SahteOturum:
    """URL → yanıt (veya fırlatılacak hata) eşlemesiyle çalışan sahte `requests.Session`."""

    def __init__(self, sayfalar: dict):
        self.sayfalar, self.headers, self.istekler = sayfalar, {}, []

    def get(self, url, timeout=None, allow_redirects=True):
        self.istekler.append(url)
        cevap = self.sayfalar.get(url, SahteYanit(url, 404))
        if isinstance(cevap, list):
            cevap = cevap.pop(0)
        if isinstance(cevap, Exception):
            raise cevap
        return cevap


class SahteSaat:
    def __init__(self):
        self.simdi, self.uykular = 0.0, []

    def saat(self) -> float:
        return self.simdi

    def uyku(self, sn: float) -> None:
        self.uykular.append(sn)
        self.simdi += sn


def istemci_kur(sayfalar: dict) -> tuple[Istemci, SahteOturum, SahteSaat]:
    oturum, saat = SahteOturum(sayfalar), SahteSaat()
    return Istemci(AYAR, oturum=oturum, uyku=saat.uyku, saat=saat.saat), oturum, saat


ROBOTS = "https://ornek.com/robots.txt"


def test_user_agent_ayarlardan_gelir():
    _, oturum, _ = istemci_kur({})
    assert oturum.headers["User-Agent"] == AYAR["user_agent"]


def test_ayni_alana_en_az_bes_saniye_arayla_istek():
    istemci, _, saat = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, 404),
        "https://ornek.com/a": SahteYanit("https://ornek.com/a", govde="a" * 50),
        "https://www.ornek.com/b": SahteYanit("https://www.ornek.com/b", govde="b" * 50),
    })
    assert istemci.getir("https://ornek.com/a").erisim_durumu == TAMAM
    assert istemci.getir("https://www.ornek.com/b").erisim_durumu == TAMAM
    assert saat.uykular == [5.0, 5.0]        # robots→a ve a→b arasında


def test_farkli_alanlar_birbirini_bekletmez():
    istemci, _, saat = istemci_kur({})
    istemci.bekle("https://bir.com/x")
    istemci.bekle("https://iki.com/x")
    assert saat.uykular == []


def test_robots_yasagi_sayfayi_aldirmaz():
    istemci, oturum, _ = istemci_kur({ROBOTS: SahteYanit(ROBOTS, govde="User-agent: *\nDisallow: /gizli/\n")})
    yanit = istemci.getir("https://ornek.com/gizli/belge")
    assert yanit.erisim_durumu == ENGELLENDI and "robots" in yanit.aciklama
    assert oturum.istekler == [ROBOTS]       # sayfanın kendisi hiç istenmedi


def test_crawl_delay_daha_uzunsa_ona_uyulur():
    istemci, _, saat = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, govde="User-agent: *\nCrawl-delay: 12\n"),
        "https://ornek.com/a": SahteYanit("https://ornek.com/a", govde="x" * 50),
    })
    istemci.getir("https://ornek.com/a")
    assert saat.uykular == [12.0]


def test_403_engellendi_sayilir_ve_yeniden_denenmez():
    istemci, oturum, _ = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, 404),
        "https://ornek.com/a": SahteYanit("https://ornek.com/a", 403),
    })
    yanit = istemci.getir("https://ornek.com/a")
    assert yanit.erisim_durumu == ENGELLENDI and yanit.icerik == b""
    assert oturum.istekler.count("https://ornek.com/a") == 1


def test_bot_korumasi_sayfasi_engellendi_sayilir():
    istemci, _, _ = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, 404),
        "https://ornek.com/a": SahteYanit("https://ornek.com/a", govde="<title>Just a moment...</title>"),
    })
    assert istemci.getir("https://ornek.com/a").erisim_durumu == ENGELLENDI


def test_404_bulunamadi():
    istemci, _, _ = istemci_kur({ROBOTS: SahteYanit(ROBOTS, 404)})
    assert istemci.getir("https://ornek.com/yok").erisim_durumu == BULUNAMADI


def test_gecici_hata_uc_kez_denenir_sonra_basarir():
    url = "https://ornek.com/a"
    istemci, oturum, _ = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, 404),
        url: [requests.ConnectionError("koptu"), SahteYanit(url, 503), SahteYanit(url, govde="tamam" * 20)],
    })
    assert istemci.getir(url).erisim_durumu == TAMAM
    assert oturum.istekler.count(url) == 3


def test_uc_denemeden_sonra_hata_doner():
    url = "https://ornek.com/a"
    istemci, oturum, _ = istemci_kur({
        ROBOTS: SahteYanit(ROBOTS, 404),
        url: [SahteYanit(url, 500), SahteYanit(url, 500), SahteYanit(url, 500)],
    })
    assert istemci.getir(url).erisim_durumu == HATA
    assert oturum.istekler.count(url) == 3


def test_alan_adi_ve_normallestirme():
    assert alan_adi("https://WWW.Ornek.com/x") == "ornek.com"
    a = url_normallestir("https://www.ornek.com/ai-policy/?utm_source=x#bolum")
    b = url_normallestir("http://ornek.com/ai-policy")
    assert a == b == "ornek.com/ai-policy"


def test_turkce_karakterli_url_kodlanir():
    kodlu = url_kodla("https://www.tgc.org.tr/bildirgeler/türkiye-gazetecilik/bildirge.html")
    assert kodlu == "https://www.tgc.org.tr/bildirgeler/t%C3%BCrkiye-gazetecilik/bildirge.html"
    assert url_kodla(kodlu) == kodlu         # iki kez kodlamaz
