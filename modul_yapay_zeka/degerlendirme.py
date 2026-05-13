"""
ATGAS — Mevcut .h5 modelleri test seti üzerinde değerlendir + TensorBoard'a logla.

Çalıştırma:
    python -m modul_yapay_zeka.degerlendirme

TensorBoard:
    tensorboard --logdir modul_yapay_zeka/logs
    → http://localhost:6006

Loglanan metrikler (her uzman için):
  - Accuracy, Macro Precision/Recall/F1
  - AUC (sadece binary modeller için)
  - Per-class precision / recall / F1
  - Confusion Matrix (görsel olarak Images sekmesinde)
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import sys
import datetime
import io
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ============================================================================
ANA_DIZIN  = os.path.dirname(os.path.abspath(__file__))
MODEL_KOK  = os.path.join(ANA_DIZIN, "modeller")
TEST_KOK   = os.path.join(ANA_DIZIN, "ornek_test_verileri")
LOG_KOK    = os.path.join(ANA_DIZIN, "logs",
                          datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
RAPOR_JSON = os.path.join(LOG_KOK, "ozet_metrikler.json")

GIRDI_BOYUTU = (384, 384)
BATCH        = 8

# Mevcut 5 uzman model — cnn_model.py'daki kütüphaneyle birebir uyumlu
UZMANLAR = {
    "xray": {
        "dosya": "atgas_xray_uzmani.h5",
        "veri":  "xray",
        "siniflar": ["Covid_19", "Normal", "Tuberkuloz", "Zaturre"],
        "isim":  "Akciğer X-Ray (Covid/Normal/Tüberküloz/Zatürre)",
    },
    "ct_akciger": {
        "dosya": "atgas_akciger_nodulu_uzmani.h5",
        "veri":  "ct/Akciger_Nodulu",
        "siniflar": ["Hastalikli", "Normal"],
        "isim":  "CT Akciğer Nodülü",
    },
    "ct_beyin": {
        "dosya": "atgas_beyin_kanamasi_uzmani.h5",
        "veri":  "ct/Beyin_Kanamasi",
        "siniflar": ["EDH", "IPH", "IVH", "Normal", "SAH", "SDH"],
        "isim":  "CT Beyin Kanaması (EDH/IPH/IVH/Normal/SAH/SDH)",
    },
    "mri_fitik": {
        "dosya": "atgas_bel_fitigi_uzmani.h5",
        "veri":  "mri/Lomber_Disk_Hernisi",
        "siniflar": ["Hastalikli", "Normal"],
        "isim":  "MRI Lomber Disk Hernisi (Bel Fıtığı)",
    },
    "mri_tumor": {
        "dosya": "atgas_meningioma_uzmani.h5",
        "veri":  "mri/Meningioma",
        "siniflar": ["Hastalikli", "Normal"],
        "isim":  "MRI Meningioma (Beyin Tümörü)",
    },
}


# ============================================================================
def cm_resim_olustur(cm, siniflar, baslik):
    """Confusion matrix matplotlib figure → numpy uint8 (TensorBoard images)."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=110)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_title(baslik, fontsize=11, pad=14)
    ax.set_xticks(range(len(siniflar)))
    ax.set_xticklabels(siniflar, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(siniflar)))
    ax.set_yticklabels(siniflar, fontsize=9)
    ax.set_xlabel("Tahmin", fontsize=10)
    ax.set_ylabel("Gerçek", fontsize=10)
    esik = cm.max() / 2.0 if cm.max() > 0 else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > esik else "black",
                    fontsize=10, fontweight="bold")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = tf.image.decode_png(buf.getvalue(), channels=4)
    return tf.expand_dims(img, 0)


def test_seti_yukle(klasor, siniflar):
    """image_dataset_from_directory ile test verisini yükler."""
    return tf.keras.utils.image_dataset_from_directory(
        klasor,
        labels="inferred",
        label_mode="int",
        class_names=siniflar,
        image_size=GIRDI_BOYUTU,
        batch_size=BATCH,
        shuffle=False,
    )


def degerlendir(uzman_kodu, cfg, writer, ozet_dict):
    """Tek bir modeli değerlendirir, TensorBoard'a metrikleri yazar."""
    model_yolu = os.path.join(MODEL_KOK, cfg["dosya"])
    test_dizini = os.path.join(TEST_KOK, cfg["veri"])

    if not os.path.exists(model_yolu):
        print(f"  ❌ Model bulunamadı: {model_yolu}")
        return
    if not os.path.isdir(test_dizini):
        print(f"  ❌ Test dizini yok: {test_dizini}")
        return

    print(f"\n📊 {uzman_kodu} → {cfg['isim']}")

    # Modeli yükle
    model = tf.keras.models.load_model(model_yolu, compile=False)

    # Test seti
    ds = test_seti_yukle(test_dizini, cfg["siniflar"])

    # Tahminler
    y_true, y_pred_proba = [], []
    for x, y in ds:
        p = model(x, training=False).numpy()
        y_true.extend(y.numpy().tolist())
        y_pred_proba.extend(p.tolist())
    y_true = np.array(y_true)
    y_pred_proba = np.array(y_pred_proba)
    y_pred = np.argmax(y_pred_proba, axis=1)

    if len(y_true) == 0:
        print("  ⚠ Test verisi boş, atlandı.")
        return

    # Metrikler
    accuracy = float((y_pred == y_true).mean())
    rapor = classification_report(
        y_true, y_pred,
        target_names=cfg["siniflar"],
        output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=range(len(cfg["siniflar"])))
    macro_f1        = float(rapor["macro avg"]["f1-score"])
    macro_precision = float(rapor["macro avg"]["precision"])
    macro_recall    = float(rapor["macro avg"]["recall"])

    auc = None
    if len(cfg["siniflar"]) == 2 and len(np.unique(y_true)) == 2:
        try:
            auc = float(roc_auc_score(y_true, y_pred_proba[:, 1]))
        except ValueError:
            pass  # tek sınıf varsa

    # --- TensorBoard'a yaz ---
    with writer.as_default():
        tf.summary.scalar(f"{uzman_kodu}/accuracy", accuracy, step=0)
        tf.summary.scalar(f"{uzman_kodu}/macro_f1", macro_f1, step=0)
        tf.summary.scalar(f"{uzman_kodu}/macro_precision", macro_precision, step=0)
        tf.summary.scalar(f"{uzman_kodu}/macro_recall", macro_recall, step=0)
        if auc is not None:
            tf.summary.scalar(f"{uzman_kodu}/auc", auc, step=0)
        # Per-class metrikler
        for sinif in cfg["siniflar"]:
            if sinif in rapor:
                tf.summary.scalar(f"{uzman_kodu}/per_class_precision/{sinif}",
                                  float(rapor[sinif]["precision"]), step=0)
                tf.summary.scalar(f"{uzman_kodu}/per_class_recall/{sinif}",
                                  float(rapor[sinif]["recall"]), step=0)
                tf.summary.scalar(f"{uzman_kodu}/per_class_f1/{sinif}",
                                  float(rapor[sinif]["f1-score"]), step=0)
        # Confusion matrix görsel olarak
        tf.summary.image(
            f"{uzman_kodu}/confusion_matrix",
            cm_resim_olustur(cm, cfg["siniflar"], cfg["isim"]),
            step=0,
        )
        # Metin raporu
        rapor_metin = classification_report(
            y_true, y_pred, target_names=cfg["siniflar"], zero_division=0,
        )
        tf.summary.text(
            f"{uzman_kodu}/classification_report",
            f"```\n{rapor_metin}\n```",
            step=0,
        )
    writer.flush()

    # Konsol özeti
    print(f"  ✓ Test örneği:    {len(y_true)}")
    print(f"  ✓ Accuracy:       {accuracy:.4f}")
    print(f"  ✓ Macro F1:       {macro_f1:.4f}")
    print(f"  ✓ Macro Precision:{macro_precision:.4f}")
    print(f"  ✓ Macro Recall:   {macro_recall:.4f}")
    if auc is not None:
        print(f"  ✓ AUC:            {auc:.4f}")
    print(f"  ✓ Confusion Matrix:\n{cm}")

    # JSON özetine kaydet
    ozet_dict[uzman_kodu] = {
        "isim": cfg["isim"],
        "test_ornek_sayisi": int(len(y_true)),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "auc": auc,
        "confusion_matrix": cm.tolist(),
        "siniflar": cfg["siniflar"],
        "per_class": {
            s: {
                "precision": float(rapor[s]["precision"]),
                "recall":    float(rapor[s]["recall"]),
                "f1":        float(rapor[s]["f1-score"]),
                "support":   int(rapor[s]["support"]),
            }
            for s in cfg["siniflar"] if s in rapor
        },
    }


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print(" ATGAS — Model Değerlendirme + TensorBoard Loglama")
    print("=" * 70)

    os.makedirs(LOG_KOK, exist_ok=True)
    writer = tf.summary.create_file_writer(LOG_KOK)
    ozet = {}

    for kod, cfg in UZMANLAR.items():
        try:
            degerlendir(kod, cfg, writer, ozet)
        except Exception as e:
            print(f"  ❌ {kod} hata: {e}")

    # JSON özet rapor
    with open(RAPOR_JSON, "w", encoding="utf-8") as f:
        json.dump(ozet, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 70)
    print(" ÖZET")
    print("=" * 70)
    for kod, m in ozet.items():
        auc = f"AUC={m['auc']:.3f}" if m["auc"] is not None else ""
        print(f"  {kod:12} acc={m['accuracy']:.3f}  f1={m['macro_f1']:.3f}  {auc}")
    print()
    print(f"  📁 Loglar: {LOG_KOK}")
    print(f"  📁 JSON:   {RAPOR_JSON}")
    print()
    print("  ▶ TensorBoard'u başlat:")
    print(f"     tensorboard --logdir {os.path.relpath(os.path.dirname(LOG_KOK))}")
    print("     ▶ http://localhost:6006")


if __name__ == "__main__":
    main()
