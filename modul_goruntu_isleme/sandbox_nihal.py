import sys
import os
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modul_goruntu_isleme.preprocessor import ImagePreprocessor, preprocess_image


def _olustur_test_png_renkli(path: str, boyut=(512, 512)):
    """Renkli (RGB) sahte tıbbi görüntü oluşturur."""
    img = np.zeros((boyut[0], boyut[1], 3), dtype=np.uint8)
    img[50:200,  50:200]  = [80,  80,  80]   # koyu gri bölge
    img[250:400, 250:400] = [180, 160, 140]  # açık bölge
    img[100:150, 300:380] = [220, 200, 180]  # anomali simülasyonu
    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def test_png_rgb_pipeline():
    print("=" * 60)
    print("TEST 1: Renkli PNG Pipeline")
    print("=" * 60)

    path = "sandbox_test_rgb.png"
    _olustur_test_png_renkli(path)

    result = preprocess_image(path)

    print(f"  Çıktı shape   : {result.shape}")
    print(f"  Dtype         : {result.dtype}")
    print(f"  Değer aralığı : [{result.min():.4f}, {result.max():.4f}]")

    assert result.shape == (384, 384, 3), f"❌ Shape hatalı: {result.shape}"
    assert result.dtype == np.float32,    f"❌ Dtype hatalı: {result.dtype}"
    assert result.min() >= 0.0,           "❌ Min değer 0'ın altında"
    assert result.max() <= 1.0,           "❌ Max değer 1'in üstünde"

    print("  ✅ Test geçti!\n")
    os.remove(path)


def test_batch_isleme():
    print("=" * 60)
    print("TEST 2: Batch İşleme — shape=(N, 384, 384, 3)")
    print("=" * 60)

    preprocessor = ImagePreprocessor()
    paths = []

    for i in range(3):
        path = f"sandbox_batch_{i}.png"
        _olustur_test_png_renkli(path, boyut=(300 + i * 50, 300 + i * 50))
        paths.append(path)

    batch = preprocessor.preprocess_batch(paths)

    print(f"  Batch shape   : {batch.shape}")
    assert batch.shape == (3, 384, 384, 3), f"❌ Batch shape hatalı: {batch.shape}"
    print("  ✅ Test geçti!\n")

    for p in paths:
        os.remove(p)


def test_bytes_pipeline():
    print("=" * 60)
    print("TEST 3: Byte Stream — Flask simülasyonu")
    print("=" * 60)

    preprocessor = ImagePreprocessor()
    path = "sandbox_bytes_test.png"
    _olustur_test_png_renkli(path)

    with open(path, "rb") as f:
        raw_bytes = f.read()

    result = preprocessor.preprocess_from_bytes(raw_bytes, "sandbox_bytes_test.png")

    print(f"  Çıktı shape   : {result.shape}")
    assert result.shape == (384, 384, 3), f"❌ Shape hatalı: {result.shape}"
    print("  ✅ Test geçti!\n")

    os.remove(path)


def test_desteklenmeyen_format():
    print("=" * 60)
    print("TEST 4: Desteklenmeyen Format Kontrolü")
    print("=" * 60)

    preprocessor = ImagePreprocessor()
    try:
        preprocessor.preprocess("goruntu.bmp")
        print("  ❌ Hata bekleniyor ama gelmedi!")
    except ValueError as e:
        print(f"  ✅ Beklenen hata yakalandı: {e}\n")


def test_pipeline_gorsellestir():
    """
    Opsiyonel: İşlenmiş görüntüyü PNG olarak kaydeder, gözle kontrol et.
    """
    print("=" * 60)
    print("TEST 5: Görsel Karşılaştırma (ham vs işlenmiş)")
    print("=" * 60)

    path = "sandbox_visual_test.png"
    _olustur_test_png_renkli(path, boyut=(600, 600))

    preprocessor = ImagePreprocessor()
    result       = preprocessor.preprocess(path)

    # [0,1] float → [0,255] uint8 kaydet
    out = (result * 255).astype(np.uint8)
    cv2.imwrite(
        "sandbox_visual_output.png",
        cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    )

    print(f"  Ham görüntü    : {path}")
    print(f"  İşlenmiş çıktı : sandbox_visual_output.png")
    print(f"  Shape          : {result.shape}")
    print("  ✅ Görsel çıktı oluşturuldu, gözle kontrol edebilirsin.\n")

    os.remove(path)


if __name__ == "__main__":
    test_png_rgb_pipeline()
    test_batch_isleme()
    test_bytes_pipeline()
    test_desteklenmeyen_format()
    test_pipeline_gorsellestir()

    print("=" * 60)
    print("🎉 Tüm sandbox testleri başarıyla tamamlandı!")
    print("   384x384 RGB pipeline göreve hazır.")
    print("=" * 60)
