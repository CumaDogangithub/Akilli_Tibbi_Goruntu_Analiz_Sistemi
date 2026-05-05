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

from .modeller import db, Doktor, AnalizRaporu


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
def ornek_doktor_ekle():
    """Demo doktor hesabını ekler (yoksa). Bilgiler .env'den okunur:
       DEMO_DOKTOR_AD, DEMO_DOKTOR_EPOSTA, DEMO_DOKTOR_SIFRE, DEMO_DOKTOR_BRANS
    Çağrılmadan önce app context'i aktif olmalı."""
    if Doktor.query.count() > 0:
        return False

    # .env'den oku — tırnak işaretleri varsa kaldır (kabuk format'ları için)
    ad     = os.environ.get("DEMO_DOKTOR_AD",     "Dr. Demo").strip('"').strip("'")
    eposta = os.environ.get("DEMO_DOKTOR_EPOSTA", "doktor@atgas.local")
    sifre  = os.environ.get("DEMO_DOKTOR_SIFRE",  "123456")
    brans  = os.environ.get("DEMO_DOKTOR_BRANS",  "Radyoloji")

    d = Doktor(ad_soyad=ad, eposta=eposta, brans=brans, unvan="Uzman Doktor")
    d.sifre_ayarla(sifre)
    db.session.add(d)
    db.session.commit()
    return True


def aktif_backend():
    """Geriye dönük uyumluluk için. Artık her zaman 'postgres' döner."""
    return "postgres"
