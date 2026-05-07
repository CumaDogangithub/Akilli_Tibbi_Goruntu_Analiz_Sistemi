"""
ATGAS — SQLAlchemy ORM Modelleri

İki ana tablo:
  - Doktor (doktorlar)
  - AnalizRaporu (analiz_raporlari)

Backend: PostgreSQL (Supabase). DATABASE_URL .env'de tanımlı olmalıdır.
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Tek bir global db instance (Flask-SQLAlchemy)
db = SQLAlchemy()


# Roller — projeakisi.md kullanıcı hikayelerine göre:
#   admin       → Sistemi yönetir, yeni kullanıcı ekler/siler
#   doktor      → Görüntü yükler, AI analizi yapar, kendi raporlarını saklar
#   radyolog    → Tüm raporları görüntüler, anomali işaretlemelerini inceler
#   akademisyen → Model performans metriklerini TensorBoard üzerinden izler
ROLLER = ("admin", "doktor", "radyolog", "akademisyen")


class Doktor(db.Model):
    __tablename__ = "doktorlar"

    id = db.Column(db.Integer, primary_key=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    eposta = db.Column(db.String(150), unique=True, nullable=False, index=True)
    sifre = db.Column(db.String(255), nullable=False)
    brans = db.Column(db.String(50), nullable=False)
    unvan = db.Column(db.String(50), default="Uzman Doktor")
    rol = db.Column(db.String(20), nullable=False, default="doktor", index=True)
    olusturulma_tarihi = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    raporlar = db.relationship(
        "AnalizRaporu",
        back_populates="doktor",
        lazy="dynamic",
        cascade="save-update, merge",
    )

    # Şifre yardımcıları
    def sifre_ayarla(self, ham_sifre: str):
        self.sifre = generate_password_hash(ham_sifre)

    def sifre_dogrula(self, ham_sifre: str) -> bool:
        return check_password_hash(self.sifre, ham_sifre)

    @property
    def rol_etiketi(self) -> str:
        return {
            "admin": "Yönetici",
            "doktor": "Doktor",
            "radyolog": "Radyolog",
            "akademisyen": "Akademisyen",
        }.get(self.rol or "doktor", "Doktor")

    def __repr__(self):
        return f"<Doktor {self.id} {self.ad_soyad} ({self.rol})>"


class AnalizRaporu(db.Model):
    __tablename__ = "analiz_raporlari"

    id = db.Column(db.Integer, primary_key=True)
    doktor_id = db.Column(
        db.Integer,
        db.ForeignKey("doktorlar.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Tarama bilgileri
    tarama_tipi = db.Column(db.String(10), nullable=False)        # MR / CT / X-Ray
    uzman_kodu = db.Column(db.String(20), nullable=False)         # xray, ct_akciger, ...

    # Görüntü dosya yolları
    goruntu_dosya_yolu = db.Column(db.String(500), nullable=False)
    isaretli_goruntu_yolu = db.Column(db.String(500))

    # AI çıktıları
    tf_tahmin_sonucu = db.Column(db.String(100))
    ham_sinif = db.Column(db.String(50))
    dogruluk_orani = db.Column(db.Numeric(5, 2))
    yapay_zeka_yorumu = db.Column(db.Text)

    # Doktor müdahalesi
    doktor_notu = db.Column(db.Text)
    durum = db.Column(db.String(20), default="Taslak", nullable=False, index=True)
    seviye = db.Column(db.String(20), default="Orta")

    # Hasta bilgileri
    hasta_ad_soyad = db.Column(db.String(200), nullable=False)
    hasta_dogum_tarihi = db.Column(db.Date, nullable=False)
    hasta_tc = db.Column(db.String(11), nullable=False)
    protokol_no = db.Column(db.String(200), nullable=False)

    islem_tarihi = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    doktor = db.relationship("Doktor", back_populates="raporlar")

    # İş kuralları için yardımcı property'ler
    @property
    def trk(self) -> str:
        """TRK-000123 formatında okunabilir kod."""
        return f"TRK-{self.id:06d}"

    @property
    def anomali_var_mi(self) -> bool:
        return self.ham_sinif and self.ham_sinif != "Normal"

    def __repr__(self):
        return f"<AnalizRaporu {self.trk} ({self.durum})>"
