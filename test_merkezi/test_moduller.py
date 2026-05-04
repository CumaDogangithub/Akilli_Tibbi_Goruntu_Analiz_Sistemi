"""
ATGAS — Entegrasyon ve Modül Testleri (SQLAlchemy + PostgreSQL)

Tüm modüllerin (DB, görüntü işleme, AI, raporlama, Flask) doğru bağlandığını doğrular.

Çalıştırma:
    python -m test_merkezi.test_moduller

Önkoşul:
    - .env'de DATABASE_URL tanımlı (Supabase veya yerel PostgreSQL)
"""

import os
import sys
import time
from datetime import date
from pathlib import Path

# .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Proje kökünü PYTHONPATH'e
ANA_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANA_DIZIN))


sonuclar = {"basarili": 0, "basarisiz": 0, "atlanan": 0}


def basla(baslik):
    print(f"\n{'='*70}\n  {baslik}\n{'='*70}")


def ok(mesaj):
    print(f"   [OK] {mesaj}")


def calistir(ad, fn):
    print(f"\n• {ad}...", end=" ", flush=True)
    try:
        sonuc = fn()
        if sonuc is False:
            print("ATLANDI")
            sonuclar["atlanan"] += 1
        else:
            print("OK")
            sonuclar["basarili"] += 1
    except Exception as e:
        print(f"HATA: {e}")
        sonuclar["basarisiz"] += 1


# ============================================================================
# 1. ORTAM
# ============================================================================
def test_ortam():
    basla("1. ORTAM (.env + paketler)")
    assert os.environ.get("ATGAS_SECRET"), "ATGAS_SECRET .env'de yok"
    ok("ATGAS_SECRET yüklü")
    assert os.environ.get("DATABASE_URL"), "DATABASE_URL .env'de yok"
    ok("DATABASE_URL yüklü")
    import sqlalchemy, flask_sqlalchemy, psycopg
    ok(f"SQLAlchemy {sqlalchemy.__version__} kurulu")
    ok(f"psycopg {psycopg.__version__} kurulu")


# ============================================================================
# 2. DB (SQLAlchemy + Supabase)
# ============================================================================
def test_db_baglanti():
    basla("2. VERİTABANI BAĞLANTISI (Supabase)")
    import app as a
    with a.app.app_context():
        from modul_veritabani import db, Doktor, AnalizRaporu
        from sqlalchemy import text
        ver = db.session.execute(text("SELECT version()")).scalar()
        ok(f"PostgreSQL: {ver[:50]}...")

        # Tablolar
        from sqlalchemy import inspect
        insp = inspect(db.engine)
        tablolar = insp.get_table_names()
        assert "doktorlar" in tablolar
        assert "analiz_raporlari" in tablolar
        ok(f"Tablolar mevcut: {tablolar}")

        # Demo doktor
        demo = Doktor.query.filter_by(eposta="doktor@atgas.local").first()
        assert demo is not None, "Demo doktor yok"
        ok(f"Demo doktor: id={demo.id}, {demo.eposta}")


def test_db_crud():
    basla("3. DB CRUD (ORM Insert/Update/Delete)")
    import app as a
    with a.app.app_context():
        from modul_veritabani import db, Doktor, AnalizRaporu

        doktor = Doktor.query.first()

        # INSERT
        r = AnalizRaporu(
            doktor_id=doktor.id,
            tarama_tipi="MR",
            uzman_kodu="mri_tumor",
            goruntu_dosya_yolu="test_orig.png",        # sadece dosya adı (taşınabilir)
            isaretli_goruntu_yolu="test_sonuc.png",
            tf_tahmin_sonucu="TEST",
            ham_sinif="Hastalikli",
            dogruluk_orani=95.0,
            yapay_zeka_yorumu="Test yorumu",
            doktor_notu="Test notu",
            durum="Taslak",
            seviye="Kritik",
            hasta_ad_soyad="Test Hasta",
            hasta_dogum_tarihi=date(1990, 1, 1),
            hasta_tc="11111111111",
            protokol_no="PRK-AUTOTEST",
        )
        db.session.add(r)
        db.session.commit()
        ok(f"INSERT: id={r.id}, {r.trk}")

        # UPDATE
        r.durum = "Kaydedildi"
        db.session.commit()
        bulundu = AnalizRaporu.query.get(r.id)
        assert bulundu.durum == "Kaydedildi"
        ok("UPDATE: durum → Kaydedildi")

        # Relationship
        assert bulundu.doktor.eposta == "doktor@atgas.local"
        ok(f"Relationship: rapor.doktor.eposta = {bulundu.doktor.eposta}")

        # DELETE
        db.session.delete(bulundu)
        db.session.commit()
        assert AnalizRaporu.query.get(r.id) is None
        ok("DELETE: kayıt silindi")


# ============================================================================
# 4. GÖRÜNTÜ ÖN İŞLEME
# ============================================================================
def test_preprocessor():
    basla("4. GÖRÜNTÜ ÖN İŞLEME (CLAHE + DICOM)")
    from modul_goruntu_isleme import format_kontrol_et, hazirla, dicom_dosyasi_mi

    assert format_kontrol_et("test.png")
    assert format_kontrol_et("test.dcm")
    assert format_kontrol_et("test.ima")
    assert not format_kontrol_et("test.bmp")
    ok("Format kontrolü: PNG/JPG/JPEG/DCM/DICOM/DIC/IMA")

    ornek = ANA_DIZIN / "modul_yapay_zeka" / "ornek_test_verileri" / "xray" / "Normal"
    test_resmi = next(ornek.glob("*.jpeg"), None) or next(ornek.glob("*.png"), None)
    if not test_resmi:
        return False
    cikti = hazirla(str(test_resmi), cikti_yolu=str(ANA_DIZIN / "test_merkezi" / "_test.png"))
    assert os.path.exists(cikti)
    ok(f"Ön işleme: {os.path.basename(cikti)}")
    os.remove(cikti)


# ============================================================================
# 5. AI MODELİ
# ============================================================================
def test_ai_analiz():
    basla("5. AI ANALİZİ (TensorFlow / Keras)")
    from modul_yapay_zeka import AtgasAnalizMotoru

    motor = AtgasAnalizMotoru()
    ok(f"Motor: {len(motor.uzman_kutuphanesi)} uzman model")

    test_resmi = ANA_DIZIN / "modul_yapay_zeka" / "ornek_test_verileri" / "xray" / "Normal"
    test_resmi = next(test_resmi.glob("*.jpeg"), None) or next(test_resmi.glob("*.png"), None)
    if not test_resmi:
        return False

    t = time.time()
    sonuc = motor.analizi_baslat(str(test_resmi), "xray")
    sure = time.time() - t
    assert sonuc["durum"] == "basarili", sonuc.get("mesaj")
    ok(f"Analiz: {sonuc['veri']['ham_sinif']} (%{sonuc['veri']['guven_orani_yuzde']}) [{sure:.1f}s]")


# ============================================================================
# 6. PDF RAPOR
# ============================================================================
def test_pdf():
    basla("6. PDF RAPOR ÜRETİMİ")
    from modul_raporlama import rapor_olustur

    veri = {
        "doktor": {"ad_soyad": "Dr. Test", "brans": "Radyoloji", "eposta": "test@atgas.local"},
        "hasta": {"ad_soyad": "Şeyma Öztürk", "tc": "12345678901",
                  "dogum_tarihi": "1985-06-15", "protokol_no": "PRK-TEST"},
        "analiz": {
            "tarama_tipi": "MR", "tf_tahmin_sonucu": "Glioblastom", "ham_sinif": "Hastalikli",
            "dogruluk_orani": 94.7, "yapay_zeka_yorumu": "Test yorumu",
            "doktor_notu": "Test notu",
            "goruntu_dosya_yolu": None, "isaretli_goruntu_yolu": None,
            "durum": "Kaydedildi", "islem_tarihi": "2026-05-04 12:00",
        },
    }
    cikti = ANA_DIZIN / "test_merkezi" / "_test_rapor.pdf"
    yol = rapor_olustur(999, veri, cikti_yolu=str(cikti))
    boyut = os.path.getsize(yol) / 1024
    assert boyut > 50, "PDF çok küçük (font embedding sorunu?)"
    ok(f"PDF üretildi: {boyut:.0f} KB")
    os.remove(yol)


# ============================================================================
# 7. FLASK ENDPOINT'LERİ
# ============================================================================
def test_flask():
    basla("7. FLASK ENTEGRASYONU (HTTP)")
    import app as a

    c = a.app.test_client()

    # Yetkisiz erişim → 302
    assert c.get("/dashboard").status_code == 302
    ok("Yetkisiz /dashboard → 302")

    # Login
    r = c.post("/login", data={"eposta": "doktor@atgas.local", "sifre": "123456"})
    assert r.status_code == 302
    ok("POST /login (geçerli) → 302")

    # Login sonrası
    with c.session_transaction() as s:
        s["doktor_id"] = 1
    for url in ["/dashboard", "/raporlar", "/profil", "/tarama"]:
        r = c.get(url)
        assert r.status_code == 200, f"{url} → {r.status_code}"
        ok(f"GET {url} → 200")


# ============================================================================
# ÇALIŞTIR
# ============================================================================
def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n" + "#" * 70)
    print("#  ATGAS — Modül Entegrasyon Testleri (SQLAlchemy + PostgreSQL)")
    print("#" * 70)

    calistir("Ortam (.env + paketler)", test_ortam)
    calistir("DB Bağlantı (Supabase)", test_db_baglanti)
    calistir("DB CRUD (ORM)", test_db_crud)
    calistir("Görüntü Ön İşleme", test_preprocessor)
    calistir("AI Analizi", test_ai_analiz)
    calistir("PDF Rapor", test_pdf)
    calistir("Flask HTTP Endpoint'leri", test_flask)

    print("\n" + "=" * 70)
    print(f"  SONUÇ: {sonuclar['basarili']} basarili · "
          f"{sonuclar['basarisiz']} basarisiz · "
          f"{sonuclar['atlanan']} atlandı")
    print("=" * 70)
    return 0 if sonuclar["basarisiz"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
