# 📊 Veritabanı Tasarımı ve İlişkiler

Bu klasör, projenin veritabanı mimarisini içermektedir.

## ⚙️ Yapılandırma
- **Sistem:** PostgreSQL 17
- **Model:** İlişkisel Veritabanı (RDBMS)

## 📁 Dosya İçerikleri
- `database_schema.sql`: Tüm tablo yapılarını ve kısıtlamaları (constraints) içeren kod dosyası.
- `ER_Diyagrami.png`: Tablolar arasındaki 1:N ve 1:1 ilişkileri gösteren görsel şema.

## 🔗 Temel İlişkiler
1. **Hasta -> Görüntü (1:N):** Bir hastanın birden fazla analizi olabilir.
2. **Doktor -> Görüntü (1:N):** Görüntüleri sisteme yükleyen yetkili takibi.
3. **Görüntü -> Analiz Sonucu (1:1):** Her görüntü için AI tarafından üretilen tekil sonuç.
