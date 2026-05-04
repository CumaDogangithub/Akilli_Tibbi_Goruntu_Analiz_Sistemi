"""
ATGAS Görüntü Ön İşleme Modülü
- DICOM (uzantı + magic bytes), PNG, JPG, JPEG desteği
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

# Bilinen DICOM uzantıları (uzantısız dosyalar magic bytes ile yakalanır)
DICOM_UZANTILARI = {".dcm", ".dicom", ".dic", ".ima"}
RESIM_UZANTILARI = {".png", ".jpg", ".jpeg"}
DESTEKLENEN_FORMATLAR = RESIM_UZANTILARI | DICOM_UZANTILARI


def _dicom_mi(dosya_yolu: str) -> bool:
    """DICOM dosyalarının ilk 132 byte'ında 128 byte preamble + 'DICM' imzası vardır.
    Uzantısız veya alışılmadık uzantılı dosyaları da yakalar."""
    try:
        with open(dosya_yolu, "rb") as f:
            f.seek(128)
            return f.read(4) == b"DICM"
    except (OSError, IOError):
        return False


def format_kontrol_et(dosya_yolu: str) -> bool:
    """Önce uzantıya bak, bilinen değilse magic bytes ile DICOM olup olmadığını kontrol et."""
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    if uzanti in DESTEKLENEN_FORMATLAR:
        return True
    # Disk'te dosya var mı? Varsa magic bytes kontrolü
    if os.path.exists(dosya_yolu) and _dicom_mi(dosya_yolu):
        return True
    return False


def dicom_dosyasi_mi(dosya_yolu: str) -> bool:
    """Dosya bir DICOM mı? Hem uzantıyı hem magic bytes'i kontrol eder.
    `.dcm`, `.dicom`, `.dic`, `.ima` veya uzantısız ama içeriği DICOM olan dosyaları yakalar."""
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    if uzanti in DICOM_UZANTILARI:
        return True
    return os.path.exists(dosya_yolu) and _dicom_mi(dosya_yolu)


def dicom_oku(dosya_yolu: str) -> np.ndarray:
    """DICOM dosyasını numpy BGR (uint8 0-255) görüntüsüne çevirir.
    HU (RescaleSlope/Intercept), Window/Level, MONOCHROME1 inversiyon ve
    multi-frame (orta slice) desteklenir."""
    if not DICOM_DESTEKLI:
        raise RuntimeError("pydicom yüklü değil. 'pip install pydicom' ile kurun.")

    ds = pydicom.dcmread(dosya_yolu, force=True)
    arr = ds.pixel_array.astype(np.float32)

    # Multi-frame ise orta slice'ı al (3D CT/MR)
    if arr.ndim == 3 and arr.shape[-1] not in (3, 4):
        arr = arr[arr.shape[0] // 2]

    # 1) HU dönüşümü (CT için kritik)
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
    if slope != 1 or intercept != 0:
        arr = arr * slope + intercept

    # 2) Window / Level (tıbbi kontrast)
    wc = getattr(ds, "WindowCenter", None)
    ww = getattr(ds, "WindowWidth", None)
    if wc is not None and ww is not None:
        wc = float(wc[0] if hasattr(wc, "__iter__") and not isinstance(wc, str) else wc)
        ww = float(ww[0] if hasattr(ww, "__iter__") and not isinstance(ww, str) else ww)
        alt = wc - ww / 2
        ust = wc + ww / 2
        arr = np.clip(arr, alt, ust)

    # 3) Min-max normalize → 0..255
    arr_min, arr_max = arr.min(), arr.max()
    if arr_max - arr_min > 0:
        arr = (arr - arr_min) / (arr_max - arr_min) * 255.0
    arr = arr.astype(np.uint8)

    # 4) MONOCHROME1 ise renk tersle (X-ray bazılarında ters çıkar)
    if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
        arr = 255 - arr

    # 5) Gri ise BGR'a çevir (OpenCV downstream BGR bekler)
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    elif arr.ndim == 3 and arr.shape[2] == 1:
        arr = cv2.cvtColor(arr.squeeze(-1), cv2.COLOR_GRAY2BGR)

    return arr


def goruntu_oku(dosya_yolu: str) -> np.ndarray:
    if not os.path.exists(dosya_yolu):
        raise FileNotFoundError(f"Görüntü bulunamadı: {dosya_yolu}")
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    # Hem uzantıdan hem magic bytes'tan DICOM tespiti
    if uzanti in DICOM_UZANTILARI or _dicom_mi(dosya_yolu):
        return dicom_oku(dosya_yolu)
    img = cv2.imread(dosya_yolu, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Görüntü okunamadı: {dosya_yolu}")
    return img


def dicom_onizleme_uret(dicom_yolu: str, cikti_yolu: str) -> str:
    """DICOM'u browser-uyumlu PNG'ye çevirip diske yazar.
    Orijinal görüntü panelinde gösterilecek olan ham önizleme.
    CLAHE/gürültü uygulanmaz — sadece tıbbi normalize (HU + Window/Level)."""
    img = dicom_oku(dicom_yolu)
    os.makedirs(os.path.dirname(cikti_yolu) or ".", exist_ok=True)
    cv2.imwrite(cikti_yolu, img)
    return cikti_yolu


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
