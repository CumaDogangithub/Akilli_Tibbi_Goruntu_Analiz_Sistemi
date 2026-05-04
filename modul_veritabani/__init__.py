"""ATGAS Veritabanı Modülü — SQLAlchemy ORM (PostgreSQL/Supabase)"""

from .modeller import db, Doktor, AnalizRaporu
from .kurulum import (
    db_init,
    database_uri,
    maskelenmis_url,
    ornek_doktor_ekle,
    aktif_backend,
)

__all__ = [
    "db",
    "Doktor",
    "AnalizRaporu",
    "db_init",
    "database_uri",
    "maskelenmis_url",
    "ornek_doktor_ekle",
    "aktif_backend",
]
