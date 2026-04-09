import cv2
import numpy as np
import os
import io

try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False
    print("[UYARI] pydicom kurulu değil. 'pip install pydicom' komutunu çalıştır.")

# ─── Sabitler ─────────────────────────────────────────────────────────────────
TARGET_SIZE    = (384, 384)   # EfficientNetV2-M giriş boyutu (güncel)
CLAHE_CLIP    = 2.0
CLAHE_GRID    = (8, 8)
SUPPORTED_EXT  = {".dcm", ".png", ".jpg", ".jpeg", ".nifti"}


class ImagePreprocessor:
    """
    ATGAS - Görüntü Ön İşleme Modülü
    ─────────────────────────────────
    Desteklenen formatlar : .dcm, .png, .jpg, .jpeg
    Pipeline (DICOM)      : Okuma → Resize → CLAHE → Gray→RGB → Normalizasyon
    Pipeline (PNG/JPG)    : Okuma(RGB) → Resize → CLAHE(LAB) → Normalizasyon
    Çıktı                 : np.ndarray, shape=(384,384,3), dtype=float32, [0,1]
    """

    def __init__(self, target_size: tuple = TARGET_SIZE):
        self.target_size = target_size
        # DICOM için CLAHE
        self.clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP,
            tileGridSize=CLAHE_GRID
        )

    # ─── Okuma ────────────────────────────────────────────────────────────────

    def _read_dicom(self, file_path: str) -> np.ndarray:
        """DICOM dosyasını okur → uint8 grayscale array döndürür."""
        if not PYDICOM_AVAILABLE:
            raise ImportError("pydicom kurulu değil: pip install pydicom")

        ds     = pydicom.dcmread(file_path)
        pixels = ds.pixel_array.astype(np.float32)

        # 3D MRI stack ise orta dilimi al
        if pixels.ndim == 3:
            pixels = pixels[pixels.shape[0] // 2]

        # DICOM piksel değerlerini 0-255 aralığına normalize et
        lo, hi = pixels.min(), pixels.max()
        if hi > lo:
            pixels = (pixels - lo) / (hi - lo) * 255.0

        return pixels.astype(np.uint8)

    def _read_dicom_bytes(self, file_bytes: bytes) -> np.ndarray:
        """Flask'tan gelen DICOM byte stream'ini okur."""
        if not PYDICOM_AVAILABLE:
            raise ImportError("pydicom kurulu değil: pip install pydicom")

        ds     = pydicom.dcmread(io.BytesIO(file_bytes))
        pixels = ds.pixel_array.astype(np.float32)

        if pixels.ndim == 3:
            pixels = pixels[pixels.shape[0] // 2]

        lo, hi = pixels.min(), pixels.max()
        if hi > lo:
            pixels = (pixels - lo) / (hi - lo) * 255.0

        return pixels.astype(np.uint8)

    def _read_standard(self, file_path: str) -> np.ndarray:
        """PNG / JPG → BGR oku, RGB'ye çevir."""
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(f"Görüntü okunamadı: {file_path}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ─── Pipeline adımları ────────────────────────────────────────────────────

    def _resize(self, img: np.ndarray) -> np.ndarray:
        return cv2.resize(img, self.target_size, interpolation=cv2.INTER_AREA)

    def _apply_clahe_gray(self, img: np.ndarray) -> np.ndarray:
        """DICOM (grayscale) görüntüye CLAHE uygular."""
        return self.clahe.apply(img)

    def _apply_clahe_rgb(self, img: np.ndarray) -> np.ndarray:
        """
        Renkli (RGB) görüntüye CLAHE uygular.
        LAB renk uzayında sadece L kanalına uygulanır;
        renk bilgisi bozulmaz.
        """
        lab            = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b        = cv2.split(lab)
        l_clahe        = self.clahe.apply(l)
        lab_clahe      = cv2.merge([l_clahe, a, b])
        return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)

    def _normalize(self, img: np.ndarray) -> np.ndarray:
        return img.astype(np.float32) / 255.0

    # ─── DICOM pipeline ───────────────────────────────────────────────────────
    def _run_pipeline_dicom(self, img_gray: np.ndarray) -> np.ndarray:
        """
        DICOM'a özel pipeline:
        resize → CLAHE(gray) → Gray→RGB → normalize
        """
        img = self._resize(img_gray)
        img = self._apply_clahe_gray(img)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        img = self._normalize(img)
        return img

    # ─── PNG/JPG pipeline ─────────────────────────────────────────────────────
    def _run_pipeline_rgb(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        Standart görüntü pipeline'ı (grayscale yok):
        resize → CLAHE(LAB) → normalize
        """
        img = self._resize(img_rgb)
        img = self._apply_clahe_rgb(img)
        img = self._normalize(img)
        return img

    # ─── Dışa açık fonksiyonlar ───────────────────────────────────────────────

    def preprocess(self, file_path: str) -> np.ndarray:
        """
        Dosya yolundan görüntüyü işler.

        Kullanım:
            preprocessor = ImagePreprocessor()
            img = preprocessor.preprocess("scan.dcm")   # (384, 384, 3) float32
            img = preprocessor.preprocess("xray.jpg")   # (384, 384, 3) float32
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".dcm":
            img_gray = self._read_dicom(file_path)
            return self._run_pipeline_dicom(img_gray)
        elif ext in SUPPORTED_EXT:
            img_rgb = self._read_standard(file_path)
            return self._run_pipeline_rgb(img_rgb)
        else:
            raise ValueError(
                f"Desteklenmeyen format: '{ext}'. "
                f"Desteklenen: {SUPPORTED_EXT}"
            )

    def preprocess_from_bytes(
        self, file_bytes: bytes, filename: str = "upload.png"
    ) -> np.ndarray:
        """
        Flask route'larından byte olarak gelen görüntüyü işler.

        Kullanım (app.py içinde):
            raw = request.files['image'].read()
            img = preprocessor.preprocess_from_bytes(raw, "scan.dcm")
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".dcm":
            img_gray = self._read_dicom_bytes(file_bytes)
            return self._run_pipeline_dicom(img_gray)
        else:
            np_arr  = np.frombuffer(file_bytes, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise ValueError(f"Görüntü decode edilemedi: {filename}")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            return self._run_pipeline_rgb(img_rgb)

    def preprocess_batch(self, file_paths: list) -> np.ndarray:
        """
        Çok sayıda dosyayı toplu işler.
        Döndürür: np.ndarray shape=(N, 384, 384, 3)
        """
        batch, errors = [], []

        for path in file_paths:
            try:
                batch.append(self.preprocess(path))
            except Exception as e:
                errors.append({"dosya": path, "hata": str(e)})

        if errors:
            print(f"[UYARI] {len(errors)} dosya işlenemedi:")
            for err in errors:
                print(f"  ✗ {err['dosya']}: {err['hata']}")

        return np.array(batch, dtype=np.float32)


# ─── Singleton & kısa kullanım fonksiyonları ──────────────────────────────────

_instance: ImagePreprocessor | None = None


def get_preprocessor() -> ImagePreprocessor:
    global _instance
    if _instance is None:
        _instance = ImagePreprocessor()
    return _instance


def preprocess_image(file_path: str) -> np.ndarray:
    """
    Diğer modüllerin kullandığı kısa yol.

    Import örneği (modul_yapay_zeka/cnn_model.py içinde):
        from modul_goruntu_isleme.preprocessor import preprocess_image
        tensor = preprocess_image("hasta.dcm")  # → (384, 384, 3)
    """
    return get_preprocessor().preprocess(file_path)


def preprocess_from_bytes(file_bytes: bytes, filename: str = "upload.png") -> np.ndarray:
    """
    app.py içinde Flask route'larından direkt çağrılır.
    """
    return get_preprocessor().preprocess_from_bytes(file_bytes, filename)
