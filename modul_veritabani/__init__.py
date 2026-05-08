"""ATGAS Veritabanı Modülü — SQLAlchemy ORM (PostgreSQL/Supabase)"""

from .modeller import db, Doktor, AnalizRaporu, ROLLER
from .kurulum import (
    db_init,
    database_uri,
    maskelenmis_url,
    ornek_doktor_ekle,
    rol_kolonu_garanti_et,
    aktif_backend,
)

__all__ = [
    "db",
    "Doktor",
    "AnalizRaporu",
    "ROLLER",
    "db_init",
    "database_uri",
    "maskelenmis_url",
    "ornek_doktor_ekle",
    "rol_kolonu_garanti_et",
    "aktif_backend",
]
