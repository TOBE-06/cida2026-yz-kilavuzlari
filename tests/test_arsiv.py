"""Arşivleme betiğinin ağdan bağımsız parçaları: kimlik atama ve adlandırma."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

from hat.ayarlar import ayarlari_yukle

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("arsiv_betigi", KOK / "scripts" / "04_arsivle.py")
betik = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(betik)


def test_mevcut_arsiv_dosya_adi_cozulur():
    m = betik.MEVCUT_AD_DESENI.match("M13_GDA ve Turkiye Basin Konseyleri_Ohri Bildirgesi_2026-09-21.pdf")
    assert m.groups() == ("M13", "GDA ve Turkiye Basin Konseyleri", "Ohri Bildirgesi", "2026-09-21")
    assert betik.MEVCUT_AD_DESENI.match("rastgele.pdf") is None


def test_kisa_ad():
    assert betik.kisa_ad_uret("Svenska Journalistförbundet (SJF)") == "SJF"
    assert betik.kisa_ad_uret("Kosova Basın Konseyi") == "KBK"
    assert betik.kisa_ad_uret("PBS") == "PBS" and betik.kisa_ad_uret("Impress (İngiltere)") == "Impress"


def test_kimlik_atama_mevcut_korunur_yeni_siradaki_numarayi_alir():
    dahil = pd.DataFrame([
        {"aday_id": "AD0001", "mevcut_belge": "K03", "birlestir": "", "grup": "K"},
        {"aday_id": "AD0002", "mevcut_belge": "K03", "birlestir": "", "grup": "K"},
        {"aday_id": "AD0003", "mevcut_belge": "", "birlestir": "", "grup": "K"},
        {"aday_id": "AD0004", "mevcut_belge": "", "birlestir": "AD0003", "grup": "K"},
        {"aday_id": "AD0005", "mevcut_belge": "", "birlestir": "", "grup": "M"},
        {"aday_id": "AD0006", "mevcut_belge": "M09", "birlestir": "", "grup": "M"},
        {"aday_id": "AD0007", "mevcut_belge": "", "birlestir": "AD0009", "grup": "M"},
        {"aday_id": "AD0009", "mevcut_belge": "", "birlestir": "", "grup": "M"},
        {"aday_id": "AD0008", "mevcut_belge": "", "birlestir": "AD0006", "grup": "M"},
    ])
    ayarlar = ayarlari_yukle() | {"arsiv": ayarlari_yukle()["arsiv"] | {"kimlik_dosyasi": "_test_yok.csv"}}
    sonuc = betik.kimlikleri_ata(dahil, ayarlar, yaz=False).set_index("aday_id")
    assert (sonuc.loc["AD0001", "belge_id"], sonuc.loc["AD0001", "parca"]) == ("K03", "a")
    assert (sonuc.loc["AD0002", "belge_id"], sonuc.loc["AD0002", "parca"]) == ("K03", "b")
    assert (sonuc.loc["AD0003", "belge_id"], sonuc.loc["AD0003", "parca"]) == ("K30", "a")
    assert (sonuc.loc["AD0004", "belge_id"], sonuc.loc["AD0004", "parca"]) == ("K30", "b")
    assert (sonuc.loc["AD0005", "belge_id"], sonuc.loc["AD0005", "parca"]) == ("M19", "")
    assert (sonuc.loc["AD0006", "belge_id"], sonuc.loc["AD0006", "parca"]) == ("M09", "a")   # sonradan parça eklendi
    assert (sonuc.loc["AD0008", "belge_id"], sonuc.loc["AD0008", "parca"]) == ("M09", "b")
    assert (sonuc.loc["AD0009", "belge_id"], sonuc.loc["AD0009", "parca"]) == ("M20", "a")   # ana metin her zaman "a"
    assert (sonuc.loc["AD0007", "belge_id"], sonuc.loc["AD0007", "parca"]) == ("M20", "b")
