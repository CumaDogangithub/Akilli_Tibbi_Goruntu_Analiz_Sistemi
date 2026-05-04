CREATE TABLE `doktorlar` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `ad_soyad` varchar(100) NOT NULL,
  `eposta` varchar(150) UNIQUE NOT NULL,
  `sifre` varchar(255) NOT NULL,
  `brans` varchar(50) NOT NULL COMMENT 'Radyoloji, Ortopedi, Nöroloji vb.',
  `olusturulma_tarihi` timestamp DEFAULT (now())
);

CREATE TABLE `analiz_raporlari` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `doktor_id` integer NOT NULL,
  `tarama_tipi` varchar(10) NOT NULL COMMENT 'MR, CT, X-Ray',
  `goruntu_dosya_yolu` varchar(500) NOT NULL,
  `isaretli_goruntu_yolu` varchar(500),
  `tf_tahmin_sonucu` varchar(100),
  `dogruluk_orani` decimal(5,2) COMMENT 'Model güven skoru, örn: 94.50',
  `doktor_notu` text,
  `durum` varchar(20) NOT NULL DEFAULT 'Taslak' COMMENT 'Taslak / Kaydedildi',
  `hasta_ad_soyad` varchar(200) NOT NULL,
  `hasta_dogum_tarihi` date NOT NULL,
  `hasta_tc` varchar(11) NOT NULL,
  `protokol_no` varchar(200) NOT NULL,
  `islem_tarihi` timestamp DEFAULT (now())
);

ALTER TABLE `analiz_raporlari` ADD FOREIGN KEY (`doktor_id`) REFERENCES `doktorlar` (`id`);
