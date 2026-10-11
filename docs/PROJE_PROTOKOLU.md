# Proje ve Veri Toplama Protokolü

**Çalışma:** "Sorumluluk Kimde?": Yapay Zekâ Kılavuzlarında Gazeteciliğin Etik Sınırlarının İnşası
**Hedef:** CIDA 2026 (5. Uluslararası Dijital Çağda İletişim Sempozyumu) bildirisi; ardından TR Dizin makalesi
**Araştırmacı:** Arş. Gör. Dr. Turancan Şirvanlı, Kocaeli Üniversitesi İletişim Fakültesi
**Protokol sürümü:** 1.3 (10 Ekim 2026)

Bu belge, çalışmanın kuramsal ve yöntemsel çerçevesini, veri toplama ve arşivleme sürecinin kurallarını tanımlar. Veri toplama hattındaki her betik bu protokolü uygular. Protokol, hakeme ve okura sürecin nasıl yürütüldüğünü göstermek için hazırlanmıştır.

---

## 1. Araştırma problemi

Üretken yapay zekâ (YZ) araçlarının 2022 sonrasında haber üretiminin hemen her aşamasına yayılmasıyla birlikte haber kuruluşları ve gazetecilik örgütleri art arda YZ kılavuzları ve etik beyanlar yayımlamaya başlamıştır. Alanyazın bu metinlerin şeffaflık, insan denetimi ve doğrulama gibi ortak ilkeler etrafında yakınsadığını göstermektedir (de-Lima-Santos vd., 2025; Becker vd., 2025; Sánchez-García vd., 2025).

Çalışmanın çıkış noktası, kılavuzların birer ilke listesi olmanın ötesinde gazeteciliğin hangi aktörleri ve pratikleri kapsadığını yeniden çizen metinler olduğu argümanıdır. Mevcut çalışmalar kılavuzları çoğunlukla tematik olarak betimlemekte; kılavuzların sınır çizme işlevine odaklanan kuramsal bir okuma ve ilan edilen ilkelerin prosedür ve denetim mekanizmalarıyla ne ölçüde güvence altına alındığına ilişkin bir sorgulama bulunmamaktadır.

## 2. Kuramsal çerçeve

**Gazetecilikte sınır çalışmaları** (Gieryn, 1999; Carlson ve Lewis, 2015). Carlson (2015), gazetecilik aktörlerinin üç stratejiyle (genişleme, dışlama, özerkliğin korunması) üç alanda (katılımcılar, pratikler, profesyonellik) sınır çizdiğini belirtir. İnsan–makine ilişkisi için Lewis, Guzman ve Schmidt (2019) çerçevesinden yararlanılır. Güncel tartışma: Kuai ve Karlsson (2026), Verhoeven ve Van Leuven (2026).

## 3. Amaç ve araştırma soruları

**Amaç:** YZ kılavuzlarını sınır çalışması perspektifinden inceleyerek sınırların hangi stratejilerle çizildiğini, sorumluluğun hangi öznelere yüklendiğini ve sınırların metin düzeyinde ne ölçüde uygulanabilir kurallarla kurumsallaştırıldığını ortaya koymak. Her soru kurumsal (K) ve mesleki (M) öz-düzenleme karşılaştırmasıyla yanıtlanır.

- **AS1 (Pratikler):** Kılavuzlarda YZ'nin hangi kullanımları gazetecilik pratiğine dahil edilmekte, hangileri dışlanmaktadır?
- **AS2 (Katılımcılar):** İnsan–YZ sınırı nasıl kurulmakta ve sorumluluk hangi öznelere atfedilmektedir?
- **AS3 (Biçim):** Hangi sınır çalışması stratejileri hangi alanlarda öne çıkmakta ve bu sınırlar ne ölçüde metinsel olarak kurumsallaşmaktadır?

## 4. Araştırma deseni (özet)

Karşılaştırmalı, kesitsel, tümdengelimli ve tümevarımlı kodlamayı birleştiren nitel içerik analizi (Schreier, 2012). Analiz birimi normatif ifadedir (tek özne, tek deontik kip, tek nesne). Kodlama boyutları: tema, kullanım alanı, deontik kip, sınır tipi, sınır alanı, sorumluluk öznesi, YZ'nin konumu ve operasyonel derinlik (D1 ilke, D2 davranış kuralı, D3 prosedür, D4 denetim/yaptırım). Kodlama jamovi'de yapılır. Ayrıntılı kodlama kılavuzu ayrı belgededir.

> **Bu protokolün kapsamı:** Aşağıdaki bölümler yalnızca **veri toplama, eleme ve arşivleme** sürecini düzenler. Kodlama ve analiz bu hattın dışındadır.

---

## 5. Evren ve örnekleme çerçevesi

**Evren:** Gazetecilik alanındaki aktörlerin (haber kuruluşları ve gazetecilik meslek örgütleri) kamuya açık biçimde yayımladığı, üretken YZ dahil yapay zekâ kullanımına ilişkin normatif hüküm içeren belgeler.

**Örnekleme yöntemi:** Amaçlı örnekleme. Hedef, iki öz-düzenleme düzeyinde aktör türü ve bölge çeşitliliğini karşılamaktır; istatistiksel temsil amaçlanmaz.

**Örnekleme çerçevesi dört kaynaktan oluşturulur:**

1. **Literatürdeki belge listeleri:** Becker vd. (2025; 52 kuruluş), de-Lima-Santos vd. (2025), Sánchez-García vd. (2025; bağlantıları açık), Gökdemir (2025).
2. **Örgüt dizinleri:** Avrupa Bağımsız Basın Konseyleri İttifakı (AIPCE) üyeleri, IFJ/EFJ üye sendikaları, Avrupa Yayın Birliği (EBU) üyesi kamu yayıncıları, büyük uluslararası haber ajansları, ülke basın konseyleri.
3. **Web araması:** Claude Code'un web arama aracıyla `site:` ve çok dilli anahtar sözcük sorguları. Her sorgu `logs/arama_gunlugu.csv` dosyasına kaydedilir.
4. **Mevcut tohum listesi:** `data/seed/kurumlar_seed.csv` (önceden derlenmiş 47 belge).

## 6. Dahil etme ve dışlama ölçütleri

Ölçütlerin tek kaynağı `config/eleme_olcutleri.yaml` dosyasıdır; eleme formunun açılır listeleri ve "Yönerge" sekmesi bu dosyadan üretilir. Aşağıdaki tablolar o dosyanın okunabilir özetidir.

### Dahil etme (hepsi sağlanmalı)

| Kod | Ölçüt |
|---|---|
| D1 | Belge bir **gazetecilik aktörü** tarafından yayımlanmıştır (haber kuruluşu, meslek örgütü, sendika, basın/medya konseyi, gazetecilik savunuculuk örgütü). |
| D2 | Belge **kamuya açıktır** (giriş, ödeme veya kurum içi erişim gerekmez). |
| D3 | Belge YZ kullanımına ilişkin **en az bir normatif hüküm** içerir (yasak, izin, yükümlülük, tavsiye veya değer beyanı). |
| D4 | Belgenin **erişim tarihindeki en güncel sürümü** kullanılır; erişim tarihi kaydedilir. |

**Statü kuralı:** Kabul edilmiş politikaların yanı sıra öneri, taslak, rapor ve kurumun yayın organında yayımlanmış metinler, kodlanabilir YZ hükmü içeriyorsa dahil edilir ve `belge_statusu` değişkeniyle işaretlenir (1 kabul edilmiş, doğrudan metin; 2 kabul edilmiş, aktarılmış/özet metin; 3 öneri/taslak; 4 kurum yayın organında makale; 5 rapor, öneri bölümü). Analizde duyarlılık kontrolü için 1 dışındakiler çıkarılabilir.

**Kapsam kuralı:** YZ'ye ayrılmış bağımsız belgede tüm metin; genel etik kod içindeki belgelerde yalnızca YZ'ye ilişkin madde veya bölüm kodlanır (`kodlama_kapsami` alanına yazılır). Belgenin biçimi `belge_bicimi` değişkeniyle kaydedilir (1 bağımsız YZ kılavuzu; 2 genel kod içinde YZ bölümü).

### Dışlama kodları

| Kod | Gerekçe |
|---|---|
| E1 | Gazetecilik aktörü değil (teknoloji şirketi, sektörler arası girişim, akademik merkez, danışmanlık). |
| E2 | Hükümetlerarası kuruluş veya kamu otoritesi metni (Avrupa Konseyi, UNESCO, AGİT, bakanlıklar, düzenleyici kurumlar). |
| E3 | YZ'ye ilişkin normatif hüküm yok (haber, tanıtım, ürün sayfası, betimleme; genel kodda YZ maddesi yok). |
| E4 | Yayıncı/işveren birliği metni veya kurumlara örnek olarak sunulan politika şablonu. |
| E5 | Mükerrer veya eski sürüm (daha güncel sürüm mevcut ya da aynı metin başka adreste zaten dahil). |
| E6 | Erişilemez (ödeme duvarı, giriş gerekli, sayfa kaldırılmış ve arşiv kopyası yok). |
| E7 | Kamuya açık olmayan kurum içi belge. |
| E8 | Grup ataması yapılamayan hibrit metin (yayıncılar ile meslek örgütlerinin ortak metni). |

### Eleme sırası

Her aday aşağıdaki sırayla kontrol edilir; ilk takılan koşulun kodu yazılır (bir adaya tek dışlama kodu verilir).

| Sıra | Adım | Kodlar |
|---|---|---|
| 1 | Erişim | E6, E7 |
| 2 | Aktör | E1, E2, E4, E8 |
| 3 | İçerik | E3 |
| 4 | Sürüm | E5 |
| 5 | Dahil | `grup`, `aktor_turu`, `ulke`, `bolge`, `belge_bicimi`, `belge_statusu`, `kodlama_kapsami` doldurulur |

### Sınır durumlar için karar kuralları

| Durum | Kural |
|---|---|
| Aynı kurumun birbirini tamamlayan birden fazla YZ metni var (ör. şirket ilkeleri + haber odası sayfası). | Tek belge kimliği altında birleştirilir; `kodlama_kapsami` alanına hangi metinlerin birleştirildiği yazılır. |
| Politikanın kendisine erişilemiyor, ama kurumun yayın organındaki bir haber politikayı aktarıyor. | Dahil; `belge_statusu = 2`; kapsam: yalnızca politikayı aktaran pasajlar ve yöneticilerin politika beyanları. |
| Kurumun kendi yayın organında yöneticisi veya çalışanı tarafından yazılmış, normatif öneri içeren yazı. | Normatif hüküm varsa dahil; `belge_statusu = 4`; kapsam: yalnızca normatif bölümler. |
| Henüz kabul edilmemiş öneri veya taslak. | Metne erişilebiliyor ve YZ hükmü içeriyorsa dahil; `belge_statusu = 3`. Metne erişilemiyorsa E6. |
| Rapor içinde öneri veya yönerge bölümü. | Dahil; `belge_statusu = 5`; kapsam: yalnızca öneri/yönerge bölümü. |
| Genel kod YZ adını anmıyor, "teknoloji" gibi genel bir terim kullanıyor. | Belgenin kendisi veya resmî açıklama notları hükmü açıkça YZ ile ilişkilendiriyorsa dahil (gerekçeye kaynak yazılır); aksi hâlde E3. |
| Basın konseyi ayrı bir YZ metni yayımlamamış, genel kurallarını YZ vakalarına kararlarla uyguluyor. | E3; gerekçeye "vaka bazlı uygulama" yazılır. Şikâyet kararları çalışmanın kapsamı dışındadır. |
| Ürün tanıtım sayfası içinde etik taahhütler. | Normatif ifadeler varsa dahil; kapsam: yalnızca normatif ifadeler ve SSS yanıtları; tanıtım cümleleri kodlanmaz. |
| Belge Türkçe veya İngilizce dışında bir dilde. | Dil dışlama ölçütü değildir; dahil edilir ve dil alanı doldurulur. |
| Kararsız kalındı. | `karar = Belirsiz`; gerekçe yazılır; ikinci okumada kesinleştirilir. Betik hiçbir "Belirsiz" kararı kendisi değiştirmez. |

Önceki derlemede dışlanan aktörler ve gerekçeleri `data/seed/dislanan_aktorler.csv` dosyasındadır. `yeniden_degerlendir = evet` olanlar bu turda yeniden kontrol edilir.

## 7. Grup ve aktör sınıflaması

**Grup (K/M) karar kuralı:** Belgeyi yayımlayan aktörün türü belirler.

- **K (kurumsal öz-düzenleme):** Bir haber kuruluşunun kendi çalışanlarına yönelik kılavuzu. Aktör türleri: 1 ajans, 2 kamu yayıncısı, 3 ticari yayın/grup, 4 dijital yerli.
- **M (mesleki öz-düzenleme):** Meslek topluluğuna ve kamuya seslenen düzenleme. Aktör türleri: 5 meslek örgütü/sendika, 6 basın/medya konseyi, 7 savunuculuk/uluslararası gazetecilik örgütü.

**Bölge:** 1 Kuzey Amerika, 2 Avrupa, 3 Türkiye (ayrı kodlanır), 4 Küresel Güney, 5 Uluslararası (birden fazla ülkeye seslenen ağlar).

## 8. Keşif stratejisi

Keşif dört katmanda yürütülür. Her aday URL'nin hangi katmanla bulunduğu kaydedilir (`bulunma_yolu`).

1. **Tohum:** `kurumlar_seed.csv` içindeki bilinen URL'ler doğrudan kontrol edilir.
2. **Site haritası:** Her alan adının `robots.txt` dosyasındaki ve `/sitemap.xml` adresindeki site haritaları okunur; URL'ler `anahtar_sozcukler.yaml` içindeki kalıplarla süzülür.
3. **Sınırlı gezinme:** Kurumun ana sayfası ve tipik kurumsal sayfalarından (hakkımızda, etik, standartlar) başlayarak en fazla 2 derinlikte bağlantılar izlenir; bağlantı metni veya URL anahtar sözcük içeriyorsa aday olur.
4. **Web araması:** `site:alanadi.com "yapay zeka" OR "artificial intelligence" guidelines` biçiminde sorgular. Arama sonuçları otomatik kazınmaz; aramayı Claude Code'un kendi arama aracı yapar ve her sorgu günlüğe yazılır.

**Aday olma koşulu:** URL, başlık veya bağlantı metninde en az bir YZ terimi ve en az bir belge terimi (çok dilli liste).

**Koşulun uygulanışı (sürüm 1.1):**

- *Eşleştirme:* Kısa terimler (ai, ki, ia, yz, llm) yalnızca tam sözcük olarak eşleşir; böylece "email" veya "retail" gibi sözcükler YZ terimi sayılmaz. Tire ile biten terimler (`ai-`) sözcük başında, tire ile başlayan Türkçe ekler (`-malı`, `-meli`) sözcük sonunda, diğer terimler sözcük başında aranır. Kural `hat/metin.py` içinde uygulanır ve `tests/test_metin.py` ile sınanır.
- *URL kalıpları:* `anahtar_sozcukler.yaml` içindeki `url_kaliplari`, YZ kalıbı ve belge kalıbı olarak ikiye ayrılır (liste: `config/ayarlar.yaml`, `belge_turu_url_kaliplari`). Tek başına bir URL kalıbı adaylık için yeterli değildir; yukarıdaki koşul aynen geçerlidir.
- *Tohum URL'leri:* Tohum listesindeki bilinen URL'ler koşula bakılmaksızın aday olur (`bulunma_yolu = tohum`).
- *Genel etik kodlar:* M grubundaki aktörlerde yalnızca belge terimi eşleşen etik kod sayfaları da `bulunma_yolu = etik_kod` etiketiyle aday olur; bu sayfalarda YZ terimi başlıkta değil tam metinde aranır (Aşama 3). Gerekçe: bazı basın konseyleri YZ hükmünü genel kodun bir maddesi olarak düzenlemektedir.

## 9. Ön puanlama ve eleme

**Otomatik ön puanlama (karar değildir):** Her adayın metni çıkarılır; YZ terimi sayısı, normatif işaret sayısı, dil ve başlık hesaplanır. Sonuç yalnızca araştırmacının eleme sırasını belirlemek için kullanılır. Betik ayrıca `isaretler` sütununa araştırmacıya yardımcı gözlemler yazar (ör. "kurum dışlanan aktörler listesinde", "metinde YZ terimi yok", "aynı kurumdan birden fazla aday", "sayfaya erişilemedi; Wayback kopyası var"). İşaretler dışlama kodu önermez; `karar` ve `dislama_kodu` sütunları betik tarafından her zaman boş bırakılır.

**İnsan elemesi (karar):** Araştırmacı `data/eleme/eleme_formu.xlsx` dosyasında her aday için şunları girer: `karar` (Dahil / Hariç / Belirsiz), `dislama_kodu` (E1–E8), `gerekce`; dahil edilenler için ayrıca `grup`, `aktor_turu`, `ulke`, `bolge`, `belge_bicimi`, `belge_statusu`, `kodlama_kapsami`. `ulke` ve `bolge` evren listesinden önceden doldurulur ve araştırmacı tarafından değiştirilebilir. Aynı kurumun birleştirilecek metinleri için isteğe bağlı `birlestir` sütununa ana adayın `aday_id` değeri yazılır. Belirsiz kararlar ikinci okumada kesinleştirilir. Dahil etme ölçütlerini karşılayan ancak araştırmacı kararıyla bu aşamadaki örnekleme alınmayan adaylar `Ertelendi` olarak işaretlenir; bunlara dışlama kodu verilmez ve arşiv dosyaları ayrı klasörde saklanır. **Hiçbir belge betik tarafından dahil edilmez veya dışlanmaz.**

İsteğe bağlı güvenilirlik adımı: adayların %20'si ikinci bir araştırmacı tarafından bağımsız olarak elenir; uyum yüzdesi raporlanır.

## 10. Arşivleme standardı

Dahil edilen her belge için:

| Dosya | İçerik |
|---|---|
| `.pdf` | Sayfanın işlenmiş görüntüsü (Playwright, A4, ekran medyası). Kaynak zaten PDF ise özgün dosya indirilir. |
| `.html` | Ham HTML |
| `.txt` | Çıkarılmış ana metin (analiz için) |
| `.png` | Tam sayfa ekran görüntüsü (görsel kontrol) |
| `.json` | Üst veri: istenen ve son URL, HTTP durumu, erişim zamanı (UTC, ISO 8601), sayfa başlığı, dil, her dosyanın SHA-256 özeti, en yakın Wayback Machine kopyası, toplama yöntemi (otomatik/manuel/wayback) |

**Adlandırma:** `[BelgeID]_[Kurum]_[kısa-ad]_[YYYY-AA-GG]` (Türkçe karakterler ASCII'ye çevrilir, boşluk yerine tire). Örnek: `K01_Associated-Press_AP_2026-10-12.pdf`.

**Bütünlük:** SHA-256 özeti, dosyanın sonradan değiştirilmediğini gösteren dijital parmak izidir. Tüm özetler `reports/manifest.csv` dosyasında toplanır.

**Erişilemeyen sayfalar:** `robots.txt` engeli, 403 hatası, bot koruması veya ödeme duvarı varsa betik sayfayı zorlamaz; `toplama_yontemi = manuel` olarak işaretler. Araştırmacı bu sayfaları tarayıcıda açıp "PDF olarak yazdır" ile aynı adlandırmayla kaydeder; betik ardından özetleri ve üst veriyi tamamlar.

**Kaldırılmış sayfalar:** Araştırmacının dahil ettiği bir belgenin sayfası kaldırılmışsa ve Wayback Machine'de kopyası varsa belge bu kopyadan arşivlenir; `toplama_yontemi = wayback` yazılır ve kopyanın tarihi üst veriye kaydedilir. Kopya yoksa belge E6 kapsamındadır (karar araştırmacınındır).

## 11. Envanter şeması

`data/envanter/envanter.csv` (ve `.xlsx`):

`belge_id, kurum, grup, aktor_turu, ulke, bolge, belge_adi, url, son_url, erisim_tarihi_utc, dil, belge_bicimi, belge_statusu, kodlama_kapsami, bulunma_yolu, toplama_yontemi, karar, dislama_kodu, gerekce, sha256_pdf, sha256_txt, wayback_url, mevcut_arsivle_eslesme, surum_degisikligi, not`

Envanter, jamovi'deki `belge_duzeyi.sav` dosyasının A ve B değişkenleriyle uyumludur.

## 12. Mevcut örneklemle uzlaştırma

Daha önce elle derlenen 47 belge (`data/mevcut_arsiv/`, **yalnızca okunur**) yeni taramayla karşılaştırılır:

- **Eşleşen:** aynı belge bulundu; metin benzerliği hesaplanır, belirgin fark varsa `surum_degisikligi = evet`.
- **Yeni aday:** taramada bulunan ve mevcut örneklemde olmayan belge; araştırmacı elemesine gider.
- **Bulunamayan:** mevcut örneklemde olup taramada çıkmayan belge; nedeni not edilir (ör. sayfa kaldırılmış).

## 13. Etik ve hukuki ilkeler

- `robots.txt` kurallarına uyulur; aynı alan adına en az 5 saniye arayla istek gönderilir.
- İstekler, araştırmacının iletişim bilgisini içeren açık bir User-Agent ile yapılır.
- Giriş gerektiren alanlara girilmez; ödeme duvarı, CAPTCHA veya bot koruması aşılmaya çalışılmaz.
- Arama motoru sonuç sayfaları otomatik kazınmaz.
- Arşivlenen belgeler yalnızca araştırma amacıyla saklanır. Telif nedeniyle PDF'ler açık depoda paylaşılmaz; hakeme ve okura URL, erişim tarihi, SHA-256 özeti ve Wayback bağlantısı sunulur.
- Kişisel veri toplanmaz.

## 14. Raporlama

Hat sonunda `reports/veri_toplama_raporu.md` otomatik oluşturulur:

- Çalıştırma bilgisi: tarih, yazılım sürümleri, git commit kimliği
- PRISMA uyarlaması akış şeması: çerçevedeki aktör → bulunan aday → ön puanlama → elenen (kodlara göre) → dahil edilen → arşivlenen (otomatik/manuel)
- Gruplara, aktör türlerine ve bölgelere göre dağılım
- Mevcut örneklemle uzlaştırma sonucu
- Başarısız ve manuel toplanan sayfalar listesi
- Yöntem bölümü için **yalnızca gerçekleşen işlemleri ve gerçek sayıları** içeren önerilen paragraf

## 15. Veri toplamanın sınırlılıkları

- Kamuya açık olmayan iç düzenlemeler kapsam dışındadır.
- Keşif dil ve anahtar sözcük listesiyle sınırlıdır; listede olmayan dillerdeki belgeler kaçabilir.
- Web sayfaları zamanla değişir; bulgular erişim tarihindeki sürüme dayanır.
- Bazı kurumların bot koruması otomatik erişimi engeller; bu sayfalar manuel toplanır ve envanterde işaretlenir.

## 16. Kaynakça

- Becker, K. B., Simon, F. M., & Crum, C. (2025). Policies in parallel? A comparative study of journalistic AI policies in 52 global news organisations. *Digital Journalism, 13*(9), 1578–1598. https://doi.org/10.1080/21670811.2024.2431519
- Carlson, M. (2015). Introduction: The many boundaries of journalism. M. Carlson & S. C. Lewis (Ed.), *Boundaries of journalism* (ss. 1–18) içinde. Routledge.
- Carlson, M., & Lewis, S. C. (Ed.). (2015). *Boundaries of journalism: Professionalism, practices and participation*. Routledge.
- de-Lima-Santos, M. F., Yeung, W. N., & Dodds, T. (2025). Guiding the way: A comprehensive examination of AI guidelines in global media. *AI & Society, 40*(4), 2585–2603. https://doi.org/10.1007/s00146-024-01973-5
- Gieryn, T. F. (1999). *Cultural boundaries of science: Credibility on the line*. University of Chicago Press.
- Gökdemir, A. (2025). Haber ajansları tarafından geliştirilen gazetecilikte yapay zekâ kullanımı standartları. *İletişim Kuram ve Araştırma Dergisi, 70*, 46–65. https://doi.org/10.47998/ikad.1592394
- Kuai, J., & Karlsson, M. (2026). The Great Wall of the Press: Layered boundary work of AI-integrated journalism. *Media and Communication, 14*, Article 12504. https://doi.org/10.17645/mac.12504
- Lewis, S. C., Guzman, A. L., & Schmidt, T. R. (2019). Automation, journalism, and human–machine communication. *Digital Journalism, 7*(4), 409–427. https://doi.org/10.1080/21670811.2019.1577147
- Sánchez-García, P., Diez-Gracia, A., Repilado Mayorga, I., & Jerónimo, P. (2025). Media self-regulation in the use of AI. *Journalism and Media, 6*(1), 29. https://doi.org/10.3390/journalmedia6010029
- Schreier, M. (2012). *Qualitative content analysis in practice*. SAGE.
- Verhoeven, E., & Van Leuven, S. (2026). Rewriting the rules? European media councils' responses to digital journalism's ethical challenges. *Digital Journalism*. https://doi.org/10.1080/21670811.2026.2685658

## Sürüm geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 1.0 | Ekim 2026 | İlk sürüm |
| 1.1 | 9 Ekim 2026 | §8: aday koşulunun uygulanışı açıklandı (sözcük sınırı kuralı, URL kalıplarının ayrımı, tohum URL'leri, M grubunda genel etik kodlar). Araştırmacı onayıyla. |
| 1.2 | 9 Ekim 2026 | §6 `config/eleme_olcutleri.yaml` ile eşitlendi: E1, E2, E3, E5, E6 ifadeleri genişletildi; eleme sırası ve sınır durum kuralları eklendi; `belge_bicimi` kodları tanımlandı. §9: `isaretler`, `ulke`, `bolge`, `belge_bicimi`, `birlestir` sütunları. §10: Wayback kopyasından arşivleme. Araştırmacı onayıyla. |
| 1.3 | 10 Ekim 2026 | §9: `Ertelendi` karar değeri eklendi. Araştırmacı kararıyla. |
