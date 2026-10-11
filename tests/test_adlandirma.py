"""Dosya adlandırma ve belge kimliği testleri."""
import pytest

from hat.adlandirma import ascii_cevir, dosya_adi, parca_temizle, sonraki_kimlik


def test_turkce_karakterler_asciiye_cevrilir():
    assert ascii_cevir("ğüşıöç ĞÜŞİÖÇ") == "gusioc GUSIOC"


def test_diger_dillerin_aksanlari():
    assert ascii_cevir("Pressenævnet Núcleo Estadão Süddeutsche") == "Pressenaevnet Nucleo Estadao Suddeutsche"


def test_bosluk_tire_olur_ozel_isaretler_atilir():
    assert parca_temizle("Türkiye Gazeteciler Cemiyeti (TGC)") == "Turkiye-Gazeteciler-Cemiyeti-TGC"


def test_protokoldeki_ornek_ad():
    assert dosya_adi("K01", "Associated Press", "AP", "2026-10-12", "pdf") == "K01_Associated-Press_AP_2026-10-12.pdf"


def test_gecersiz_tarih_reddedilir():
    with pytest.raises(ValueError):
        dosya_adi("K01", "AP", "AP", "12.10.2026", "pdf")


def test_siradaki_kimlik():
    mevcut = ["K01", "K29", "K03a", "M18"]
    assert sonraki_kimlik(mevcut, "K") == "K30"
    assert sonraki_kimlik(mevcut, "M") == "M19"
