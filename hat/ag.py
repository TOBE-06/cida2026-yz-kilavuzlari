"""Tüm ağ isteklerinin geçtiği tek kapı.

Her istekte sırasıyla: robots.txt kontrolü, aynı alan adına en az bekleme süresi,
ayarlardaki User-Agent, zaman aşımı ve üstel geri çekilmeli yeniden deneme uygulanır.
Engellenen sayfalar (403, bot koruması vb.) zorlanmaz; `engellendi` olarak döner.
"""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from hat.kayit import utc_simdi
from hat.robots import RobotsKurali, kural_olustur

TAMAM, ENGELLENDI, BULUNAMADI, HATA = "tamam", "engellendi", "bulunamadi", "hata"
IZLEME_PARAMETRELERI = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")


class GeciciHata(Exception):
    """Yeniden denenebilir hata (bağlantı sorunu veya 5xx yanıtı)."""


@dataclass
class Yanit:
    """Bir isteğin sonucu."""

    istenen_url: str
    son_url: str
    durum_kodu: int | None
    icerik: bytes
    icerik_turu: str
    erisim_durumu: str
    aciklama: str
    zaman_utc: str

    @property
    def metin(self) -> str:
        """İçeriği metin olarak döndürür: önce sunucunun bildirdiği kodlama, sonra UTF-8, sonra Windows-1252."""
        bildirilen = re.search(r"charset=([\w-]+)", self.icerik_turu, flags=re.I)
        for kodlama in ([bildirilen.group(1)] if bildirilen else []) + ["utf-8"]:
            try:
                return self.icerik.decode(kodlama)
            except (UnicodeDecodeError, LookupError):
                continue
        return self.icerik.decode("cp1252", errors="replace")

    @property
    def html_mi(self) -> bool:
        return "html" in self.icerik_turu.lower() or self.icerik.lstrip()[:1] == b"<" and not self.pdf_mi

    @property
    def pdf_mi(self) -> bool:
        return "pdf" in self.icerik_turu.lower() or self.icerik[:5] == b"%PDF-"


def alan_adi(url: str) -> str:
    """URL'nin alan adını küçük harfle ve `www.` olmadan döndürür."""
    ag_konumu = (urlsplit(url).hostname or "").lower()
    return ag_konumu[4:] if ag_konumu.startswith("www.") else ag_konumu


def url_kodla(url: str) -> str:
    """URL'deki ASCII dışı karakterleri (ör. Türkçe harfler) yüzde kodlamasına çevirir."""
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%:@!$&'()*+,;=~"),
                       quote(p.query, safe="=&%:@!$'()*+,;/?~"), ""))


def url_normallestir(url: str) -> str:
    """Mükerrer URL'leri birleştirmek için karşılaştırma anahtarı üretir.

    Şema ve `www.` atılır, alan adı küçültülür, izleme parametreleri ve `#...` silinir,
    sondaki `/` kaldırılır.
    """
    p = urlsplit(url_kodla(url))
    sorgu = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith(IZLEME_PARAMETRELERI)]
    yol = p.path.rstrip("/")
    return alan_adi(url) + yol + ("?" + urlencode(sorted(sorgu)) if sorgu else "")


class Istemci:
    """Kibar HTTP istemcisi. Hattaki bütün istekler bu sınıftan geçer."""

    def __init__(
        self,
        ag_ayarlari: dict[str, Any],
        oturum: requests.Session | None = None,
        uyku: Callable[[float], None] = time.sleep,
        saat: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ayar = ag_ayarlari
        self.user_agent: str = ag_ayarlari["user_agent"]
        self.oturum = oturum or requests.Session()
        self.oturum.headers.update({"User-Agent": self.user_agent})
        self._uyku, self._saat = uyku, saat
        self._son_istek: dict[str, float] = {}
        self._robots: dict[str, RobotsKurali] = {}
        self._kilit = threading.Lock()
        self._alan_kilitleri: dict[str, threading.Lock] = {}

    # --- bekleme ve robots ---------------------------------------------------

    def bekle(self, url: str) -> None:
        """Aynı alan adına iki istek arasında en az bekleme süresi bırakır.

        Birden çok iş parçacığı aynı anda çalışsa bile aynı alan adına giden isteklerin
        başlangıçları arasında en az bu süre olur; farklı alan adları birbirini bekletmez.
        """
        alan = alan_adi(url)
        sure = float(self.ayar["alan_basi_bekleme_sn"])
        kural = self._robots.get(alan)
        if kural and (istenen := kural.bekleme_sn(self.user_agent)):
            sure = max(sure, istenen)
        with self._kilit:
            simdi = self._saat()
            onceki = self._son_istek.get(alan)
            baslangic = simdi if onceki is None else max(simdi, onceki + sure)
            self._son_istek[alan] = baslangic
        if baslangic > simdi:
            self._uyku(baslangic - simdi)

    def _alan_kilidi(self, alan: str) -> threading.Lock:
        with self._kilit:
            return self._alan_kilitleri.setdefault(alan, threading.Lock())

    def robots_kurali(self, url: str) -> RobotsKurali:
        """Alan adının robots.txt kurallarını (bir kez indirip) döndürür."""
        alan = alan_adi(url)
        with self._alan_kilidi(alan):
            if alan not in self._robots:
                p = urlsplit(url)
                robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
                try:
                    yanit = self._istek(robots_url)
                    self._robots[alan] = kural_olustur(yanit.status_code, yanit.text)
                except (GeciciHata, requests.RequestException):
                    self._robots[alan] = kural_olustur(None, "")
        return self._robots[alan]

    def izinli(self, url: str) -> bool:
        """robots.txt bu URL'ye izin veriyor mu? (`robots_txt_uy: false` ise her zaman evet)"""
        if not self.ayar.get("robots_txt_uy", True):
            return True
        return self.robots_kurali(url).izinli(self.user_agent, url)

    # --- istek ---------------------------------------------------------------

    def _tek_istek(self, url: str) -> requests.Response:
        self.bekle(url)
        try:
            yanit = self.oturum.get(url, timeout=self.ayar["zaman_asimi_sn"], allow_redirects=True)
        except (requests.ConnectionError, requests.Timeout) as hata:
            raise GeciciHata(str(hata)) from hata
        if yanit.status_code >= 500:
            raise GeciciHata(f"HTTP {yanit.status_code}")
        return yanit

    def _istek(self, url: str) -> requests.Response:
        """İsteği üstel geri çekilmeyle (her denemede daha uzun bekleyerek) yeniden dener."""
        deneyici = Retrying(
            stop=stop_after_attempt(int(self.ayar["yeniden_deneme"])),
            wait=wait_exponential(multiplier=2, max=30),
            retry=retry_if_exception_type(GeciciHata),
            sleep=self._uyku,
            reraise=True,
        )
        return deneyici(self._tek_istek, url)

    def _bot_korumasi(self, yanit: requests.Response) -> bool:
        if len(yanit.content) > int(self.ayar["bot_korumasi_max_uzunluk"]):
            return False
        govde = yanit.content.decode("utf-8", errors="ignore").lower()
        return any(isaret in govde for isaret in self.ayar["bot_korumasi_isaretleri"])

    def getir(self, url: str) -> Yanit:
        """Bir URL'yi tüm etik kurallarla indirir. Hata fırlatmaz; sonucu `Yanit` olarak döndürür."""
        url = url_kodla(url)

        def sonuc(durum: str, aciklama: str, yanit: requests.Response | None = None) -> Yanit:
            return Yanit(
                istenen_url=url, son_url=yanit.url if yanit is not None else url,
                durum_kodu=yanit.status_code if yanit is not None else None,
                icerik=yanit.content if yanit is not None and durum == TAMAM else b"",
                icerik_turu=yanit.headers.get("Content-Type", "") if yanit is not None else "",
                erisim_durumu=durum, aciklama=aciklama, zaman_utc=utc_simdi(),
            )

        if not self.izinli(url):
            return sonuc(ENGELLENDI, "robots.txt izin vermiyor")
        try:
            yanit = self._istek(url)
        except GeciciHata as hata:
            return sonuc(HATA, f"yeniden denemeler tükendi: {hata}")
        except requests.RequestException as hata:
            return sonuc(HATA, f"{type(hata).__name__}: {hata}")
        if alan_adi(yanit.url) != alan_adi(url) and not self.izinli(yanit.url):
            return sonuc(ENGELLENDI, "yönlendirilen adres robots.txt ile yasak", yanit)
        if yanit.status_code in self.ayar["engel_durum_kodlari"]:
            return sonuc(ENGELLENDI, f"HTTP {yanit.status_code}", yanit)
        if yanit.status_code in (404, 410):
            return sonuc(BULUNAMADI, f"HTTP {yanit.status_code}", yanit)
        if yanit.status_code >= 400:
            return sonuc(HATA, f"HTTP {yanit.status_code}", yanit)
        if self._bot_korumasi(yanit):
            return sonuc(ENGELLENDI, "bot koruması sayfası", yanit)
        return sonuc(TAMAM, "", yanit)
