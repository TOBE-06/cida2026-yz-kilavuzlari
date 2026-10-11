"""Ayar dosyalarını okur ve proje içi yolları üretir.

Betiklerde sabit değer kullanılmaz; her parametre buradan okunur.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

KOK: Path = Path(__file__).resolve().parents[1]
AYAR_DOSYASI: Path = KOK / "config" / "ayarlar.yaml"


@lru_cache(maxsize=1)
def ayarlari_yukle() -> dict[str, Any]:
    """`config/ayarlar.yaml` dosyasını sözlük olarak döndürür."""
    with AYAR_DOSYASI.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def yol(ad: str) -> Path:
    """`yollar` bölümündeki bir klasörün tam yolunu döndürür (ör. `yol("log")`)."""
    return KOK / ayarlari_yukle()["yollar"][ad]


@lru_cache(maxsize=1)
def eleme_olcutleri() -> dict[str, Any]:
    """Eleme ölçütlerini (`config/eleme_olcutleri.yaml`) okur. Form ve yönerge buradan üretilir."""
    with (KOK / "config" / "eleme_olcutleri.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def anahtar_sozcukler() -> dict[str, Any]:
    """Çok dilli anahtar sözcük listesini (`data/seed/anahtar_sozcukler.yaml`) okur."""
    with (yol("seed") / "anahtar_sozcukler.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)
