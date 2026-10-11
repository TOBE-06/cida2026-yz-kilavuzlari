"""Ön puanlama ve araştırmacıya yardımcı işaretler.

Buradaki hiçbir işlev dahil etme/dışlama kararı vermez ve dışlama kodu önermez.
Ön puan yalnızca eleme formundaki sıralamayı belirler.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import quote

from rapidfuzz import fuzz

from hat.ag import TAMAM, Istemci, Yanit
from hat.metin import aday_eslesmesi, dil_tahmin, html_baslik, html_metin, pdf_metin, terim_say, tum_terimler


def metin_cikar(yanit: Yanit) -> tuple[str, str]:
    """İndirilen sayfadan (başlık, ana metin) çıkarır. PDF ve HTML desteklenir."""
    if yanit.pdf_mi:
        try:
            return "", pdf_metin(yanit.icerik)
        except Exception:  # bozuk veya şifreli PDF
            return "", ""
    html = yanit.metin
    return html_baslik(html), html_metin(html)


def on_puan(yz_sayisi: int, normatif_sayisi: int, baslik_eslesti: bool, ayar: dict[str, Any]) -> int:
    """Sıralama puanı (0–100): YZ terimi ve normatif işaret yoğunluğu ile başlık eşleşmesi."""
    puan = min(yz_sayisi, ayar["yz_tavan"]) * ayar["yz_agirlik"]
    puan += min(normatif_sayisi, ayar["normatif_tavan"]) * ayar["normatif_agirlik"]
    puan += ayar["baslik_eslesme_puani"] if baslik_eslesti else 0
    return int(puan)


def metin_olcumleri(url: str, baslik: str, metin: str, html: str, ayar: dict[str, Any]) -> dict[str, Any]:
    """Bir adayın metninden dil, terim sayıları, uzunluk, ön puan ve metin özetini hesaplar."""
    yz = sum(terim_say(metin, tum_terimler("yz_terimi")).values())
    normatif = sum(terim_say(metin, tum_terimler("normatif_isaret")).values())
    e = aday_eslesmesi(url, baslik)
    sade = re.sub(r"\s+", " ", metin).strip().lower()
    return {
        "dil": dil_tahmin(metin, html) if metin else "",
        "yz_terim_sayisi": yz, "normatif_isaret_sayisi": normatif, "metin_uzunlugu": len(metin),
        "on_puan": on_puan(yz, normatif, bool(e["yz"] and e["belge"]), ayar),
        "metin_ozeti": hashlib.sha256(sade.encode("utf-8")).hexdigest() if sade else "",
    }


def wayback_kopyasi(istemci: Istemci, url: str, api: str) -> str:
    """Wayback Machine'deki en yakın kopyanın adresini döndürür; yoksa veya sorgulanamazsa boş metin."""
    yanit = istemci.getir(api + quote(url, safe=""))
    if yanit.erisim_durumu != TAMAM:
        return ""
    try:
        en_yakin = json.loads(yanit.metin).get("archived_snapshots", {}).get("closest", {})
    except json.JSONDecodeError:
        return ""
    return en_yakin.get("url", "") if en_yakin.get("available") else ""


def benzer_adaylar(metinler: dict[str, str], esik: float, max_karakter: int) -> dict[str, list[str]]:
    """Aynı kurumun adayları arasında metni çok benzer olanları bulur: `aday → [benzer adaylar]`."""
    kimlikler = [k for k, m in metinler.items() if m]
    kisa = {k: metinler[k][:max_karakter] for k in kimlikler}
    sonuc: dict[str, list[str]] = {}
    for i, a in enumerate(kimlikler):
        for b in kimlikler[i + 1:]:
            if fuzz.ratio(kisa[a], kisa[b]) >= esik:
                sonuc.setdefault(a, []).append(b)
                sonuc.setdefault(b, []).append(a)
    return sonuc


def isaretler(aday: dict[str, Any], kurum_aday_sayisi: int, benzerler: list[str], yeniden_degerlendirme: bool,
              min_metin: int) -> str:
    """Araştırmacıya yardımcı gözlemleri tek hücrelik metne çevirir. Dışlama kodu içermez."""
    liste: list[str] = []
    if aday.get("mevcut_belge"):
        liste.append(f"mevcut 47 belgeden biriyle eşleşiyor: {aday['mevcut_belge']}")
    if yeniden_degerlendirme:
        liste.append("kurum dışlanan aktörler listesinde (yeniden değerlendirilecek)")
    if aday["erisim_durumu"] != TAMAM:
        liste.append(f"sayfaya erişilemedi ({aday['erisim_durumu']}: {aday.get('erisim_aciklamasi', '')})".replace(": )", ")"))
        liste.append("Wayback kopyası var" if aday.get("wayback_url") else "Wayback kopyası bulunamadı")
    else:
        if int(aday["yz_terim_sayisi"]) == 0:
            liste.append("metinde YZ terimi yok")
        if int(aday["normatif_isaret_sayisi"]) == 0:
            liste.append("metinde normatif işaret yok")
        if int(aday["metin_uzunlugu"]) < min_metin:
            liste.append(f"metin çok kısa ({aday['metin_uzunlugu']} karakter)")
    if kurum_aday_sayisi > 1:
        liste.append(f"aynı kurumdan {kurum_aday_sayisi} aday")
    if benzerler:
        liste.append("metni çok benzer aday: " + ", ".join(sorted(benzerler)))
    if aday.get("birlesen_adaylar"):
        liste.append(f"aynı adrese yönlenen adaylar birleştirildi: {aday['birlesen_adaylar']}")
    return "; ".join(liste)
