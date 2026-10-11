# CIDA 2026 – YZ Kılavuzları Veri Toplama ve Arşivleme Hattı

**"Sorumluluk Kimde?": Yapay Zekâ Kılavuzlarında Gazeteciliğin Etik Sınırlarının İnşası**
Arş. Gör. Dr. Turancan Şirvanlı · Kocaeli Üniversitesi İletişim Fakültesi

## Proje hedefi

Haber kuruluşları (kurumsal öz-düzenleme, K) ile meslek örgütleri ve basın konseylerinin (mesleki öz-düzenleme, M) yayımladığı yapay zekâ kılavuzlarını gazetecilikte sınır çalışmaları perspektifinden karşılaştırmak. Bu depo, analizin veri tabanını oluşturan belgelerin **sistematik, belgelenmiş ve tekrar üretilebilir** biçimde toplanmasını sağlar.

**Araştırma soruları**
- **AS1:** YZ'nin hangi kullanımları gazetecilik pratiğine dahil ediliyor, hangileri dışlanıyor?
- **AS2:** İnsan–YZ sınırı nasıl kuruluyor, sorumluluk hangi öznelere atfediliyor?
- **AS3:** Hangi sınır stratejileri hangi alanlarda öne çıkıyor ve sınırlar ne ölçüde metinsel olarak kurumsallaşıyor?

## Hat ne yapar?

```
1 Evren  →  2 Keşif  →  3 Ön puanlama  →  ARAŞTIRMACI ELEMESİ  →  4 Arşivleme  →  5 Envanter  →  6 Uzlaştırma  →  7 Rapor
```

Aşama numaraları `scripts/` altındaki betik numaralarıyla aynıdır.

1. **Evren:** Tohum listesi, literatürdeki belge listeleri ve örgüt dizinlerinden aktör listesi çıkarır.
2. **Keşif:** Her kurumun sitesinde site haritası, sınırlı gezinme ve kayıtlı web aramalarıyla YZ kılavuzu adaylarını bulur.
3. **Ön puanlama:** Adayların metnini çıkarır, YZ terimi ve normatif ifade yoğunluğunu hesaplar, eleme formunu hazırlar.
   - **Eleme (betik değil):** Dahil etme ve dışlama kararlarını **araştırmacı** verir (protokoldeki D1–D4 ve E1–E8 ölçütleri). Form doldurulmadan Aşama 4'e geçilmez.
4. **Arşivleme:** Dahil edilen her belgeyi PDF, HTML, metin, ekran görüntüsü ve üst veri olarak tarih damgası ve SHA-256 özetiyle kaydeder.
5. **Envanter:** Envanter tablosunu ve tüm arşiv dosyalarının özet listesini (manifest) üretir.
6. **Uzlaştırma:** Yeni arşivi önceden elle derlenen 47 belgeyle karşılaştırır.
7. **Rapor:** Akış şeması, sayılar, başarısız sayfalar ve yöntem bölümü için önerilen metni üretir.

## Klasör yapısı

```
README.md              bu dosya
CLAUDE.md              Claude Code için talimatlar ve kodlama standartları
docs/                  PROJE_PROTOKOLU.md (tüm kurallar), BASLANGIC_REHBERI.md
config/ayarlar.yaml    tüm parametreler
data/seed/             tohum kurum listesi, dışlanan aktörler, çok dilli anahtar sözcükler
data/interim/          ara çıktılar
data/eleme/            araştırmacının doldurduğu eleme formu
data/envanter/         envanter tablosu
archive/               arşivlenen belgeler (telif nedeniyle paylaşılmaz)
logs/                  çalışma ve arama günlükleri
reports/               veri toplama raporu, manifest (SHA-256 listesi)
scripts/ , hat/        betikler ve ortak modüller
tests/                 testler
```

## Hızlı başlangıç

```bash
cd cida2026-yz-kilavuzlari
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
pytest                                   # testler
python scripts/run_pipeline.py --asama 1 # aşama aşama ilerleyin (1–7)
```

Ayrıntılı ilk kullanım adımları: `docs/BASLANGIC_REHBERI.md`.

## Hakem ve okur için

Bu depo şunları belgeler: veri toplama protokolü, betikler, ayarlar, arama ve çalışma günlükleri, eleme kararları ve gerekçeleri, envanter, her belgenin erişim tarihi, URL'si, SHA-256 özeti ve Wayback Machine bağlantısı. Arşivlenen tam metinler telif nedeniyle paylaşılmaz; aynı belgeye URL ve Wayback bağlantısı üzerinden ulaşılabilir ve özet değerleri dosyanın değişmediğini doğrular.

## Etik

`robots.txt` kurallarına uyulur, istekler arasında bekleme süresi bırakılır, giriş, ödeme duvarı ve bot koruması aşılmaz, kişisel veri toplanmaz. Ayrıntı: `docs/PROJE_PROTOKOLU.md` §13.

## Yapay zekâ kullanım beyanı

Veri toplama betikleri araştırmacının yönlendirmesiyle Claude Code (Anthropic) yardımıyla yazılmıştır. Belgelerin örnekleme dahil edilmesine ilişkin tüm kararlar araştırmacı tarafından verilmiştir.

## Nasıl yeniden üretilir?

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
