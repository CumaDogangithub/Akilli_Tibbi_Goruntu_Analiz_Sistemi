"""
ATGAS Veritabanı Modülü
- SQLite tabanlı (yerel KVKK uyumlu, kurulum gerektirmez)
- Şema: raporlar/veritabani_mysql.sql ile bire bir uyumlu
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

ANA_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_KLASORU = os.path.join(ANA_DIZIN, "veritabani")
DB_YOLU = os.path.join(DB_KLASORU, "atgas.db")


def veritabani_baglantisi():
    os.makedirs(DB_KLASORU, exist_ok=True)
    baglanti = sqlite3.connect(DB_YOLU)
    baglanti.row_factory = sqlite3.Row
    baglanti.execute("PRAGMA foreign_keys = ON")
    return baglanti


def veritabanini_kur():
    """Tabloları oluşturur (yoksa)."""
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS doktorlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad VARCHAR(100) NOT NULL,
        eposta VARCHAR(150) UNIQUE NOT NULL,
        sifre VARCHAR(255) NOT NULL,
        brans VARCHAR(50) NOT NULL,
        unvan VARCHAR(50) DEFAULT 'Uzman Doktor',
        olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS analiz_raporlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doktor_id INTEGER NOT NULL,
        tarama_tipi VARCHAR(10) NOT NULL,
        uzman_kodu VARCHAR(20) NOT NULL,
        goruntu_dosya_yolu VARCHAR(500) NOT NULL,
        isaretli_goruntu_yolu VARCHAR(500),
        tf_tahmin_sonucu VARCHAR(100),
        ham_sinif VARCHAR(50),
        dogruluk_orani DECIMAL(5,2),
        yapay_zeka_yorumu TEXT,
        doktor_notu TEXT,
        durum VARCHAR(20) NOT NULL DEFAULT 'Taslak',
        seviye VARCHAR(20) DEFAULT 'Orta',
        hasta_ad_soyad VARCHAR(200) NOT NULL,
        hasta_dogum_tarihi DATE NOT NULL,
        hasta_tc VARCHAR(11) NOT NULL,
        protokol_no VARCHAR(200) NOT NULL,
        islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doktor_id) REFERENCES doktorlar(id)
    );
    """)

    baglanti.commit()
    baglanti.close()


def ornek_doktor_ekle():
    """Demo doktor hesabı: doktor@atgas.local / 123456"""
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute("SELECT COUNT(*) AS adet FROM doktorlar")
    if cur.fetchone()["adet"] == 0:
        cur.execute(
            "INSERT INTO doktorlar (ad_soyad, eposta, sifre, brans, unvan) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "Dr. Cuma Doğan",
                "doktor@atgas.local",
                generate_password_hash("123456"),
                "Radyoloji",
                "Uzman Doktor",
            ),
        )
        baglanti.commit()
    baglanti.close()


if __name__ == "__main__":
    veritabanini_kur()
    ornek_doktor_ekle()
    print(f"✅ Veritabanı hazır: {DB_YOLU}")
