"""robots.txt karar testleri."""
from hat.robots import kural_olustur

UA = "CIDA2026-AcademicResearch/1.0 (non-commercial research)"

ORNEK = """\
User-agent: *
Disallow: /private/
Crawl-delay: 12
Sitemap: https://ornek.com/sitemap.xml

User-agent: CIDA2026-AcademicResearch
Disallow: /yasak/
"""


def test_genel_kural_uygulanir():
    kural = kural_olustur(200, "User-agent: *\nDisallow: /private/\n")
    assert kural.izinli(UA, "https://ornek.com/about/ai-policy")
    assert not kural.izinli(UA, "https://ornek.com/private/x")


def test_bize_ozel_kural_oncelikli():
    kural = kural_olustur(200, ORNEK)
    assert not kural.izinli(UA, "https://ornek.com/yasak/belge")
    assert kural.izinli(UA, "https://ornek.com/private/x")


def test_site_haritasi_ve_bekleme_okunur():
    kural = kural_olustur(200, "User-agent: *\nCrawl-delay: 12\nSitemap: https://ornek.com/sitemap.xml\n")
    assert kural.site_haritalari == ["https://ornek.com/sitemap.xml"]
    assert kural.bekleme_sn(UA) == 12.0


def test_tum_botlar_yasaksa_izin_yok():
    assert not kural_olustur(200, "User-agent: *\nDisallow: /\n").izinli(UA, "https://ornek.com/")


def test_robots_yoksa_serbest():
    assert kural_olustur(404, "").izinli(UA, "https://ornek.com/her/sey")


def test_robots_403_veya_erisilemezse_temkinli():
    assert not kural_olustur(403, "").izinli(UA, "https://ornek.com/")
    assert not kural_olustur(None, "").izinli(UA, "https://ornek.com/")
    assert not kural_olustur(503, "").izinli(UA, "https://ornek.com/")
