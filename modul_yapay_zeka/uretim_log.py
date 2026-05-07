"""
ATGAS — Üretim Verisi TensorBoard Log Üretici

DB'deki AnalizRaporu kayıtlarını işler ve TensorBoard'a "üretim" metriklerini yazar.
`degerlendirme.py` test seti üzerinde sabit metrikler üretirken (model + test seti
değişmediği için her run aynı çıkar), bu modül **canlı veriyi** loglar — yeni hasta
analizi geldikçe sayılar değişir, dolayısıyla TB grafikleri anlamlı olarak değişir.

Step olarak unix timestamp kullanılır → her tetikleme yeni bir veri noktası ekler;
TB tek bir run altında zaman serisi çizgisi gösterir.

Loglanan metrikler:
  - Genel: toplam analiz, anomali/normal sayım & oran, ort güven, onay oranı
  - Tip bazlı (MR/CT/X-Ray): sayım, anomali oranı, ort güven
  - Seviye bazlı (Kritik/Orta/Temiz): sayım
  - Histogram: güven skoru dağılımı
  - Text: özet rapor

Çağırma şekilleri:
  1) Flask request içinde (önerilen):
       from modul_yapay_zeka.uretim_log import uretim_loglarini_yaz
       sonuc = uretim_loglarini_yaz()
  2) CLI (standalone):
       python -m modul_yapay_zeka.uretim_log
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import sys
import time
import datetime

import tensorflow as tf


ANA_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ANA_DIZIN, "modul_yapay_zeka", "logs", "uretim")


def _tag_temizle(s: str) -> str:
    """TB tag'leri için karakter sanitize (boşluk, /, \\ kaldır)."""
    return (s or "Bilinmiyor").replace(" ", "_").replace("/", "_").replace("\\", "_").replace("-", "_")


def uretim_loglarini_yaz():
    """DB'deki tüm AnalizRaporu kayıtlarından üretim metriklerini hesaplar
    ve TensorBoard'a yazar. Flask app context içinde çağrılmalıdır.

    Returns:
        dict: özet metrikler (toplam, anomali, normal, ort_guven, onaylanan, step)
    """
    from modul_veritabani import AnalizRaporu

    step = int(time.time())
    os.makedirs(LOG_DIR, exist_ok=True)
    writer = tf.summary.create_file_writer(LOG_DIR)

    raporlar = AnalizRaporu.query.all()
    toplam = len(raporlar)

    if toplam == 0:
        with writer.as_default():
            tf.summary.text(
                "uretim/durum",
                "DB'de henüz analiz yok. En az bir hasta taraması yapın.",
                step=step,
            )
        writer.flush()
        writer.close()
        return {"toplam": 0, "step": step, "mesaj": "DB boş"}

    # === Genel sayımlar ===
    anomali = sum(1 for r in raporlar if r.ham_sinif and r.ham_sinif != "Normal")
    normal = toplam - anomali
    onaylanan = sum(1 for r in raporlar if r.durum == "Kaydedildi")
    taslak = toplam - onaylanan
    guvenler = [float(r.dogruluk_orani or 0) for r in raporlar]
    ort_guven = sum(guvenler) / toplam

    # === Tip bazlı (MR / CT / X-Ray) ===
    tipler = {}
    for r in raporlar:
        tipler.setdefault(r.tarama_tipi or "Bilinmiyor", []).append(r)

    # === Seviye bazlı (Kritik / Orta / Temiz) ===
    seviyeler = {"Kritik": 0, "Orta": 0, "Temiz": 0}
    for r in raporlar:
        sev = r.seviye or "Orta"
        seviyeler[sev] = seviyeler.get(sev, 0) + 1

    with writer.as_default():
        # ---- Genel ----
        tf.summary.scalar("uretim/01_toplam_analiz", toplam, step=step)
        tf.summary.scalar("uretim/02_anomali_sayisi", anomali, step=step)
        tf.summary.scalar("uretim/03_normal_sayisi", normal, step=step)
        tf.summary.scalar("uretim/04_anomali_orani", anomali / toplam, step=step)
        tf.summary.scalar("uretim/05_ortalama_guven_yuzde", ort_guven, step=step)
        tf.summary.scalar("uretim/06_onaylanan_rapor", onaylanan, step=step)
        tf.summary.scalar("uretim/07_taslak_rapor", taslak, step=step)
        tf.summary.scalar("uretim/08_onay_orani", onaylanan / toplam, step=step)

        # ---- Histogram: güven skoru dağılımı ----
        tf.summary.histogram("uretim/guven_skoru_dagilimi", guvenler, step=step)

        # ---- Tip bazlı ----
        for tip, lst in tipler.items():
            n = len(lst)
            tip_anom = sum(1 for r in lst if r.ham_sinif and r.ham_sinif != "Normal")
            tip_guv = [float(r.dogruluk_orani or 0) for r in lst]
            tip_ort = sum(tip_guv) / n if n else 0
            tag = _tag_temizle(tip)
            tf.summary.scalar(f"tip_{tag}/sayim", n, step=step)
            tf.summary.scalar(f"tip_{tag}/anomali_orani", tip_anom / n if n else 0, step=step)
            tf.summary.scalar(f"tip_{tag}/ort_guven_yuzde", tip_ort, step=step)

        # ---- Seviye bazlı ----
        for sev, n in seviyeler.items():
            tf.summary.scalar(f"seviye_{_tag_temizle(sev)}", n, step=step)

        # ---- Özet metin ----
        zaman = datetime.datetime.fromtimestamp(step).strftime("%Y-%m-%d %H:%M:%S")
        tip_ozet = ", ".join(f"{t}={len(l)}" for t, l in sorted(tipler.items()))
        ozet = (
            f"## ATGAS Üretim Snapshot\n\n"
            f"- **Zaman:** {zaman}\n"
            f"- **Toplam analiz:** {toplam}\n"
            f"- **Anomali:** {anomali} (%{100*anomali/toplam:.1f})\n"
            f"- **Normal:** {normal} (%{100*normal/toplam:.1f})\n"
            f"- **Onaylanan rapor:** {onaylanan} (%{100*onaylanan/toplam:.1f})\n"
            f"- **Taslak:** {taslak}\n"
            f"- **Ortalama güven:** %{ort_guven:.1f}\n"
            f"- **Tarama tipi dağılımı:** {tip_ozet}\n"
            f"- **Seviye dağılımı:** " + ", ".join(f"{s}={n}" for s, n in seviyeler.items())
        )
        tf.summary.text("uretim/ozet", ozet, step=step)

    writer.flush()
    writer.close()

    return {
        "toplam": toplam,
        "anomali": anomali,
        "normal": normal,
        "onaylanan": onaylanan,
        "taslak": taslak,
        "ort_guven": round(ort_guven, 1),
        "anomali_orani": round(anomali / toplam, 3),
        "step": step,
        "tip_sayilari": {t: len(l) for t, l in tipler.items()},
    }


def main():
    """CLI: python -m modul_yapay_zeka.uretim_log"""
    sys.path.insert(0, ANA_DIZIN)
    from app import app  # noqa

    print("=" * 60)
    print(" ATGAS — Üretim Verisi → TensorBoard Log")
    print("=" * 60)
    with app.app_context():
        sonuc = uretim_loglarini_yaz()
    print(f"  ✓ Yazıldı: {sonuc}")
    print(f"  📁 Log dizini: {LOG_DIR}")


if __name__ == "__main__":
    main()
