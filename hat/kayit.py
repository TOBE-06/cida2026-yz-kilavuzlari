"""Günlük tutma, CSV kayıtları ve dosya özeti yardımcıları."""
from __future__ import annotations

import csv
import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from hat.ayarlar import yol

HATA_SUTUNLARI = ["zaman_utc", "asama", "url", "hata_turu", "mesaj"]
ARAMA_SUTUNLARI = ["zaman_utc", "arac", "sorgu", "sonuc_sayisi", "eklenen_aktor", "not"]


def utc_simdi() -> str:
    """Şu anki zamanı UTC ISO 8601 biçiminde döndürür (ör. `2026-10-12T09:15:03Z`)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gunluk_kur(asama: str, log_klasoru: Path | None = None) -> logging.Logger:
    """Bir aşama için hem ekrana hem `logs/<asama>.log` dosyasına yazan günlükçü kurar."""
    klasor = log_klasoru or yol("log")
    klasor.mkdir(parents=True, exist_ok=True)
    gunluk = logging.getLogger(asama)
    if gunluk.handlers:
        return gunluk
    gunluk.setLevel(logging.INFO)
    bicim = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    bicim.converter = lambda *_: datetime.now(timezone.utc).timetuple()
    for isleyici in (
        logging.FileHandler(klasor / f"{asama}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ):
        isleyici.setFormatter(bicim)
        gunluk.addHandler(isleyici)
    return gunluk


def csv_satir_ekle(dosya: Path, sutunlar: list[str], satir: dict[str, object]) -> None:
    """CSV dosyasının sonuna bir satır ekler; dosya yoksa başlık satırıyla oluşturur."""
    dosya.parent.mkdir(parents=True, exist_ok=True)
    yeni = not dosya.exists()
    with dosya.open("a", encoding="utf-8", newline="") as f:
        yazici = csv.DictWriter(f, fieldnames=sutunlar)
        if yeni:
            yazici.writeheader()
        yazici.writerow({s: satir.get(s, "") for s in sutunlar})


def hata_yaz(asama: str, url: str, hata_turu: str, mesaj: str, log_klasoru: Path | None = None) -> None:
    """Bir hatayı `logs/hatalar.csv` dosyasına kaydeder."""
    satir = {"zaman_utc": utc_simdi(), "asama": asama, "url": url, "hata_turu": hata_turu, "mesaj": mesaj}
    csv_satir_ekle((log_klasoru or yol("log")) / "hatalar.csv", HATA_SUTUNLARI, satir)


def arama_yaz(
    arac: str, sorgu: str, sonuc_sayisi: int, eklenen_aktor: str = "", not_: str = "",
    log_klasoru: Path | None = None,
) -> None:
    """Yapılan bir web aramasını `logs/arama_gunlugu.csv` dosyasına kaydeder."""
    satir = {
        "zaman_utc": utc_simdi(), "arac": arac, "sorgu": sorgu,
        "sonuc_sayisi": sonuc_sayisi, "eklenen_aktor": eklenen_aktor, "not": not_,
    }
    csv_satir_ekle((log_klasoru or yol("log")) / "arama_gunlugu.csv", ARAMA_SUTUNLARI, satir)


def sha256_dosya(dosya: Path) -> str:
    """Diskteki dosyanın SHA-256 özetini (dijital parmak izi) hesaplar."""
    ozet = hashlib.sha256()
    with dosya.open("rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            ozet.update(parca)
    return ozet.hexdigest()
