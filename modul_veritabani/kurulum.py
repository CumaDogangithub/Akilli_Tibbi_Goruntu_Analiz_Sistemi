"""
ATGAS — Veritabanı Yapılandırması (SQLAlchemy + PostgreSQL/Supabase)

SQLite desteği KALDIRILDI. DATABASE_URL .env dosyasında zorunludur.

Kullanım (Flask app içinde):
    from modul_veritabani import db, db_init, ornek_doktor_ekle
    app = Flask(__name__)
    db_init(app)            # SQLAlchemy + Flask-Migrate
    with app.app_context():
        db.create_all()     # tabloları oluştur (ilk kurulumda)
        ornek_doktor_ekle() # demo doktor ekle
"""

import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from flask_migrate import Migrate
from sqlalchemy import text

from .modeller import db, Doktor, AnalizRaporu, ROLLER


# ============================================================================
# DATABASE_URL'i SQLAlchemy + psycopg3 uyumlu hâle getir
# ============================================================================
def database_uri() -> str:
    """
    Beklenenler:
      - DATABASE_URL .env'de tanımlı olmalı
      - postgres:// öneki postgresql:// olarak normalize edilir
      - SQLAlchemy 2.0 default psycopg2 ister; biz psycopg3 kullandığımız için
        postgresql+psycopg:// dialect'ine zorlarız
      - Supabase/PgBouncer'a özel (pgbouncer=true gibi) parametreler libpq tanımaz,
        query string'den temizlenir.
    """
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError(
            "DATABASE_URL ortam değişkeni tanımlı değil.\n"
            ".env dosyasına Supabase connection string'inizi ekleyin:\n"
            "  DATABASE_URL=postgresql://postgres.<REF>:<PASS>@aws-0-<REGION>"
            ".pooler.supabase.com:6543/postgres"
        )

    url = raw
    # Tırnak içinde gelmiş olabilir
    if (url.startswith('"') and url.endswith('"')) or \
       (url.startswith("'") and url.endswith("'")):
        url = url[1:-1]

    # postgres:// → postgresql:// (Heroku/Render kompatibilitesi)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # SQLAlchemy 2.0 default: postgresql+psycopg2. Bizde psycopg3 kurulu → explicit.
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    # Sürücü-spesifik (libpq'nun tanımadığı) parametreleri sıyır
    parts = urlsplit(url)
    if parts.query:
        SURUCU_OZEL = {"pgbouncer", "supa"}
        temiz = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                 if k.lower() not in SURUCU_OZEL]
        url = urlunsplit((parts.scheme, parts.netloc, parts.path,
                          urlencode(temiz), parts.fragment))
    return url


def maskelenmis_url() -> str:
    """Şifreyi gizlenmiş hâlde DATABASE_URL'i döner (log için güvenli)."""
    import re
    return re.sub(r"://([^:]+):[^@]+@", r"://\1:****@", database_uri())


# ============================================================================
# FLASK ENTEGRASYONU
# ============================================================================
def db_init(app):
    """Flask app'e SQLAlchemy + Flask-Migrate bağlar."""
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        # Bağlantı bayatlamasını önler (özellikle Supabase pooler için kritik)
        "pool_pre_ping": True,
        "pool_recycle": 1800,        # 30 dakika
        "pool_size": 5,
        "max_overflow": 10,
    }
    db.init_app(app)
    Migrate(app, db)
    return db


# ============================================================================
# YARDIMCILAR
# ============================================================================
def rol_kolonu_garanti_et():
    """Eski Supabase kurulumlarında 'rol' sütunu yoksa ekler.
    PostgreSQL özellikli (IF NOT EXISTS) — tek seferlik, idempotent."""
    try:
        db.session.execute(text(
            "ALTER TABLE doktorlar "
            "ADD COLUMN IF NOT EXISTS rol VARCHAR(20) NOT NULL DEFAULT 'doktor'"
        ))
        db.session.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_doktorlar_rol ON doktorlar(rol)"
        ))
        db.session.commit()
    except Exception:
        # Tablo henüz yoksa create_all() oluşturacak; sessizce geç
        db.session.rollback()


def _kullanici_olustur_yoksa(eposta, ad_soyad, sifre, brans, unvan, rol):
    """Verilen e-posta sahibi kullanıcı yoksa oluşturur. True/False döner."""
    if Doktor.query.filter_by(eposta=eposta).first():
        return False
    k = Doktor(
        ad_soyad=ad_soyad.strip('"').strip("'"),
        eposta=eposta,
        brans=brans,
        unvan=unvan,
        rol=rol,
    )
    k.sifre_ayarla(sifre)
    db.session.add(k)
    db.session.commit()
    return True


def ornek_doktor_ekle():
    """Demo hesapları yoksa ekler — her rol için bir tane.
    Bilgiler .env'den okunur (DEMO_DOKTOR_*, DEMO_ADMIN_*, DEMO_RADYOLOG_*, DEMO_AKADEMISYEN_*).
    Çağrılmadan önce app context'i aktif olmalı."""
    eklenenler = []

    # 1) DOKTOR
    if _kullanici_olustur_yoksa(
        eposta=os.environ.get("DEMO_DOKTOR_EPOSTA", "doktor@atgas.local"),
        ad_soyad=os.environ.get("DEMO_DOKTOR_AD",   "Dr. Demo"),
        sifre=os.environ.get("DEMO_DOKTOR_SIFRE",   "123456"),
        brans=os.environ.get("DEMO_DOKTOR_BRANS",   "Radyoloji"),
        unvan="Uzman Doktor",
        rol="doktor",
    ):
        eklenenler.append("doktor")

    # 2) ADMIN
    if _kullanici_olustur_yoksa(
        eposta=os.environ.get("DEMO_ADMIN_EPOSTA",  "admin@atgas.local"),
        ad_soyad=os.environ.get("DEMO_ADMIN_AD",    "Sistem Yöneticisi"),
        sifre=os.environ.get("DEMO_ADMIN_SIFRE",    "admin123"),
        brans=os.environ.get("DEMO_ADMIN_BRANS",    "Yönetim"),
        unvan="Yönetici",
        rol="admin",
    ):
        eklenenler.append("admin")

    # 3) RADYOLOG
    if _kullanici_olustur_yoksa(
        eposta=os.environ.get("DEMO_RADYOLOG_EPOSTA",  "radyolog@atgas.local"),
        ad_soyad=os.environ.get("DEMO_RADYOLOG_AD",    "Dr. Radyolog"),
        sifre=os.environ.get("DEMO_RADYOLOG_SIFRE",    "radyolog123"),
        brans=os.environ.get("DEMO_RADYOLOG_BRANS",    "Radyoloji"),
        unvan="Uzman Radyolog",
        rol="radyolog",
    ):
        eklenenler.append("radyolog")

    # 4) AKADEMİSYEN
    if _kullanici_olustur_yoksa(
        eposta=os.environ.get("DEMO_AKADEMISYEN_EPOSTA",  "akademisyen@atgas.local"),
        ad_soyad=os.environ.get("DEMO_AKADEMISYEN_AD",    "Prof. Akademisyen"),
        sifre=os.environ.get("DEMO_AKADEMISYEN_SIFRE",    "akademisyen123"),
        brans=os.environ.get("DEMO_AKADEMISYEN_BRANS",    "Tıbbi Görüntüleme AR-GE"),
        unvan="Akademisyen",
        rol="akademisyen",
    ):
        eklenenler.append("akademisyen")

    return eklenenler


def aktif_backend():
    """Geriye dönük uyumluluk için. Artık her zaman 'postgres' döner."""
    return "postgres"
