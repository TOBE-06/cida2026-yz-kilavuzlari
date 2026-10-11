Merhaba. Bu klasörde CIDA 2026 sempozyumuna sunacağım "Sorumluluk Kimde?: Yapay Zekâ Kılavuzlarında Gazeteciliğin Etik Sınırlarının İnşası" çalışmasının veri toplama projesi var. Senden, gazetecilik aktörlerinin yapay zekâ (YZ) kılavuzlarını sistematik olarak bulan, benim elememe sunan, arşivleyen ve envanterleyen; hakeme gösterebileceğim, tekrar üretilebilir bir Python veri toplama hattı kurmanı istiyorum.

Claude Code'u yeni öğreniyorum. Lütfen her zaman Türkçe yanıt ver, her adımdan önce ne yapacağını ve sonra ne yaptığını sade bir dille açıkla, teknik terimleri ilk kullandığında bir cümleyle tanımla.

## 0. Önce oku, sonra planla (şu an plan modundayım)

Kod yazmadan önce şu dosyaları sırayla ve tamamen oku:
1. `CLAUDE.md` – senin talimatların ve kodlama standartların
2. `README.md` – proje özeti
3. `docs/PROJE_PROTOKOLU.md` – tüm yöntemsel kurallar (evren, dahil etme/dışlama ölçütleri, K/M kuralları, arşiv standardı, envanter şeması, etik ilkeler)
4. `config/ayarlar.yaml` – parametreler
5. `data/seed/kurumlar_seed.csv`, `data/seed/dislanan_aktorler.csv`, `data/seed/anahtar_sozcukler.yaml`

Okuduktan sonra:
- Projeyi ve görevini en fazla 10 maddede özetle.
- Protokolde belirsiz, eksik veya çelişkili gördüğün noktaları listele ve bana sor.
- Aşağıdaki aşamalar için bir uygulama planı öner: hangi dosyaları oluşturacaksın, hangi kütüphaneleri kullanacaksın, her aşamanın çıktısı ne olacak, tahmini süre.
- Planı onaylamadan hiçbir dosya oluşturma veya komut çalıştırma.

## 1. Çalışmanın özü (bağlam)

- **Problem:** YZ kılavuzları şeffaflık ve insan denetimi gibi ilkelerde yakınsıyor; ama bu metinlerin gazeteciliğin sınırlarını nasıl yeniden çizdiği ve ilkelerin uygulanabilir kurallarla ne ölçüde güvence altına alındığı belirsiz.
- **Kuram:** Gazetecilikte sınır çalışmaları (Carlson ve Lewis, 2015): genişleme, dışlama, özerkliğin korunması × katılımcılar, pratikler, profesyonellik.
- **Karşılaştırma:** K = haber kuruluşlarının kendi çalışanlarına yönelik kılavuzları (ajans, kamu yayıncısı, ticari, dijital yerli). M = meslek örgütleri, sendikalar, basın konseyleri ve gazetecilik savunuculuk örgütlerinin düzenlemeleri.
- **Mevcut durum:** Daha önce elle derlenmiş 47 belge var (29 K, 18 M; `kurumlar_seed.csv`). Bu hat iki işe yarayacak: (a) aynı süreci sistematik ve belgelenmiş biçimde baştan yürütmek ve gözden kaçmış belge olup olmadığını görmek; (b) tüm belgeleri tarih damgası ve SHA-256 özetiyle arşivlemek.
- **Kapsam dışı:** Kodlama ve analiz bu projede yok. Yalnızca veri toplama, eleme desteği, arşivleme ve envanter.

## 2. Aşamalar ve teslimler

Her aşamayı ayrı bir betik olarak yaz (`scripts/0N_*.py`), ortak işlevleri `hat/` altında topla, hepsini `scripts/run_pipeline.py --asama N` ile çalıştırılabilir yap. Her aşamanın sonunda dur, özet ver, onay bekle ve bir git commit öner.

**Aşama 0 – Kurulum**
- `git init`, `.gitignore` (`.venv/`, `archive/`, `data/mevcut_arsiv/`, `__pycache__/`), `requirements.txt` (sürümler sabit).
- Python sürümünü kontrol et; `uv` varsa onu, yoksa `python3 -m venv .venv` kullan. Sistem genelinde bir şey kurman gerekirse önce sor.
- Playwright Chromium'u kur.
- `hat/` modüllerini yaz: `ag.py` (robots kontrolü, alan başı bekleme, zaman aşımı, yeniden deneme, User-Agent), `metin.py` (trafilatura ile metin çıkarımı, PDF'ten metin), `adlandirma.py` (Türkçe karakter dönüşümlü dosya adı), `kayit.py` (logging, hatalar.csv, arama_gunlugu.csv).
- `tests/` altında bu modüller için pytest testleri ve küçük örnek HTML dosyaları; testleri çalıştır.

**Aşama 1 – Evren (örnekleme çerçevesi)** → `data/interim/evren.csv`
- Tohum listesindeki 47 kurumu ve `dislanan_aktorler.csv` içinde `yeniden_degerlendir = evet` olanları al.
- Literatürdeki belge listelerini (Becker vd. 2025; de-Lima-Santos vd. 2025; Sánchez-García vd. 2025; Gökdemir 2025) ve örgüt dizinlerini (AIPCE üye basın konseyleri, EFJ/IFJ üye sendikaları, EBU üyesi kamu yayıncıları, büyük haber ajansları, Türkiye'deki gazetecilik örgütleri) web arama aracınla tara; bulduğun her yeni aktörü kaynağıyla ekle.
- Her aramayı `logs/arama_gunlugu.csv` dosyasına yaz: `zaman_utc, arac, sorgu, sonuc_sayisi, eklenen_aktor, not`.
- Alan adı bilinmeyen veya "doğrulanmalı" notlu kurumların alan adını bul ve kaynağını yaz.
- Sütunlar: `aktor_id, kurum, olasi_grup, olasi_aktor_turu, ulke, bolge, alan_adi, kaynak, eklenme_nedeni`.
- Durma noktası: kaç aktör eklendiğini kaynak türüne göre tablo halinde göster.

**Aşama 2 – Keşif** → `data/interim/adaylar.csv`
- Her alan adı için protokol §8'deki dört katmanı uygula: tohum URL kontrolü, robots.txt ve sitemap, en fazla 2 derinlikte sınırlı gezinme (`baslangic_yollari`), kayıtlı `site:` web aramaları (çok dilli, `anahtar_sozcukler.yaml`).
- Aday olma koşulu: URL, başlık veya bağlantı metninde en az bir YZ terimi ve bir belge terimi.
- Her adayın `bulunma_yolu` (tohum/sitemap/gezinme/arama) ve `eslesen_terimler` alanını doldur.
- `robots.txt` izin vermiyorsa, bot koruması veya 403 varsa sayfayı alma; `erisim_durumu = engellendi` yaz.
- Mükerrer URL'leri birleştir (yönlendirme sonrası son URL ve normalleştirilmiş adres üzerinden).
- Durma noktası: kurum başına aday sayısı, bulunma yollarının dağılımı, engellenen alan adları.

**Aşama 3 – Ön puanlama ve eleme formu** → `adaylar_puanli.csv`, `data/eleme/eleme_formu.xlsx`
- Her adayın metnini çıkar; `dil`, `yz_terim_sayisi`, `normatif_isaret_sayisi`, `metin_uzunlugu`, `on_puan` hesapla.
- Ön puan **karar değildir**; yalnızca sıralama içindir.
- Excel formunu hazırla:
  - Puanlı sütunlar + araştırmacı sütunları: `karar` (Dahil/Hariç/Belirsiz), `dislama_kodu` (E1–E8), `gerekce`, `grup` (K/M), `aktor_turu`, `belge_statusu` (1–5), `kodlama_kapsami`.
  - Açılır listeler, sabitlenmiş başlık satırı, tıklanabilir URL.
  - Ölçütleri (D1–D4, E1–E8, statü ve kapsam kuralları) özetleyen bir "Yönerge" sekmesi.
  - Mevcut 47 belgeye karşılık gelen adayları işaretleyen bir sütun.
- **Durma noktası: Ben formu doldurup "eleme bitti" diyene kadar bekle. Hiçbir adayı kendin dahil etme veya dışlama.**

**Aşama 4 – Arşivleme** → `archive/K/`, `archive/M/`
- Yalnızca `karar = Dahil` olanları arşivle; belge kimliklerini koru (mevcut 47 kimliğini korur, yeniler sıradaki numarayı alır).
- Her belge için protokol §10'daki dosyaları üret: PDF (Playwright, A4, ekran medyası; kaynak PDF ise özgün dosya), HTML, TXT, tam sayfa PNG, JSON üst veri (istenen/son URL, HTTP durumu, erişim zamanı UTC, başlık, dil, her dosyanın SHA-256 özeti, en yakın Wayback kopyası).
- Çerez bannerları içeriği kapatıyorsa yalnızca "reddet / yalnızca gerekli" türü düğmeleri tıklamayı dene; olmazsa `gorsel_kontrol_gerekli` işaretle.
- Metin çok kısaysa veya YZ terimi içermiyorsa `gorsel_kontrol_gerekli` işaretle.
- Erişilemeyenleri `archive/manuel/BEKLENEN_DOSYALAR.md` dosyasında listele: hangi adla, hangi URL'den kaydetmem gerektiğini yaz. Ben tarayıcıdan "PDF olarak kaydet" ile ekledikten sonra özetleri ve üst veriyi tamamla, `toplama_yontemi = manuel` yaz.
- Durma noktası: otomatik, manuel ve başarısız sayılarını ve kontrol edilmesi gereken dosyaları göster.

**Aşama 5 – Envanter** → `data/envanter/envanter.csv` ve `.xlsx`
- Protokol §11'deki şemayı kullan. jamovi'deki belge düzeyi değişkenleriyle uyumlu olsun (grup, aktör türü, bölge, belge biçimi, belge statüsü, kodlama kapsamı).
- `reports/manifest.csv`: her arşiv dosyasının yolu, boyutu ve SHA-256 özeti.

**Aşama 6 – Mevcut örneklemle uzlaştırma** → `reports/uzlastirma.csv`
- `data/mevcut_arsiv/` varsa (yalnızca oku, asla değiştirme) yeni arşivle karşılaştır: eşleşen, yeni aday, bulunamayan.
- Eşleşenlerde metin benzerliğini (rapidfuzz) hesapla; belirgin fark varsa `surum_degisikligi = evet`.
- Klasör yoksa bu aşamayı atla ve bunu rapora yaz.

**Aşama 7 – Rapor** → `reports/veri_toplama_raporu.md`, `reports/akis_semasi.md`
- Çalıştırma bilgisi: tarih, Python ve paket sürümleri, git commit kimliği.
- PRISMA uyarlaması akış şeması (Mermaid): çerçevedeki aktör → bulunan aday → elenen (E kodlarına göre) → dahil edilen → arşivlenen (otomatik/manuel).
- K/M, aktör türü ve bölgeye göre dağılım tabloları; uzlaştırma sonucu; başarısız ve manuel sayfalar.
- "Yöntem bölümü için önerilen metin": yalnızca gerçekten yapılan işlemleri ve dosyalardan hesaplanan gerçek sayıları içeren 120–150 kelimelik akademik Türkçe paragraf. "Yalnızca … değil, aynı zamanda …" ve "… değil, …" kalıplarını kullanma.
- `README.md`'nin sonuna "Nasıl yeniden üretilir?" bölümü ekle.

## 3. Uyulması zorunlu kurallar (ayrıntısı CLAUDE.md'de)

- Bilimsel kararlar (dahil etme, dışlama, grup ataması) bana aittir.
- Uydurma URL, belge, tarih veya sayı yok. Raporlardaki her sayı dosyalardan hesaplanmalı.
- `robots.txt`'e uy, aynı alan adına en az 5 saniye arayla istek at, ayarlardaki User-Agent'ı kullan; giriş, ödeme duvarı, CAPTCHA ve bot korumasını aşmaya çalışma; arama motoru sonuç sayfalarını kazıma.
- `data/seed/` ve `data/mevcut_arsiv/` yalnızca okunur. Proje dışındaki hiçbir klasöre dokunma.
- Sistem genelinde kurulum ve dosya silme öncesi sor.
- Tüm parametreler `config/ayarlar.yaml`'dan okunur; betikler `--help`, `--dry-run`, `--force` destekler ve tekrar çalıştırılabilir (idempotent).

## 4. Bitiş tanımı

İş, şu koşullar sağlandığında tamamdır:
- `python scripts/run_pipeline.py --asama 1` … `--asama 7` sırasıyla hatasız çalışıyor; `pytest` geçiyor.
- Envanterdeki her dahil edilen belgenin arşiv dosyaları, erişim tarihi ve SHA-256 özeti var.
- Arama günlüğü, eleme formu, envanter, manifest ve rapor oluşmuş; rapordaki sayılar dosyalarla tutarlı.
- Bir hakem `README.md` ve `docs/PROJE_PROTOKOLU.md`'yi okuyarak süreci izleyebiliyor ve betikleri yeniden çalıştırabiliyor.

## 5. Şimdi yapacağın ilk iş

Yalnızca 0. bölümdeki okuma ve planlamayı yap: dosyaları oku, projeyi özetle, sorularını sor, uygulama planını öner ve onayımı bekle.
