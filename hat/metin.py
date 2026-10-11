"""Metin çıkarımı ve çok dilli anahtar sözcük eşleştirme.

Eşleştirme kuralları (protokol §8 uygulaması):
- Kısa terimler (ai, ki, ia, yz, llm) yalnızca tam sözcük olarak eşleşir ("email" içindeki "ai" sayılmaz).
- `-` ile biten terimler (ör. `ai-`) sözcük başında aranır ("AI-generated").
- `-` ile başlayan terimler (ör. `-malı`) sözcük sonunda aranır ("yapılmalı").
- Diğer terimler sözcük başında aranır ve ek alabilir ("guideline" → "guidelines").
"""
from __future__ import annotations

import io
import re
from collections import Counter
from functools import lru_cache
from typing import Any
from urllib.parse import unquote

import trafilatura
from bs4 import BeautifulSoup
from pypdf import PdfReader

from hat.ayarlar import anahtar_sozcukler, ayarlari_yukle


def kucult(metin: str) -> str:
    """Metni karşılaştırma için küçük harfe çevirir (Türkçe İ dahil) ve boşlukları sadeleştirir."""
    kucuk = metin.replace("İ", "i").lower().replace("̇", "")
    return re.sub(r"\s+", " ", kucuk)


def url_metni(url: str) -> str:
    """URL'yi sözcüklere ayırır: `/ai-policy/` → `ai policy`."""
    return re.sub(r"[\W_]+", " ", kucult(unquote(url))).strip()


@lru_cache(maxsize=None)
def terim_deseni(terim: str, kisa_uzunluk: int) -> re.Pattern[str]:
    """Bir anahtar sözcük için modül başındaki kurallara uygun arama deseni üretir."""
    t = kucult(terim).strip()
    if t.startswith("-"):
        return re.compile(re.escape(t[1:]) + r"(?!\w)")
    if t.endswith("-"):
        return re.compile(r"(?<!\w)" + re.escape(t))
    if len(t) <= kisa_uzunluk:
        return re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)")
    return re.compile(r"(?<!\w)" + re.escape(t))


def _kisa_uzunluk() -> int:
    return int(ayarlari_yukle()["kesif"]["kisa_terim_uzunlugu"])


def terim_say(metin: str, terimler: list[str]) -> Counter[str]:
    """Metinde her terimin kaç kez geçtiğini sayar (yalnızca geçenler döner)."""
    kucuk = kucult(metin)
    sayac: Counter[str] = Counter()
    for terim in terimler:
        adet = len(terim_deseni(terim, _kisa_uzunluk()).findall(kucuk))
        if adet:
            sayac[terim.strip()] = adet
    return sayac


def tum_terimler(tur: str, sozluk: dict[str, Any] | None = None) -> list[str]:
    """Bütün dillerdeki terimleri tek listede toplar. `tur`: yz_terimi, belge_terimi, normatif_isaret."""
    sozluk = sozluk or anahtar_sozcukler()
    gorulen: dict[str, None] = {}
    for dil in sozluk["diller"].values():
        for terim in dil.get(tur, []):
            gorulen.setdefault(terim.strip(), None)
    return list(gorulen)


@lru_cache(maxsize=None)
def _birlesik_yz_deseni() -> re.Pattern[str]:
    """Tüm YZ terimlerini tek desende birleştirir (çok sayıda adresi hızlı süzmek için)."""
    return re.compile("|".join(terim_deseni(t, _kisa_uzunluk()).pattern for t in tum_terimler("yz_terimi")))


def yz_izi_var(url: str) -> bool:
    """Hızlı ön süzgeç: adreste herhangi bir YZ terimi veya YZ türü URL kalıbı geçiyor mu?"""
    if _birlesik_yz_deseni().search(url_metni(url)):
        return True
    return bool(url_kalibi_eslesmeleri(url)[0])


def etik_kod_eslesmesi(url: str, baglanti_metni: str = "") -> list[str]:
    """Adres veya bağlantı metninde geçen genel etik kod terimlerini döndürür (M grubu için)."""
    terimler = ayarlari_yukle()["kesif"]["etik_kod_terimleri"]
    return list(terim_say(url_metni(url) + " | " + baglanti_metni, terimler))


def url_kalibi_eslesmeleri(url: str) -> tuple[list[str], list[str]]:
    """URL'de geçen kalıpları (YZ türü, belge türü) olarak ikiye ayırıp döndürür."""
    kucuk = kucult(unquote(url))
    belge_turu = set(ayarlari_yukle()["kesif"]["belge_turu_url_kaliplari"])
    eslesen = [k for k in dict.fromkeys(anahtar_sozcukler()["url_kaliplari"]) if k in kucuk]
    return [k for k in eslesen if k not in belge_turu], [k for k in eslesen if k in belge_turu]


def aday_eslesmesi(url: str, baslik: str = "", baglanti_metni: str = "") -> dict[str, list[str]]:
    """URL, başlık ve bağlantı metninde eşleşen YZ ve belge terimlerini döndürür."""
    birlesik = " | ".join([url_metni(url), baslik, baglanti_metni])
    yz_kalip, belge_kalip = url_kalibi_eslesmeleri(url)
    yz = list(terim_say(birlesik, tum_terimler("yz_terimi"))) + yz_kalip
    belge = list(terim_say(birlesik, tum_terimler("belge_terimi"))) + belge_kalip
    return {"yz": yz, "belge": belge}


def aday_mi(url: str, baslik: str = "", baglanti_metni: str = "") -> bool:
    """Aday olma koşulu: en az `min_yz_terimi` YZ terimi ve `min_belge_terimi` belge terimi."""
    kesif = ayarlari_yukle()["kesif"]
    e = aday_eslesmesi(url, baslik, baglanti_metni)
    return len(e["yz"]) >= kesif["min_yz_terimi"] and len(e["belge"]) >= kesif["min_belge_terimi"]


# --- metin çıkarımı ---------------------------------------------------------

def html_metin(html: str) -> str:
    """HTML sayfasının ana metnini çıkarır (menü, altbilgi, reklam ayıklanır)."""
    ana = trafilatura.extract(html, include_comments=False, include_tables=True, favor_recall=True)
    if ana:
        return ana.strip()
    corba = BeautifulSoup(html, "lxml")
    for etiket in corba(["script", "style", "noscript"]):
        etiket.decompose()
    return re.sub(r"\n\s*\n+", "\n\n", corba.get_text("\n")).strip()


def html_baslik(html: str) -> str:
    """Sayfa başlığını (`<title>`, yoksa ilk `<h1>`) döndürür."""
    corba = BeautifulSoup(html, "lxml")
    for etiket in (corba.title, corba.find("h1")):
        if etiket and etiket.get_text(strip=True):
            return re.sub(r"\s+", " ", etiket.get_text()).strip()
    return ""


def pdf_metin(icerik: bytes) -> str:
    """PDF dosyasının metnini sayfa sayfa çıkarır."""
    okuyucu = PdfReader(io.BytesIO(icerik))
    return "\n\n".join((sayfa.extract_text() or "").strip() for sayfa in okuyucu.pages).strip()


def dil_tahmin(metin: str, html: str = "") -> str:
    """Belgenin dilini tahmin eder: önce HTML `lang` özniteliği, yoksa en çok terimi eşleşen dil."""
    if html:
        kok = BeautifulSoup(html, "lxml").find("html")
        if kok and kok.get("lang"):
            return str(kok["lang"]).split("-")[0].lower()
    puanlar: Counter[str] = Counter()
    for kod, dil in anahtar_sozcukler()["diller"].items():
        terimler = dil.get("normatif_isaret", []) + dil.get("belge_terimi", []) + dil.get("yz_terimi", [])
        puanlar[kod] = sum(terim_say(metin, terimler).values())
    en_iyi = puanlar.most_common(1)
    return en_iyi[0][0] if en_iyi and en_iyi[0][1] > 0 else "bilinmiyor"
