import cv2
import numpy as np
import os

# --- ATGAS Görüntü Ön İşleme Sınıfı ---
class ImagePreprocessor:
    def __init__(self, target_size=(384, 384)):
        self.target_size = target_size
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def preprocess(self, path):
        img = cv2.imread(path)
        if img is None: return None
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, self.target_size)
        # Kontrast İyileştirme (CLAHE)
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        img = cv2.merge([l, a, b])
        img = cv2.cvtColor(img, cv2.COLOR_LAB2RGB)
        return img.astype(np.float32) / 255.0

# --- Birim Test Senaryosu ---
def test_pipeline():
    print("\n" + "="*50)
    print("🧪 GÖRÜNTÜ ÖN İŞLEME MODÜLÜ BİRİM TESTLERİ")
    print("="*50)
    
    # 1. Test Verisi Oluşturma
    dummy_path = "test_image.png"
    dummy_img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    cv2.imwrite(dummy_path, dummy_img)
    
    # 2. Modülü Çalıştırma
    preprocessor = ImagePreprocessor()
    result = preprocessor.preprocess(dummy_path)
    
    # 3. Doğrulama (Assertions)
    print(f"🔹 Girdi Boyutu: 512x512  ->  Çıktı Boyutu: {result.shape}")
    print(f"🔹 Piksel Aralığı: [{result.min():.2f}, {result.max():.2f}]")
    
    assert result.shape == (384, 384, 3), "❌ HATA: Çıktı boyutu yanlış!"
    assert result.dtype == np.float32, "❌ HATA: Veri tipi yanlış!"
    
    os.remove(dummy_path)
    print("\n✅ TÜM TESTLER BAŞARIYLA TAMAMLANDI!")
    print("🚀 Modül EfficientNetV2-M girişi için hazır.")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_pipeline()

