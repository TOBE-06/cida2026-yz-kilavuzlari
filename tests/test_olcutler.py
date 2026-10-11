"""Eleme ölçütleri dosyasının iç tutarlılığı."""
from hat.ayarlar import eleme_olcutleri

OLCUT = eleme_olcutleri()


def test_karar_secenekleri():
    assert OLCUT["karar"] == ["Dahil", "Hariç", "Belirsiz", "Ertelendi"]


def test_dahil_ve_dislama_kodlari_tam():
    assert list(OLCUT["dahil_etme"]) == ["D1", "D2", "D3", "D4"]
    assert list(OLCUT["dislama"]) == [f"E{i}" for i in range(1, 9)]


def test_eleme_sirasindaki_her_kod_tanimli_ve_bir_kez_geciyor():
    siradaki = [kod for adim in OLCUT["eleme_sirasi"] for kod in adim.get("kodlar", [])]
    assert sorted(siradaki) == sorted(OLCUT["dislama"])


def test_son_adim_dahil_ve_doldurulacak_alanlar_siniflamayla_uyumlu():
    son = OLCUT["eleme_sirasi"][-1]
    assert son["asama"] == "Dahil"
    serbest_metin = {"ulke", "kodlama_kapsami"}
    assert set(son["sonra_doldurulacak"]) - serbest_metin == set(OLCUT["siniflama"])


def test_siniflama_kodlari():
    s = OLCUT["siniflama"]
    assert list(s["grup"]) == ["K", "M"]
    assert list(s["aktor_turu"]) == [1, 2, 3, 4, 5, 6, 7]
    assert list(s["bolge"]) == [1, 2, 3, 4, 5]
    assert list(s["belge_bicimi"]) == [1, 2]
    assert list(s["belge_statusu"]) == [1, 2, 3, 4, 5]


def test_sinir_durumlarin_hepsinde_durum_ve_kural_var():
    assert len(OLCUT["sinir_durumlar"]) == 10
    assert all(d["durum"] and d["kural"] for d in OLCUT["sinir_durumlar"])
