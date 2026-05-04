"""
ATGAS Görüntü Ön İşleme Modülü
- DICOM, PNG, JPG, JPEG desteği
- CLAHE ile kontrast iyileştirme
- Gürültü giderme
- Yeniden boyutlandırma
"""

import os
import cv2
import numpy as np

try:
    import pydicom
    DICOM_DESTEKLI = True
except ImportError:
    DICOM_DESTEKLI = False

DESTEKLENEN_FORMATLAR = {".png", ".jpg", ".jpeg", ".dcm", ".dicom"}


def format_kontrol_et(dosya_yolu: str) -> bool:
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    return uzanti in DESTEKLENEN_FORMATLAR


def dicom_oku(dosya_yolu: str) -> np.ndarray:
    if not DICOM_DESTEKLI:
        raise RuntimeError("pydicom yüklü değil. requirements.txt'ten pydicom kurun.")
    ds = pydicom.dcmread(dosya_yolu)
    pixel_array = ds.pixel_array.astype(np.float32)
    pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min() + 1e-8)
    pixel_array = (pixel_array * 255).astype(np.uint8)
    if len(pixel_array.shape) == 2:
        pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2BGR)
    return pixel_array


def goruntu_oku(dosya_yolu: str) -> np.ndarray:
    if not os.path.exists(dosya_yolu):
        raise FileNotFoundError(f"Görüntü bulunamadı: {dosya_yolu}")
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    if uzanti in {".dcm", ".dicom"}:
        return dicom_oku(dosya_yolu)
    img = cv2.imread(dosya_yolu, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Görüntü okunamadı: {dosya_yolu}")
    return img


def clahe_uygula(img: np.ndarray, clip_limit: float = 2.0, tile_grid_size=(8, 8)) -> np.ndarray:
    """Kontrast iyileştirme — düşük kaliteli tıbbi görüntüler için."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def gurultu_gider(img: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)


def hazirla(dosya_yolu: str, hedef_boyut=(384, 384), cikti_yolu: str | None = None) -> str:
    """
    Tıbbi görüntüyü modele girmeye hazırlar:
      1. Format dönüştürme (DICOM → PNG)
      2. CLAHE kontrast iyileştirme
      3. Hafif gürültü giderme
      4. Boyutlandırma
    Diske kaydedilen normalize PNG'nin yolunu döner.
    """
    if not format_kontrol_et(dosya_yolu):
        raise ValueError(f"Desteklenmeyen format: {dosya_yolu}")

    img = goruntu_oku(dosya_yolu)
    img = clahe_uygula(img)
    img = gurultu_gider(img)
    img = cv2.resize(img, hedef_boyut, interpolation=cv2.INTER_AREA)

    if cikti_yolu is None:
        kok, _ = os.path.splitext(dosya_yolu)
        cikti_yolu = kok + "_islenmis.png"
    os.makedirs(os.path.dirname(cikti_yolu) or ".", exist_ok=True)
    cv2.imwrite(cikti_yolu, img)
    return cikti_yolu
