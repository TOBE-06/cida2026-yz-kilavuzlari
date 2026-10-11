"""Aşama 7 – Rapor.

`reports/veri_toplama_raporu.md` ve `reports/akis_semasi.md` dosyalarını üretir; README'ye
"Nasıl yeniden üretilir?" bölümünü (yoksa) ekler.

Rapordaki HER SAYI bu betik tarafından proje dosyalarından (evren, adaylar, eleme formu, arşiv
durumu, envanter, uzlaştırma, günlükler) hesaplanır; elle yazılmış sayı yoktur. Betik ağa çıkmaz.
"""
from __future__ import annotations

import argparse
import platform
import re
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hat import form as f  # noqa: E402
from hat.ayarlar import KOK, ayarlari_yukle, eleme_olcutleri, yol  # noqa: E402
from hat.kayit import gunluk_kur, utc_simdi  # noqa: E402

README_BASLIGI = "## Nasıl yeniden üretilir?"


def csv(dosya: Path) -> pd.DataFrame:
    return pd.read_csv(dosya, dtype=str, keep_default_na=False) if dosya.exists() else pd.DataFrame()


def tablo(basliklar: list[str], satirlar: list[list[Any]]) -> str:
    """Markdown tablosu üretir."""
    cizgi = ["| " + " | ".join(basliklar) + " |", "|" + "---|" * len(basliklar)]
    return "\n".join(cizgi + ["| " + " | ".join(str(h) for h in s) + " |" for s in satirlar])


def sayim(seri: pd.Series, sirala: bool = True) -> list[list[Any]]:
    s = seri.replace("", "(boş)").value_counts()
    return [[k, int(v)] for k, v in (s.items() if sirala else s.sort_index().items())]


def git_bilgisi() -> str:
    """Son commit kimliğini `.git` klasöründen okur (git komutuna gerek duymaz)."""
    git = KOK / ".git"
    try:
        bas = (git / "HEAD").read_text(encoding="utf-8").strip()
        if not bas.startswith("ref: "):
            return bas[:7]
        ref = bas[5:]
        if (git / ref).exists():
            return (git / ref).read_text(encoding="utf-8").strip()[:7] + f" ({ref.split('/')[-1]})"
        for satir in (git / "packed-refs").read_text(encoding="utf-8").splitlines():
            if satir.endswith(" " + ref):
                return satir.split()[0][:7] + f" ({ref.split('/')[-1]})"
    except OSError:
        pass
    return "bulunamadı"


def paket_surumleri() -> list[list[str]]:
    adlar = [s.split("==")[0] for s in (KOK / "requirements.txt").read_text(encoding="utf-8").splitlines() if "==" in s]
    return [[a, metadata.version(a)] for a in adlar]


def verileri_topla(ayarlar: dict) -> dict[str, Any]:
    """Raporun dayandığı tüm tabloları okur ve temel sayıları hesaplar."""
    ara, kesif = yol("ara"), ayarlar["kesif"]
    v: dict[str, Any] = {
        "evren": csv(ara / ayarlar["evren"]["cikti_dosyasi"]), "ek": csv(ara / ayarlar["evren"]["ek_aktor_dosyasi"]),
        "adaylar": csv(ara / kesif["cikti_dosyasi"]), "alan": csv(ara / kesif["alan_durumu_dosyasi"]),
        "puanli": csv(ara / ayarlar["puanlama"]["cikti_dosyasi"]), "arsiv": csv(ara / ayarlar["arsiv"]["durum_dosyasi"]),
        "envanter": csv(yol("envanter") / "envanter.csv"), "uzl": csv(yol("rapor") / ayarlar["uzlastirma"]["cikti_dosyasi"]),
        "manifest": csv(yol("rapor") / "manifest.csv"), "arama": csv(yol("log") / "arama_gunlugu.csv"),
        "form": f.form_oku(yol("eleme") / ayarlar["puanlama"]["form_dosyasi"]),
    }
    form, alan = v["form"], v["alan"]
    v["web_adayi"] = v["puanli"][~v["puanli"]["aday_id"].str.startswith("TOHUM-")]
    v["adressiz"] = form[form["aday_id"].str.startswith("TOHUM-")]
    v["haric"], v["dahil"] = form[form["karar"] == "Hariç"], form[form["karar"] == "Dahil"]
    v["ertelenen"], v["belirsiz"], v["kararsiz"] = form[form["karar"] == "Ertelendi"], form[form["karar"] == "Belirsiz"], form[form["karar"] == ""]
    v["ertelenen_belge"] = int((v["ertelenen"]["birlestir"] == "").sum())
    v["engelli"] = alan[alan["ana_sayfa_durumu"].str.contains("engellendi")]
    v["hatali"] = alan[alan["ana_sayfa_durumu"].str.contains("hata")]
    v["alansiz"] = alan[alan["ana_sayfa_durumu"] == ""]
    v["harita_siniri"] = int(alan["notlar"].str.contains("site haritası üst sınırı").sum())
    return v


def akis_semasi(v: dict[str, Any]) -> str:
    """PRISMA uyarlaması akış şeması (Mermaid)."""
    kodlar = ", ".join(f"{k}: {n}" for k, n in sayim(v["haric"]["dislama_kodu"], sirala=False))
    yontem = v["arsiv"]["toplama_yontemi"].value_counts().to_dict()
    satirlar = [
        "```mermaid", "flowchart TD",
        f'  A["Örnekleme çerçevesi<br/>{len(v["evren"])} aktör"] --> B["Keşifte bulunan aday adres<br/>{len(v["adaylar"])}"]',
        f'  B --> C["Aynı adrese yönlenenler birleştirildikten sonra<br/>{len(v["web_adayi"])} aday"]',
        f'  T["Önceki örneklemde olup adresi bilinmeyen belge<br/>{len(v["adressiz"])}"] --> D',
        f'  C --> D["Araştırmacının değerlendirdiği kayıt<br/>{len(v["form"]) - len(v["kararsiz"])} / {len(v["form"])}"]',
        f'  D --> H["Hariç: {len(v["haric"])}<br/>{kodlar}"]',
        f'  D --> U["Belirsiz (ikinci okuma bekliyor): {len(v["belirsiz"])}"]',
        f'  D --> R["Ölçütleri karşılayan, bu aşamada örnekleme alınmayan<br/>{len(v["ertelenen"])} aday / {v["ertelenen_belge"]} belge (araştırmacı kararı)"]',
        f'  D --> I["Dahil: {len(v["dahil"])} aday<br/>{len(v["envanter"])} belge"]',
        f'  I --> O["Siteden otomatik arşivlenen<br/>{yontem.get("otomatik", 0)} parça"]',
        f'  I --> M["Araştırmacının elle kaydettiği kopyadan arşivlenen<br/>{yontem.get("manuel", 0)} parça"]',
        "```",
    ]
    if len(v["kararsiz"]):
        satirlar.insert(-1, f'  D --> Y["Kararı girilmemiş: {len(v["kararsiz"])}"]')
    return "\n".join(satirlar)


def yontem_paragrafi(v: dict[str, Any], ayarlar: dict) -> str:
    """Yöntem bölümü için önerilen paragraf: yalnızca gerçekleşen işlemler ve dosyalardan hesaplanan sayılar."""
    env, yontem = v["envanter"], v["arsiv"]["toplama_yontemi"].value_counts().to_dict()
    kaynaklar = " ".join(v["evren"]["kaynak"])
    literatur = [ad for ad, iz in (("Becker vd., 2025", "Becker"), ("de-Lima-Santos vd., 2025", "de-Lima-Santos"),
                                   ("Sánchez-García vd., 2025", "Sánchez-García")) if iz in kaynaklar]
    degerlendirilen = len(v["form"]) - len(v["kararsiz"])
    kapsam = "tamamı" if not len(v["kararsiz"]) else f"{degerlendirilen} tanesi"
    ertelenen = (f" Ölçütleri karşılayan {v['ertelenen_belge']} belge araştırmacı kararıyla bu aşamadaki örnekleme alınmamıştır."
                 if v["ertelenen_belge"] else "")
    return (
        f"Veri toplama, belgelenmiş ve yeniden çalıştırılabilir bir Python hattıyla yürütülmüştür. Örnekleme çerçevesi, önceden "
        f"derlenen {int((v['evren']['kaynak_turu'] == 'tohum').sum())} belgelik liste, alanyazındaki belge listeleri ({'; '.join(literatur)}), "
        f"basın konseyleri dizini ve kayıtlı web aramalarıyla oluşturulmuş ve {len(v['evren'])} aktörü kapsamıştır. Aktörlerin "
        f"sitelerinde bilinen adresler, site haritası, sınırlı gezinme ve kayıtlı arama sonuçlarıyla {len(v['adaylar'])} aday adres belirlenmiştir. Taramada "
        f"robots.txt kurallarına uyulmuş, aynı alan adına gönderilen istekler arasında en az {ayarlar['ag']['alan_basi_bekleme_sn']} "
        f"saniye beklenmiş, otomatik erişimi engelleyen {len(v['engelli'])} aktörün sitesi taranmamıştır. Adaylar yapay zekâ terimi "
        f"ve normatif ifade sıklığına göre sıralanmış, {len(v['form'])} kaydın {kapsam} araştırmacı tarafından dahil etme ve dışlama "
        f"ölçütleriyle değerlendirilmiştir.{ertelenen} Analiz örneklemi {len(env)} belgeden ({int((env['grup'] == 'K').sum())} kurumsal, "
        f"{int((env['grup'] == 'M').sum())} mesleki) oluşmaktadır. Belgelerin {yontem.get('otomatik', 0)} parçası sitelerinden otomatik "
        f"olarak, {yontem.get('manuel', 0)} parçası araştırmacının elle kaydettiği kopyalardan arşivlenmiş; her dosya için erişim "
        f"tarihi ve SHA-256 özeti kaydedilmiştir."
    )


def rapor_metni(v: dict[str, Any], ayarlar: dict, olcut: dict) -> str:
    env, arsiv, uzl, form = v["envanter"], v["arsiv"], v["uzl"], v["form"]
    etiket = lambda ad, k: f"{k} – {olcut['siniflama'][ad].get(int(k), '?')}" if k.isdigit() else "(boş)"  # noqa: E731
    erisilemeyen_kaynak = v["arama"][v["arama"]["sonuc_sayisi"] == "0"]
    manuel = arsiv[arsiv["toplama_yontemi"] == "manuel"]
    gorsel = arsiv[arsiv["gorsel_kontrol_gerekli"] == "evet"]
    paragraf = yontem_paragrafi(v, ayarlar)
    b: list[str] = [
        "# Veri Toplama Raporu", "",
        "Bu rapor `scripts/07_rapor.py` tarafından otomatik üretilmiştir. Tüm sayılar proje dosyalarından hesaplanır.", "",
        "## 1. Çalıştırma bilgisi", "",
        tablo(["Bilgi", "Değer"], [["Rapor zamanı (UTC)", utc_simdi()], ["Python", platform.python_version()],
                                    ["İşletim sistemi", f"{platform.system()} {platform.machine()}"], ["Git commit", git_bilgisi()],
                                    ["Protokol", re.search(r"\*\*Protokol sürümü:\*\* (.+)", (KOK / "docs/PROJE_PROTOKOLU.md").read_text(encoding="utf-8")).group(1)],
                                    ["User-Agent", f"`{ayarlar['ag']['user_agent']}`"],
                                    ["Alan başı bekleme", f"{ayarlar['ag']['alan_basi_bekleme_sn']} sn"]]), "",
        "Paket sürümleri: " + ", ".join(f"{a} {s}" for a, s in paket_surumleri()) + ".", "",
        "## 2. Akış şeması", "", akis_semasi(v), "",
        "## 3. Örnekleme çerçevesi (Aşama 1)", "",
        f"Çerçevede **{len(v['evren'])} aktör** vardır. Web aramaları ve kaynak sayfa okumaları `logs/arama_gunlugu.csv` dosyasına "
        f"kaydedilmiştir ({len(v['arama'])} kayıt: {', '.join(f'{k} {n}' for k, n in sayim(v['arama']['arac']))}).", "",
        tablo(["Kaynak türü", "Aktör"], sayim(v["evren"]["kaynak_turu"])), "",
        f"Literatür listelerinde veya aramada görülüp araştırmacı kararıyla çerçeveye alınmayan aktör: "
        f"{int((v['ek']['evrene_al'] != 'evet').sum())} ({', '.join(v['ek'][v['ek']['evrene_al'] != 'evet']['kurum'])}).", "",
        "Erişilemeyen kaynaklar (engel aşılmamıştır):", "",
        tablo(["Adres veya sorgu", "Not"], [[s["sorgu"], s["not"]] for s in erisilemeyen_kaynak.to_dict("records")]), "",
        "## 4. Keşif (Aşama 2)", "",
        f"{len(v['alan'])} aktör işlenmiş, **{len(v['adaylar'])} aday adres** bulunmuştur.", "",
        tablo(["Bulunma yolu", "Aday"], sayim(v["adaylar"]["bulunma_yolu"])), "",
        tablo(["Aktör düzeyinde erişim", "Aktör"], [
            ["Ana sayfası alınan ve taranan", len(v["alan"]) - len(v["engelli"]) - len(v["hatali"]) - len(v["alansiz"])],
            ["Engellendi (robots.txt, HTTP 403 veya robots.txt alınamadı); taranmadı", len(v["engelli"])],
            ["Hata (sunucu hatası, yönlendirme döngüsü)", len(v["hatali"])], ["Alan adı bulunamadı", len(v["alansiz"])]]), "",
        f"Site haritası dosya üst sınırına ({ayarlar['kesif']['sitemap_max_dosya']} dosya) takılan aktör: {v['harita_siniri']}. "
        f"Gezinmede alan adı başına en fazla {ayarlar['kesif']['alan_basi_max_sayfa']} sayfa indirilmiştir. Arama katmanı, "
        f"Aşama 1 aramalarında bulunan adreslerle sınırlıdır (`data/interim/arama_sonuclari.csv`).", "",
        "Engellenen veya hata veren aktörler:", "",
        tablo(["Aktör", "Kurum", "Durum"], [[s["aktor_id"], s["kurum"], s["ana_sayfa_durumu"]]
                                             for s in pd.concat([v["engelli"], v["hatali"]]).sort_values("aktor_id").to_dict("records")]), "",
        "## 5. Ön puanlama ve eleme (Aşama 3)", "",
        f"Aynı adrese yönlenen {len(v['adaylar']) - len(v['web_adayi'])} aday birleştirilmiş, {len(v['web_adayi'])} aday puanlanmıştır. "
        f"Önceki örneklemde olup adresi bilinmeyen {len(v['adressiz'])} belge forma ayrıca eklenmiştir; form {len(form)} kayıt içerir. "
        f"Ön puan yalnızca sıralama için kullanılmıştır; kararların tamamı araştırmacıya aittir.", "",
        tablo(["Adayın sayfasına erişim", "Aday"], sayim(v["web_adayi"]["erisim_durumu"])), "",
        tablo(["Araştırmacı kararı", "Kayıt"], sayim(form["karar"])), "",
        tablo(["Dışlama kodu", "Tanım", "Kayıt"], [[k, olcut["dislama"].get(k, ""), n] for k, n in sayim(v["haric"]["dislama_kodu"], sirala=False)]), "",
        f"`Ertelendi`: dahil etme ölçütlerini karşılayan, araştırmacı kararıyla bu aşamadaki örnekleme alınmayan "
        f"{len(v['ertelenen'])} aday ({v['ertelenen_belge']} belge). Bu belgelerin arşiv dosyaları `archive/{ayarlar['arsiv']['ertelenen_klasoru']}/` altında saklanmaktadır.", "",
        "## 6. Arşiv ve envanter (Aşama 4–5)", "",
        f"Örneklem **{len(env)} belge** ({len(arsiv)} parça) içerir. Manifestte {len(v['manifest'])} dosya vardır "
        f"({v['manifest']['boyut_bayt'].astype(int).sum() / 1e6:.1f} MB); diskten hesaplanan özetlerle üst verideki özetler arasında "
        f"uyuşmazlık sayısı: {int((v['manifest']['ust_veriyle_uyumlu'] == 'hayır').sum())}.", "",
        tablo(["Toplama yöntemi", "Parça"], sayim(arsiv["toplama_yontemi"])), "",
        tablo(["Grup", "Belge"], sayim(env["grup"], sirala=False)), "",
        tablo(["Aktör türü", "Belge"], [[etiket("aktor_turu", k), n] for k, n in sayim(env["aktor_turu"], sirala=False)]), "",
        tablo(["Bölge", "Belge"], [[etiket("bolge", k), n] for k, n in sayim(env["bolge"], sirala=False)]), "",
        "Envanterde boş kalan alanlar (araştırmacı formda doldurmamıştır): " + "; ".join(
            f"`{s}` {int((env[s] == '').sum())} belge" for s in ("belge_bicimi", "belge_statusu", "kodlama_kapsami") if (env[s] == "").any()) + ".", "",
        "### Elle toplanan parçalar", "",
        tablo(["Belge", "Kurum", "Neden"], [[s["belge_id"] + s["parca"], s["kurum"], s["aciklama"].split("; manuel kopya")[0]] for s in manuel.to_dict("records")]), "",
        "### Görsel kontrol gereken parçalar", "",
        (tablo(["Belge", "Kurum"], [[s["belge_id"] + s["parca"], s["kurum"]] for s in gorsel.to_dict("records")]) if len(gorsel) else "Yok."), "",
        "Çıkarılan metin çok kısaysa veya anahtar sözcük listesindeki YZ terimlerini içermiyorsa parça işaretlenir.", "",
        "## 7. Önceki örneklemle uzlaştırma (Aşama 6)", "",
    ]
    if uzl.empty:
        b += ["`data/mevcut_arsiv/` bulunmadığı için bu aşama atlanmıştır.", ""]
    else:
        onceki = uzl[uzl["durum"] != "yeni aday"]
        b += [tablo(["Durum", "Belge"], sayim(uzl["durum"])), "",
              tablo(["Sürüm değişikliği (önceki belgeler)", "Belge"], sayim(onceki["surum_degisikligi"])), "",
              f"Benzerlik eşiği {ayarlar['uzlastirma']['benzerlik_esigi']}; altında kalan belgeler olası sürüm farkı olarak işaretlenir. "
              "Fark metin çıkarma yönteminden de kaynaklanabilir; araştırmacı kontrolü gerekir.", "",
              tablo(["Belge", "Kurum", "Benzerlik"], [[s["belge_id"], s["kurum"], s["benzerlik"]] for s in onceki[onceki["surum_degisikligi"] == "evet"].to_dict("records")]), ""]
    b += [
        "## 8. Sınırlılıklar", "",
        f"- Otomatik erişimi engelleyen {len(v['engelli'])} aktörün sitesi taranmamıştır; bu aktörlerde yalnızca bilinen adresler aday olmuştur.",
        f"- Site haritaları alan adı başına {ayarlar['kesif']['sitemap_max_dosya']} dosya ile sınırlanmıştır; {v['harita_siniri']} aktörde haritanın tamamı okunmamıştır.",
        "- Arama katmanı aktör başına ayrı `site:` sorgularıyla yürütülmemiş, Aşama 1 aramalarında bulunan adreslerle sınırlı kalmıştır.",
        "- Keşif, anahtar sözcük listesindeki dillerle sınırlıdır.",
        f"- Elle toplanan {len(manuel)} parçada erişim tarihi araştırmacının dosya adına yazdığı tarihtir; saat bilgisi yoktur.", "",
        "## 9. Yöntem bölümü için önerilen metin", "",
        f"Aşağıdaki paragraf {len(paragraf.split())} sözcüktür ve yalnızca gerçekleşen işlemleri içerir.", "", "> " + paragraf, "",
    ]
    return "\n".join(b)


README_EKI = f"""
{README_BASLIGI}

1. Ortamı kurun (Python 3.11+):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m playwright install chromium
   pytest
   ```
2. Aşamaları sırayla çalıştırın. Her betik `--help`, `--dry-run` ve `--force` destekler; var olan çıktıyı atlar.
   ```bash
   python scripts/run_pipeline.py --asama 1   # evren: data/interim/evren.csv
   python scripts/run_pipeline.py --asama 2   # keşif: data/interim/adaylar.csv
   python scripts/run_pipeline.py --asama 3   # ön puanlama ve eleme formu
   # Araştırmacı data/eleme/eleme_formu.xlsx dosyasını doldurur (karar betik tarafından verilmez)
   python scripts/run_pipeline.py --asama 4   # arşivleme: archive/K, archive/M
   python scripts/run_pipeline.py --asama 5   # envanter ve manifest
   python scripts/run_pipeline.py --asama 6   # önceki örneklemle uzlaştırma
   python scripts/run_pipeline.py --asama 7   # rapor ve akış şeması
   ```
3. Dikkat edilecekler:
   - Web sayfaları değişir; yeniden çalıştırmada aday sayıları ve arşiv özetleri farklı çıkabilir. Bu çalışmadaki
     sürümler `reports/manifest.csv` içindeki SHA-256 özetleri ve envanterdeki Wayback bağlantılarıyla belgelenmiştir.
   - Web aramaları betiklerle değil, Claude Code'un arama aracıyla yapılmış ve `logs/arama_gunlugu.csv` dosyasına
     kaydedilmiştir; bulunan aktörler `data/interim/evren_ek_aktorler.csv`, adresler `data/interim/arama_sonuclari.csv` dosyasındadır.
   - `scripts/03b_karar_aktar.py` karar vermez; araştırmacının toplu kararlarını forma işler (betiğin başındaki açıklamaya bakınız).
   - Arşiv dosyaları (`archive/`) telif nedeniyle depoda yer almaz.
   - Tüm parametreler `config/ayarlar.yaml`, eleme ölçütleri `config/eleme_olcutleri.yaml` dosyasındadır.
"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="yöntem paragrafını ve sözcük sayısını göster, dosya yazma")
    p.add_argument("--force", action="store_true", help="var olan raporun üzerine yaz")
    p.add_argument("--sadece", default="", help="bu aşamada kullanılmaz (ana betikle uyum için)")
    args = p.parse_args()

    ayarlar, olcut = ayarlari_yukle(), eleme_olcutleri()
    gunluk = gunluk_kur("07_rapor")
    rapor = yol("rapor") / "veri_toplama_raporu.md"
    if rapor.exists() and not (args.force or args.dry_run):
        gunluk.info("Rapor zaten var; atlandı (yenilemek için --force).")
        return 0
    v = verileri_topla(ayarlar)
    paragraf = yontem_paragrafi(v, ayarlar)
    gunluk.info("Yöntem paragrafı: %d sözcük.", len(paragraf.split()))
    if args.dry_run:
        print(paragraf)
        gunluk.info("Deneme çalıştırması: dosya yazılmadı.")
        return 0
    rapor.parent.mkdir(parents=True, exist_ok=True)
    rapor.write_text(rapor_metni(v, ayarlar, olcut), encoding="utf-8")
    (yol("rapor") / "akis_semasi.md").write_text(
        "# Veri toplama akış şeması (PRISMA uyarlaması)\n\n" + akis_semasi(v) + f"\n\nÜretim zamanı (UTC): {utc_simdi()}\n", encoding="utf-8")
    beni_oku = KOK / "README.md"
    metin = beni_oku.read_text(encoding="utf-8")
    if README_BASLIGI not in metin:
        beni_oku.write_text(metin.rstrip("\n") + "\n" + README_EKI, encoding="utf-8")
        gunluk.info("README'ye '%s' bölümü eklendi.", README_BASLIGI)
    gunluk.info("Yazıldı: reports/veri_toplama_raporu.md, reports/akis_semasi.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
