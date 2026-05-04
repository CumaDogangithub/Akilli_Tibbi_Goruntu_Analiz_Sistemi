"""
ATGAS — Entegrasyon ve Modül Testleri
Tüm modüllerin (DB, görüntü işleme, AI, raporlama) doğru bağlandığını doğrular.

Çalıştırma:  python -m test_merkezi.test_moduller
"""

import os
import sys
import time
import shutil
import sqlite3
from pathlib import Path

# Proje kökünü PYTHONPATH'e ekle
ANA_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANA_DIZIN))


def basla(baslik):
    print(f"\n{'='*70}\n🧪  {baslik}\n{'='*70}")


def basari(mesaj):
    print(f"   ✅ {mesaj}")


def hata(mesaj):
    print(f"   ❌ {mesaj}")


sonuclar = {"basarili": 0, "basarisiz": 0, "atlanan": 0}


def calistir(ad, fn):
    print(f"\n• {ad}...", end=" ", flush=True)
    try:
        sonuc = fn()
        if sonuc is False:
            print("ATLANDI")
            sonuclar["atlanan"] += 1
        else:
            print("✓")
            sonuclar["basarili"] += 1
    except Exception as e:
        print(f"✗ HATA: {e}")
        sonuclar["basarisiz"] += 1


# ============================================================================
# 1. VERİTABANI MODÜLÜ
# ============================================================================
def test_db_kurulum():
    basla("1. VERİTABANI MODÜLÜ")
    from modul_veritabani import veritabanini_kur, ornek_doktor_ekle, veritabani_baglantisi, DB_YOLU
    veritabanini_kur()
    ornek_doktor_ekle()
    assert os.path.exists(DB_YOLU), "DB dosyası oluşmadı"
    basari(f"DB hazır: {DB_YOLU}")

    bg = veritabani_baglantisi()
    cur = bg.cursor()
    cur.execute("SELECT COUNT(*) AS adet FROM doktorlar")
    adet = cur.fetchone()["adet"]
    bg.close()
    assert adet >= 1, "Demo doktor yok"
    basari(f"Doktor sayısı: {adet}")


def test_db_rapor_ekle_sil():
    from modul_veritabani import veritabani_baglantisi
    bg = veritabani_baglantisi()
    cur = bg.cursor()
    cur.execute(
        "INSERT INTO analiz_raporlari "
        "(doktor_id, tarama_tipi, uzman_kodu, goruntu_dosya_yolu, tf_tahmin_sonucu, "
        "ham_sinif, dogruluk_orani, hasta_ad_soyad, hasta_dogum_tarihi, hasta_tc, protokol_no) "
        "VALUES (1, 'X-Ray', 'xray', '/tmp/x.png', 'TestSınıf', 'Normal', 95.5, "
        "'Test Hasta', '1990-01-01', '12345678901', 'PRK-TEST-001')"
    )
    rapor_id = cur.lastrowid
    bg.commit()

    cur.execute("SELECT durum FROM analiz_raporlari WHERE id = ?", (rapor_id,))
    assert cur.fetchone()["durum"] == "Taslak", "Varsayılan durum 'Taslak' olmalı"
    basari(f"Rapor eklendi (id={rapor_id}), varsayılan durum: Taslak")

    cur.execute("UPDATE analiz_raporlari SET durum = 'Kaydedildi' WHERE id = ?", (rapor_id,))
    bg.commit()
    cur.execute("SELECT durum FROM analiz_raporlari WHERE id = ?", (rapor_id,))
    assert cur.fetchone()["durum"] == "Kaydedildi"
    basari("Durum 'Kaydedildi'e güncellenebiliyor")

    cur.execute("DELETE FROM analiz_raporlari WHERE id = ?", (rapor_id,))
    bg.commit()
    bg.close()
    basari("Rapor silindi")


# ============================================================================
# 2. GÖRÜNTÜ ÖN İŞLEME
# ============================================================================
def test_preprocessor():
    basla("2. GÖRÜNTÜ ÖN İŞLEME")
    from modul_goruntu_isleme import format_kontrol_et, hazirla, DESTEKLENEN_FORMATLAR

    assert format_kontrol_et("test.png")
    assert format_kontrol_et("test.dcm")
    assert not format_kontrol_et("test.bmp")
    basari(f"Format kontrolü: {DESTEKLENEN_FORMATLAR}")

    ornek = ANA_DIZIN / "modul_yapay_zeka" / "ornek_test_verileri" / "xray" / "Normal"
    test_resmi = next(ornek.glob("*.jpeg"), None) or next(ornek.glob("*.png"), None)
    if not test_resmi:
        print("(test resmi bulunamadı, atlandı)", end=" ")
        return False

    cikti = hazirla(str(test_resmi), cikti_yolu=str(ANA_DIZIN / "test_merkezi" / "_test_islenmis.png"))
    assert os.path.exists(cikti)
    basari(f"Ön işleme başarılı: {cikti}")
    os.remove(cikti)


# ============================================================================
# 3. AI ANALİZİ
# ============================================================================
def test_ai_analiz():
    basla("3. AI ANALİZİ (TensorFlow / Keras)")
    from modul_yapay_zeka import AtgasAnalizMotoru

    motor = AtgasAnalizMotoru()
    basari(f"Motor başlatıldı, {len(motor.uzman_kutuphanesi)} uzman model var")

    test_resmi = ANA_DIZIN / "modul_yapay_zeka" / "ornek_test_verileri" / "xray" / "Normal"
    test_resmi = next(test_resmi.glob("*.jpeg"), None) or next(test_resmi.glob("*.png"), None)
    if not test_resmi:
        print("(test resmi yok, atlandı)", end=" ")
        return False

    print(f"\n   ▶ Analiz ediliyor: {test_resmi.name} (xray)")
    basla_ts = time.time()
    sonuc = motor.analizi_baslat(str(test_resmi), "xray")
    sure = time.time() - basla_ts

    assert sonuc["durum"] == "basarili", f"Hata: {sonuc.get('mesaj')}"
    veri = sonuc["veri"]
    basari(f"Analiz tamamlandı ({sure:.1f}s)")
    basari(f"Tahmin: {veri['ham_sinif']} (%{veri['guven_orani_yuzde']})")
    basari(f"Görüntü: {veri['islenmis_resim_yolu']}")

    return veri  # PDF testi için


# ============================================================================
# 4. PDF RAPOR
# ============================================================================
def test_pdf_uretim():
    basla("4. PDF RAPOR ÜRETİMİ")
    from modul_raporlama import rapor_olustur

    veri = {
        "doktor": {"ad_soyad": "Dr. Test Demo", "brans": "Radyoloji", "eposta": "test@atgas.local"},
        "hasta": {
            "ad_soyad": "Mehmet Kara",
            "tc": "12345678901",
            "dogum_tarihi": "1985-06-15",
            "protokol_no": "PRK-2026-04782",
        },
        "analiz": {
            "tarama_tipi": "MR",
            "tf_tahmin_sonucu": "Glioblastom",
            "ham_sinif": "Hastalikli",
            "dogruluk_orani": 94.7,
            "yapay_zeka_yorumu": "Yüksek güven oranıyla Meningioma teşhisi konulmuştur.",
            "doktor_notu": "Sol frontal lobda 3.2 cm boyutunda kontrast tutan kitle lezyonu izlenmektedir.",
            "goruntu_dosya_yolu": None,
            "isaretli_goruntu_yolu": None,
            "durum": "Kaydedildi",
            "islem_tarihi": "2026-05-03 14:32",
        },
    }
    cikti = ANA_DIZIN / "test_merkezi" / "_test_rapor.pdf"
    yol = rapor_olustur(999, veri, cikti_yolu=str(cikti))
    assert os.path.exists(yol)
    boyut_kb = os.path.getsize(yol) / 1024
    basari(f"PDF üretildi: {yol} ({boyut_kb:.0f} KB)")
    os.remove(yol)


# ============================================================================
# 5. FLASK ENDPOINT TESTLERİ
# ============================================================================
def test_flask_endpoints():
    basla("5. FLASK ENTEGRASYONU (Test Client)")
    import app as atgas_app

    istemci = atgas_app.app.test_client()

    yanit = istemci.get("/")
    assert yanit.status_code in (302, 200), f"Beklenmeyen: {yanit.status_code}"
    basari(f"GET / → {yanit.status_code} (login'e yönlendirme)")

    yanit = istemci.get("/login")
    assert yanit.status_code == 200
    assert b"ATGAS" in yanit.data
    basari("GET /login → 200, ATGAS markası var")

    yanit = istemci.get("/dashboard")
    assert yanit.status_code == 302, "Yetkisiz erişim 302 vermeli"
    basari("GET /dashboard (yetkisiz) → 302")

    yanit = istemci.post("/login", data={"eposta": "doktor@atgas.local", "sifre": "123456"}, follow_redirects=False)
    assert yanit.status_code == 302, "Başarılı girişte 302 redirect olmalı"
    basari("POST /login (geçerli) → 302 (dashboard'a yönlendirme)")

    with istemci.session_transaction() as oturum:
        oturum["doktor_id"] = 1

    for yol in ["/dashboard", "/raporlar", "/profil", "/tarama"]:
        yanit = istemci.get(yol)
        assert yanit.status_code == 200, f"{yol} → {yanit.status_code}"
        basari(f"GET {yol} → 200")


# ============================================================================
# ÇALIŞTIR
# ============================================================================
def main():
    # Windows konsolunu UTF-8'e zorla
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n" + "#" * 70)
    print("#      ATGAS - Modul Entegrasyon Testleri                            #")
    print("#" * 70)

    calistir("DB Kurulum + Demo Doktor", test_db_kurulum)
    calistir("DB Rapor Ekle/Güncelle/Sil", test_db_rapor_ekle_sil)
    calistir("Görüntü Ön İşleme (CLAHE + Resize)", test_preprocessor)
    calistir("AI Analizi (TensorFlow Modeli)", test_ai_analiz)
    calistir("PDF Rapor Üretimi (reportlab)", test_pdf_uretim)
    calistir("Flask Endpoint Entegrasyonu", test_flask_endpoints)

    print("\n" + "=" * 70)
    print(f"📊  SONUÇ: {sonuclar['basarili']} başarılı · "
          f"{sonuclar['basarisiz']} başarısız · "
          f"{sonuclar['atlanan']} atlandı")
    print("=" * 70)
    return 0 if sonuclar["basarisiz"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
