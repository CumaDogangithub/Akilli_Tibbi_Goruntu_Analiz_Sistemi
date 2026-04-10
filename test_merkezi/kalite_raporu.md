# 🩺 ATGAS Görüntü Ön İşleme Modülü Kalite Raporu

**Tarih:** 10 Nisan 2026  
**:** Elif İkra Çakmak  
**Proje:** Akıllı Tıbbi Görüntü Analiz Sistemi (ATGAS)  

---

## 1. Modül Amacı ve Kapsamı
Bu rapor, `ImagePreprocessor` sınıfının teknik yeterliliğini ve **EfficientNetV2-M** derin öğrenme mimarisiyle olan uyumluluğunu belgelemek amacıyla hazırlanmıştır. Modül, tıbbi görüntülerin (DICOM, PNG, JPG) analiz öncesi standartlaştırılmasını sağlar.

## 2. Uygulanan Teknik Standartlar

### 📏 Boyutlandırma (Resizing)
* **Hedef Çözünürlük:** 384x384 piksel.
* **Açıklama:** Modelin karmaşıklığı ve doğruluk oranı arasındaki dengeyi korumak için mimari standartlara uygun interpolasyon yöntemleri kullanılmıştır.

### ✨ Kontrast İyileştirme (CLAHE)
* **Yöntem:** Contrast Limited Adaptive Histogram Equalization.
* **Parametreler:** `clipLimit=2.0`, `tileGridSize=(8, 8)`.
* **Etki:** Tıbbi görüntülerdeki (Röntgen, BT) düşük kontrastlı alanlar, gürültü artırılmadan belirginleştirilmiştir. İşlem, renk bozulmasını önlemek için **LAB renk uzayında** gerçekleştirilmiştir.

### 🔢 Normalizasyon ve Veri Tipi
* **Yöntem:** Min-Max Normalization [0.0, 1.0].
* **Veri Tipi:** `float32`.
* **Fayda:** Gradyan patlamalarını önleyerek modelin eğitim ve çıkarım (inference) sürecini stabilize eder.

---

## 3. Birim Test (Unit Test) Doğrulaması
Modül, sandbox ortamında hazırlanan `test_moduller.py` senaryolarından **%100 başarı** ile geçmiştir.

| Test Kriteri | Beklenen Sonuç | Gerçekleşen Sonuç | Durum |
| :--- | :--- | :--- | :---: |
| Giriş Kanalı İşleme | RGB Dönüşümü | RGB (3 Kanal) | ✅ |
| Çıktı Matrisi | (384, 384, 3) | (384, 384, 3) | ✅ |
| Veri Tipi Kontrolü | `numpy.float32` | `numpy.float32` | ✅ |
| Piksel Aralığı | 0.0 - 1.0 | 0.0 - 1.0 | ✅ |
| Boş Dosya Kontrolü | `None` Return | `None` Return | ✅ |

---

## 4. Sistem Gereksinimleri ve Bağımlılıklar
Modülün sorunsuz çalışması için aşağıdaki kütüphane sürümleri sisteme dahil edilmiştir:
* **OpenCV (`opencv-python`):** Görüntü işleme pipeline'ı için.
* **NumPy:** Matris operasyonları ve normalizasyon için.
* **PyDicom:** `.dcm` formatındaki tıbbi verilerin entegrasyonu için.

---

## 5. Sonuç ve Onay
Yapılan testler sonucunda modülün, projenin ana iş akışına dahil edilmeye **uygun** olduğu tespit edilmiştir. 

**Durum:** 🚀 Yayına Hazır
