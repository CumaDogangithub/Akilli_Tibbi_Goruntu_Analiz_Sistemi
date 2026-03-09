# 🩺 Akıllı Tıbbi Görüntü Analiz Sistemi (ATGAS)

Yapay zeka destekli tıbbi görüntü analiz platformu. X-ray, MRI ve CT taramalarını analiz ederek potansiyel hastalıkları otomatik olarak tespit eder ve doktorlara hızlı, doğru teşhis koyma imkanı sunar.

---

## 📌 Hafta 1 - Sprint Planlaması ve Temel Altyapı

Bu belge, projenin ilk sprint'i (geliştirme döngüsü) kapsamında yapılacak görevleri listeler. Scrum Master (@CumaDogangithub) tarafından koordine edilmektedir.

### 🎯 1. Proje Tanımı ve Hedef Belirleme

---
Bu proje, derin öğrenme ve bilgisayarlı görü tekniklerini kullanarak tıbbi görüntülerin (X-ray, MRI, CT) analizini otomatize eden bir karar destek sistemidir. Amacımız, radyologların teşhis sürecini hızlandırmak ve hata payını minimize etmektir.
---

### 🔍 Kapsam
- **Girdi:** DICOM formatındaki tıbbi görüntüler.
- **İşlem:** OpenCV ile ön işleme ve TensorFlow/Keras tabanlı derin öğrenme modelleri ile analiz.
- **Çıktı:** Hastalık tespiti, anomali bölgelerinin işaretlenmesi ve Flask tabanlı web arayüzünde raporlama.

---

## ⚠️ 2. Çözüm Getirilen Problemler
Geleneksel teşhis süreçlerinde karşılaşılan ve bu projenin odaklandığı temel sorunlar:
* **Zaman Baskısı:** Acil servislerdeki yoğunluk nedeniyle görüntülerin hızlıca önceliklendirilmesi ihtiyacı.
* **İnsan Kaynaklı Hatalar:** Uzun mesai saatleri sonrası oluşan dikkat dağınıklığını yapay zeka desteğiyle dengelemek.
* **Veri Karmaşıklığı:** DICOM verilerinin ham halde yorumlanmasının zorluğu ve standardize edilmemiş görüntü kaliteleri.

---

## 🎯 3. Temel Hedefler ve Başarı Kriterleri (KPI)
Projenin teknik ve işlevsel hedefleri şunlardır:

| Hedef | Açıklama | Başarı Metriği |
| :--- | :--- | :--- |
| **Yüksek Doğruluk** | Modelin hastalıkları doğru teşhis etmesi | %90+ Accuracy / %85+ F1-Score |
| **Hızlı İşleme** | Görüntü analiz süresinin optimize edilmesi | Görüntü başına < 5 Saniye |
| **Kullanılabilirlik** | Doktorların kolayca kullanabileceği bir arayüz | Modern ve Responsive Web UI |
| **Veri Uyumluluğu** | Farklı cihazlardan gelen DICOM verilerinin okunması | %100 DICOM Standart Uyumu |

---

## 🛠️ 4. Teknoloji Yığını (Tech Stack)
Proje kapsamında kullanılacak temel araçlar:
* **Dil:** Python 3.x
* **Yapay Zeka:** TensorFlow, Keras
* **Görüntü İşleme:** OpenCV, Pydicom
* **Backend:** Flask
* **Versiyon Kontrol:** Git & GitHub

---

## 📦 5. Teslim Edilecek Modüller
Haftalık planlama dahilinde geliştirilecek temel bileşenler:
1.  ✅ **Görüntü Ön İşleme Modülü:** Gürültü giderme ve kontrast iyileştirme.
2.  ✅ **Hastalık Tespit Algoritmaları:** CNN tabanlı sınıflandırma modelleri.
3.  ✅ **Web Arayüzü:** Dosya yükleme ve sonuç görüntüleme ekranları.
4.  ✅ **Raporlama Sistemi:** Analiz sonuçlarının PDF formatında dökümü.
5.  ✅ **Performans Raporları:** Model eğitim ve test metrikleri dökümantasyonu.

---

> 👨‍💻 **Hazırlayan:** Nihal Eylül İL

### 📊 2. Gereksinim Toplama ve Analizi

---

  Akıllı Tıbbi Görüntü Analiz Sistemi'nin temel olarak hangi işlevleri yerine getirmesi gerektiği, kalite standartları ve kullanıcı ihtiyaçları aşağıda detaylandırılmıştır.
  
  ### ⚙️ 1. Fonksiyonel Gereksinimler (Functional Requirements)
  Sistemin doğrudan yerine getirmesi gereken temel işlevler:
  
  * 🖼️ **Görüntü Yükleme ve İşleme:** Sistem, tıbbi görüntülerin analiz edilebilmesi için DICOM formatındaki görüntülerin yanı sıra yaygın olarak kullanılan JPG ve PNG gibi standart formatları da desteklemelidir.
  * 🧹 **Ön İşleme (Preprocessing):** Yüklenen görüntülerdeki gürültüler, OpenCV gibi kütüphaneler kullanılarak temizlenmeli, kontrast iyileştirme (örneğin, CLAHE yöntemiyle) yapılmalı ve görüntüler, modelin gerektirdiği boyuta uygun şekilde ölçeklendirilmelidir.
  * 🦠 **Hastalık Tespiti:** TensorFlow veya Keras tabanlı yapay zeka modelleri, yüklenen tıbbi görüntüler üzerinde analiz yaparak anomali (örneğin tümör, zatürre, kırık) tespitini otomatik olarak gerçekleştirmelidir.
  * 💻 **Kullanıcı Arayüzü:** Doktorların kolayca kullanabilmesi için web tabanlı bir panel (Flask ile geliştirilebilir) sunulmalı ve analiz sonuçları görsel olarak anlaşılır biçimde gösterilmelidir.
  * 📄 **Raporlama:** Analiz sonuçları; tespit edilen bölge, güven skoru ve tarih gibi bilgilerle birlikte, PDF formatında veya web üzerinden erişilebilecek bir rapor olarak sunulmalıdır.
  
  ### 🚀 2. Fonksiyonel Olmayan Gereksinimler (Non-Functional Requirements)
  Sistemin çalışma biçimini ve kalite standartlarını belirleyen gereksinimler:
  
  * 🎯 **Doğruluk (Accuracy):** Kullanılan yapay zeka modelinin doğruluk oranı, kabul edilebilir bir eşik olan %90’ın üzerinde olmalıdır.
  * ⚡ **Hız:** Bir görüntünün yüklenip analiz edilmesi ve sonucun kullanıcıya sunulması 5 saniyeyi geçmemelidir.
  * 🔒 **Güvenlik ve Gizlilik:** Tıbbi verilerin hassasiyeti göz önünde bulundurularak, tüm görüntüler anonimleştirilmeli ve sistem KVKK/GDPR gibi veri koruma düzenlemelerine uygun şekilde tasarlanmalıdır.
  * ✨ **Kullanılabilirlik:** Kullanıcı arayüzü, doktorların mevcut iş akışlarını sekteye uğratmayacak kadar sade, anlaşılır ve erişilebilir olmalıdır.
  
  ### 🧑‍⚕️ 3. Kullanıcı Hikayeleri (User Stories)
  Sistemin geliştirilmesi sürecinde, kullanıcı ihtiyaçlarını anlamak ve önceliklendirmek için tanımlanan kullanıcı hikayeleri aşağıda özetlenmiştir. *(Bu hikayeler, Sprint planlaması dahilinde GitHub "Issues" bölümüne eklenip ilgili ekip üyelerine atanacaktır.)*
  
  | 🆔 ID | 👤 Rol | 💬 İstek | 🎯 Amaç |
  | :--- | :--- | :--- | :--- |
  | **US1** | 🩺 Doktor | Bir DICOM dosyasını sisteme yüklemek istiyorum. | Hastanın ham verisini analiz sürecine dahil edebilmek için. |
  | **US2** | ☢️ Radyolog | Görüntü üzerindeki anomaliyi işaretlenmiş şekilde görmek istiyorum. | Teşhis koyarken hangi bölgeye odaklanmam gerektiğini anlamak için. |
  | **US3** | 🤖 Sistem | Görüntüye otomatik kontrast iyileştirme uygulamak istiyorum. | Düşük kaliteli çekimlerde bile modelin doğru sonuç vermesini sağlamak için. |
  | **US4** | 🩺 Doktor | Analiz sonucunu PDF olarak indirmek istiyorum. | Hastanın dosyasına eklemek ve diğer uzmanlarla paylaşmak için. |
  | **US5** | 🎓 Akademisyen | Modelin performans metriklerini (ROC eğrisi, Confusion Matrix) görmek istiyorum. | Sistemin tıbbi güvenilirliğini doğrulamak için. |
  
  > 👨‍💻 **Hazırlayan:** Cuma Doğan

### 🛠️ 3. Teknoloji Araştırması ve Seçimi

---

Proje için uygun olan görüntü işleme kütüphanelerini (örneğin OpenCV, scikit-image) ve yapay zeka/makine öğrenimi framework'lerini (örneğin TensorFlow, PyTorch) araştırın ve karşılaştırın. Seçim nedenlerinizi açıklayın.

### 💻 4. Geliştirme Ortamı Kurulumu

---

Gerekli yazılım geliştirme araçlarını (IDE, derleyiciler, kütüphaneler) ve sürüm kontrol sistemini (Git) kurun ve yapılandırın. Ekip üyelerinin erişebileceği bir ortak geliştirme ortamı oluşturun.

### 🖼️ 5. Veri Seti İncelemesi ve Ön İşleme

---

Kullanılacak tıbbi görüntü veri setlerini (örneğin, akciğer tomografisi, MR görüntüleri) inceleyin. Veri formatlarını, boyutlarını ve olası ön işleme ihtiyaçlarını (gürültü giderme, normalizasyon) belirleyin.
