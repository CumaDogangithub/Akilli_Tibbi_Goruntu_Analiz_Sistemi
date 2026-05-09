# 🩺 Akıllı Tıbbi Görüntü Analiz Sistemi (ATGAS)

Yapay zeka destekli tıbbi görüntü analiz platformu. X-ray, MRI ve CT taramalarını analiz ederek potansiyel hastalıkları otomatik olarak tespit eder ve doktorlara hızlı, doğru teşhis koyma imkanı sunar.

## 🚀 Projenin Tüm Aşamaları

1. **Gereksinim Analizi ve Kapsam Belirleme:** Geleneksel teşhis süreçlerinde karşılaşılan zaman baskısı, insan kaynaklı hatalar ve karmaşık DICOM verilerinin analiz edilmesinin çözümü olarak tasarlandı. %90+ doğruluk oranı ve 5 saniyeden düşük analiz süresi hedeflendi.
2. **Veri Toplama ve Ön İşleme:** Çeşitli görüntü formatları (DICOM, JPG, PNG) entegre edildi. Ham veriler dengesiz olduğu için Data Augmentation (Yatay Çevirme, Döndürme vb.) yöntemleriyle iyileştirildi. 
3. **Görüntü İşleme (Image Preprocessing):** Görüntüler, modele gönderilmeden önce (384x384) çözünürlüğüne getirildi. Tıbbi detayları (kemik, doku vb.) en iyi şekilde vurgulamak için LAB uzayında **CLAHE** (Contrast Limited Adaptive Histogram Equalization) uygulandı ve Min-Max Normalizasyonu ile değerler (0.0 - 1.0) aralığına çekildi. (float32 tipinde).
4. **Model Seçimi ve Eğitimi:** PyTorch yerine entegrasyonu ve üretim(production) kolaylığı sebebiyle TensorFlow/Keras Kütüphaneleri seçildi. 
5. **Backend ve Entegrasyon:** Python ve Flask kullanılarak modeller için gelişmiş bir REST API altyapısı geliştirildi. 
6. **Arayüz (UI) ve PDF Raporlama:** Doktorların pratik şekilde görüntü yükleyip anomalileri görebileceği UI ile değerlendirme sonuçlarını PDF olarak indirmelerini sağlayan raporlama modülü tamamlandı.

---

## 🛠 Kullanılan Algoritmalar

- **Görüntü İşleme ve Ön İşleme Algoritmaları:** 
  - Boyutlandırma ve İnterpolasyon
  - CLAHE (Contrast Limited Adaptive Histogram Equalization) - Kontrast Artırıcı Algoritma
  - Min-Max Normalization
- **Yapay Zeka & Derin Öğrenme Algoritmaları:**
  - **Evrişimli Sinir Ağları (CNN)**
  - Derin Öğrenme Mimari Modeli: **EfficientNetV2-M**

---

## 📂 Veri Seti (Dataset)

Veri setimizde sınıfların dengesiz durumu çözmek için sentetik verilerle (Data Augmentation) örnekler çoğaltılmıştır. Veriler genel olarak CT, MRI ve X-Ray taramalarından oluşmaktadır:

*   **CT (Bilgisayarlı Tomografi):** 
    *   *Akciğer Nodülü:* Hastalıklı, Normal
    *   *Beyin Kanaması:* EDH, IPH, IVH, SAH, SDH, Normal
*   **MRI (Manyetik Rezonans):**
    *   *Lomber Disk Hernisi (Bel Fıtığı):* Hastalıklı, Normal
    *   *Meningioma (Beyin Tümörü):* Hastalıklı, Normal
*   **X-Ray (Röntgen):**
    *   *Akciğer Tarama Sınıfları:* Covid-19, Normal, Tüberküloz, Zatürre

---

## 🏗 Model Mimarisi

*   **Model Türü:** EfficientNetV2-M (TensorFlow / Keras üzerinden)
*   **Giriş (Input) Katmanı:** (384, 384, 3) boyutunda, 0-1 arasına Normalize edilmiş RGB Görüntü Matrisi.
*   **Çıkış (Output) Katmanı:** Farklı beyin ve akciğer hastalığı sınıfları için sınıf sayısına uygun output (Softmax veya Sigmoid aktivasoynu).
*   **Optimizasyon:** TF XLA ayarlamalarıyla bellek performansı iyileştirildi. Sınıfların olasılık değerleri alınarak front-end'e aktarıldı.

---

## 🎯 Sonuçlar ve Metrikler

*   **Modül Testi:** Geliştirilen ön işleme (ImagePreprocessor) Unit testlerinden **%100 Başarı** ile geçmiştir.
*   **Hız:** Seçilen mimariler (EfficientNetV2-M, OpenCV CLAHE) ile görüntü analizi süresi **< 5 Saniye** kriterine ulaşmıştır.
*   **Doğruluk:** Modeller dengelenmiş veri seti sayesinde belirlenen hedeflerin (%90 Accuracy / %85 F1-Score) karşılanmasında gerekli altyapıyı sağlamıştır.

---

## 🌐 API Dokümantasyonu

Web arayüzünde ve dış entegrasyonlarda kullanılmak üzere tasarlanan uç noktalar:

### POST /api/analiz
*   **İşlev:** Yüklenen görüntünün analiz sürecini başlatır ve yapay zeka modelini çalıştırır.
*   **İstek Yapısı (FormData):** 
    *   ile: Tıbbi görüntü dosyası (DCM, JPG, PNG)
    *   uzmanlik: Gerekli analiz türevi (örn: xray, ct_beyin)
*   **Dönüş Değeri:** Tahmin edilen hastalık, güven yüzdesi listesi ve tespit görsel yolunu (URL) içeren JSON veri kümesi.

### POST /api/save_draft
*   **İşlev:** Doktor panelinden süren teşhis sürecini "Taslak" (Draft) olarak geçici kaydeder.
*   **İstek Yapısı:** Analiz sonuçlarını ve hasta bilgilerini barındıran JSON bloğu.

### POST /api/save_report
*   **İşlev:** Onaylanan analizi kalıcı veritabanına rapor olarak kaydeder.
*   **Dönüş Değeri:** Başarı durumu ve ilişkili apor_id değerini içeren JSON objesi.

### POST /api/iptal (veya GET)
*   **İşlev:** Arka planda fazla uzun süren veya gereksiz analiz sürecini durdurmak için asenkron istektir.

### DELETE /api/raporlar/<int:rapor_id>
*   **İşlev:** Belirtilen kimliğe (apor_id) sahip raporu sistemden veritabanı uçlarında kalıcı olarak siler.

### GET /raporlar/<int:rapor_id>/pdf
*   **İşlev:** İlgili raporun özetini, hasta formlarını ve yapay zekanın işaretlendiği görseli içeren hazır **PDF dokümanı** döndürür (File Download).

---

## 👥 Geliştirici Ekip
Bu proje, Agile/Scrum metodolojisi takip edilerek aşağıdaki ekip tarafından geliştirilmektedir:
* 👑 **Cuma Doğan** - Yazılım Mühendisi (Scrum Master)
* 💻 **Nihal Eylül İl** - Yazılım Mühendisi
* 💻 **Ozan Diyar Ay** - Yazılım Mühendisi
* 💻 **Esmanur Ulu** - Yazılım Mühendisi
* 💻 **Elif İkra Çakmak** - Yazılım Mühendisi
