# Başlangıç Rehberi: Claude Code ile Veri Toplama

Bu rehber, Claude Code'u daha önce kullanmamış biri için bu projenin nasıl yürütüleceğini adım adım anlatır.

## 1. Claude Code nedir?

Claude Code, bilgisayarınızdaki **bir klasörün içinde çalışan** bir yapay zekâ asistanıdır. Sohbetteki Claude'dan farkı şudur: klasördeki dosyaları okuyabilir, yeni dosya ve program (betik) yazabilir, bu programları sizin onayınızla çalıştırabilir ve sonuçlarına bakarak düzeltebilir.

Bir benzetmeyle: Claude Code, masanızda oturan ve programlama bilen bir araştırma asistanıdır. Ona ne istediğinizi Türkçe anlatırsınız; o kodu yazar, çalıştırmadan önce size sorar, sonucu gösterir. Bilimsel kararları (hangi belge örnekleme girer) siz verirsiniz.

## 2. Üç temel parça

| Parça | Ne işe yarar? | Bu projedeki karşılığı |
|---|---|---|
| **Proje klasörü** | Claude Code'un çalıştığı alan. Yalnızca bu klasörü görür ve değiştirir. | `cida2026-yz-kilavuzlari/` |
| **CLAUDE.md** | Asistanın "iş tanımı". Her oturum başında otomatik okunur. Kurallar, standartlar, yasaklar burada. | Etik tarama kuralları, kararları araştırmacının vermesi, Türkçe yanıt |
| **Prompt** | O günkü görev. Sohbete yapıştırdığınız talimat. | `PROMPT_CLAUDE_CODE.md` |

Ek olarak `docs/PROJE_PROTOKOLU.md` çalışmanın tüm yöntemsel kurallarını içerir; Claude Code bunu da okur.

## 3. Bu projede Claude Code ne yapacak?

| Kavram | Sade anlamı |
|---|---|
| **Tarama (keşif)** | Kurumların sitelerinde YZ kılavuzu olabilecek sayfaları bulmak. |
| **Site haritası (sitemap)** | Bir sitenin tüm sayfalarını listeleyen dosya. Bütün siteyi gezmeden adresleri görmeyi sağlar. |
| **robots.txt** | Sitenin "hangi sayfalarımı otomatik programlar alabilir" kurallarını yazdığı dosya. Uyacağız. |
| **Kazıma (scraping)** | Bulunan sayfanın metnini programla almak. |
| **Arşivleme** | Sayfayı o günkü haliyle PDF olarak kaydetmek ve tarih damgası eklemek. |
| **SHA-256 özeti** | Dosyanın dijital parmak izi. Dosyada tek harf değişse özet değişir; hakeme "dosya sonradan değiştirilmedi" demenin yolu. |
| **Envanter** | Tüm belgelerin listesi: kim, ne zaman, hangi adresten, hangi kararla. |
| **Eleme** | Bulunan adayların ölçütlere uyup uymadığına sizin karar vermeniz. |

## 4. Kurulum (bir kez)

**Seçenek A – Claude masaüstü uygulaması (önerilen):** Uygulamayı açın, **Code** sekmesine tıklayın, proje klasörünü seçin. Masaüstü uygulaması Claude Code'u içerir; ayrıca kurmanıza gerek yoktur (ücretli abonelik gerekir).

**Seçenek B – Terminal:** macOS'ta Terminal'i açıp şunu yapıştırın:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Kurulumdan sonra yeni bir Terminal penceresinde `claude --version` yazın; bir sürüm numarası görmelisiniz. Ardından:

```bash
cd ~/Akademi/cida2026-yz-kilavuzlari   # klasörün bulunduğu yol
claude
```

Güncel kurulum bilgisi: https://code.claude.com/docs/en/overview

## 5. Adım adım çalışma

1. **Klasörü hazırlayın.** Bu paketteki `cida2026-yz-kilavuzlari` klasörünü bilgisayarınızda kalıcı bir yere koyun (ör. `~/Akademi/`). Daha önce elle topladığınız 47 PDF'i karşılaştırma için kullanmak isterseniz `data/mevcut_arsiv/` içine **kopyalayın** (özgün klasörü taşımayın).
2. **Claude Code'u bu klasörde açın** (Seçenek A veya B).
3. **Plan moduna geçin.** `Shift+Tab` tuşuna, durum çubuğunda "plan mode on" görünene kadar basın. Bu modda Claude Code dosyaları okur ve plan önerir ama hiçbir şeyi değiştirmez.
4. **Prompt'u yapıştırın.** `PROMPT_CLAUDE_CODE.md` içindeki metnin tamamını kopyalayıp gönderin.
5. **Planı okuyun ve onaylayın.** Claude Code projeyi özetleyip plan önerecek. Anlamadığınız yeri sorun; değiştirmek istediğinizi söyleyin. Onayladığınızda plan modundan çıkar ve çalışmaya başlar.
6. **İzin isteklerini okuyun.** Claude Code bir komut çalıştırmadan veya dosya yazmadan önce izin ister. Ne yapacağını okuyun; emin değilseniz "bu komut ne yapıyor?" diye sorun.
7. **Durma noktalarında kontrol edin.** Her aşama sonunda özet verir ve bekler. Sayıları ve oluşan dosyaları kontrol edin.
8. **Elemeyi siz yapın.** Aşama 3 sonunda `data/eleme/eleme_formu.xlsx` oluşur. Excel'de açın, her aday için karar verin, kaydedin, Claude Code'a "eleme bitti" yazın.
9. **Manuel sayfaları kaydedin.** Bot korumalı sitelerin listesini verecek; bu sayfaları tarayıcıda açıp "Yazdır → PDF olarak kaydet" ile söylediği adla `archive/manuel/` içine kaydedin.
10. **Raporu alın.** Son aşamada `reports/veri_toplama_raporu.md` oluşur. Yöntem bölümündeki sayıları buradan alın.

## 6. Faydalı komutlar ve ipuçları

| Ne yapmak istiyorum? | Nasıl? |
|---|---|
| Plan moduna geçmek / çıkmak | `Shift+Tab` |
| Önceki oturuma dönmek | Terminalde `claude --continue` |
| Bir dosyayı göstermek | Sohbette `@data/eleme/eleme_formu.xlsx` gibi `@` ile yazın |
| Ne yaptığını anlamak | "Bu betik ne yapıyor, satır satır açıkla" |
| Bir aşamayı yeniden çalıştırmak | "Aşama 2'yi yalnızca K19 ve K20 için yeniden çalıştır" |
| Durdurmak | `Esc` |

- Kısa ve net isteyin: "Aşama 2'yi çalıştır, sonra kaç aday çıktığını kurum bazında tablo halinde göster."
- Her aşamadan sonra "git commit yap" diyerek ilerlemenizi kaydettirin; bir şey bozulursa geri dönebilirsiniz.
- Claude Code'un yazdığı her betik `scripts/` klasöründe durur. Hakeme gösterilecek olan bu betikler, günlükler ve rapordur.

## 7. Dikkat edilecekler

- Claude Code, onay vermediğiniz bir komutu çalıştırmaz; ama onay verdiğiniz her şeyi yapar. İzin isteklerini okuyun.
- Özgün çalışma klasörlerinizi (ör. "TAMAMLANAN ÇALIŞMALAR") bu projeye bağlamayın; gerekiyorsa kopyalayın.
- Bulguları sempozyum metninde kullanmadan önce raporun "çalıştırma tarihi" ve sayılarını kontrol edin. Yöntem bölümünde yalnızca gerçekten yapılan işlemleri yazın.
