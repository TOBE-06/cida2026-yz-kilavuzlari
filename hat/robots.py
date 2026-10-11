"""robots.txt kararları.

robots.txt: sitenin otomatik programlara hangi sayfaları yasakladığını yazdığı dosya.
Bu modül dosyayı yorumlar; indirme işini `hat/ag.py` yapar. Yorumlama için `protego`
kullanılır (joker karakterli `*` ve `$` kurallarını da anlar).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from protego import Protego

# RFC 9309: 4xx (401/403 dahil değil) "kural yok" sayılır; erişilemeyen robots.txt "tümü yasak" sayılır.
YASAK_SAYILAN_KODLAR = {401, 403}


@dataclass
class RobotsKurali:
    """Tek bir alan adının robots.txt kuralları."""

    ayristirici: Protego | None = None
    tumu_yasak: bool = False
    aciklama: str = ""
    site_haritalari: list[str] = field(default_factory=list)

    def izinli(self, user_agent: str, url: str) -> bool:
        """Verilen User-Agent bu URL'yi alabilir mi?"""
        if self.tumu_yasak:
            return False
        if self.ayristirici is None:
            return True
        return self.ayristirici.can_fetch(url, user_agent)

    def bekleme_sn(self, user_agent: str) -> float | None:
        """Sitenin istediği bekleme süresi (Crawl-delay) varsa döndürür."""
        if self.ayristirici is None:
            return None
        gecikme = self.ayristirici.crawl_delay(user_agent)
        return float(gecikme) if gecikme is not None else None


def kural_olustur(durum_kodu: int | None, metin: str) -> RobotsKurali:
    """robots.txt isteğinin sonucundan kural nesnesi üretir.

    - 200: dosya yorumlanır.
    - 401/403 veya ağ hatası/5xx: temkinli davranılır, tüm site yasak sayılır.
    - Diğer 4xx (ör. 404): robots.txt yok, kısıtlama yok.
    """
    if durum_kodu is None or durum_kodu >= 500:
        return RobotsKurali(tumu_yasak=True, aciklama="robots.txt alınamadı")
    if durum_kodu in YASAK_SAYILAN_KODLAR:
        return RobotsKurali(tumu_yasak=True, aciklama=f"robots.txt {durum_kodu} döndürdü")
    if durum_kodu >= 400:
        return RobotsKurali(aciklama="robots.txt yok")
    ayristirici = Protego.parse(metin)
    return RobotsKurali(
        ayristirici=ayristirici, aciklama="robots.txt okundu",
        site_haritalari=list(ayristirici.sitemaps),
    )
