"""Arşiv dosya adları ve belge kimlikleri.

Biçim: `[BelgeID]_[Kurum]_[kısa-ad]_[YYYY-AA-GG].[uzantı]`
"""
from __future__ import annotations

import re
import unicodedata

# NFKD ayrıştırmasıyla çözülmeyen harfler (Türkçe ı ve bazı Avrupa dilleri)
OZEL_HARFLER = str.maketrans({
    "ı": "i", "İ": "I", "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S",
    "ö": "o", "Ö": "O", "ü": "u", "Ü": "U", "ç": "c", "Ç": "C",
    "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O", "ß": "ss", "đ": "d", "Đ": "D", "ł": "l", "Ł": "L",
})


def ascii_cevir(metin: str) -> str:
    """Türkçe ve diğer aksanlı harfleri ASCII karşılıklarına çevirir (ğ→g, ş→s, ı→i ...)."""
    ayrik = unicodedata.normalize("NFKD", metin.translate(OZEL_HARFLER))
    return ayrik.encode("ascii", "ignore").decode("ascii")


def parca_temizle(metin: str) -> str:
    """Dosya adının bir parçasını hazırlar: ASCII, boşluk yerine tire, özel işaret yok."""
    tireli = re.sub(r"[^A-Za-z0-9]+", "-", ascii_cevir(metin))
    return tireli.strip("-")


def dosya_adi(belge_id: str, kurum: str, kisa_ad: str, tarih: str, uzanti: str) -> str:
    """Arşiv dosya adını üretir. `tarih` YYYY-AA-GG biçiminde olmalıdır."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarih):
        raise ValueError(f"Tarih YYYY-AA-GG biçiminde olmalı: {tarih!r}")
    parcalar = [belge_id, parca_temizle(kurum), parca_temizle(kisa_ad), tarih]
    return "_".join(p for p in parcalar if p) + "." + uzanti.lstrip(".")


def sonraki_kimlik(mevcut_kimlikler: list[str], grup: str) -> str:
    """Bir grup (K veya M) için sıradaki boş belge kimliğini verir (ör. K29'dan sonra K30)."""
    sayilar = [int(m.group(1)) for k in mevcut_kimlikler if (m := re.fullmatch(rf"{grup}(\d+)[a-z]?", k))]
    return f"{grup}{max(sayilar, default=0) + 1:02d}"
