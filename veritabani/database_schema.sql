CREATE TABLE Kullanicilar (
    kullanici_id SERIAL PRIMARY KEY,
    ad_soyad VARCHAR(100) NOT NULL,
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL,
    rol VARCHAR(20) CHECK (rol IN ('Doktor', 'Radyolog', 'Akademisyen')),
    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Hastalar (
    hasta_id SERIAL PRIMARY KEY,
    tc_no CHAR(11) UNIQUE NOT NULL,
    ad_soyad VARCHAR(100) NOT NULL,
    dogum_tarihi DATE,
    cinsiyet VARCHAR(10)
);

CREATE TABLE Goruntuler (
    goruntu_id SERIAL PRIMARY KEY,
    hasta_id INT REFERENCES Hastalar(hasta_id) ON DELETE CASCADE,
    yukleyen_doktor_id INT REFERENCES Kullanicilar(kullanici_id),
    dosya_yolu TEXT NOT NULL, -- Örn: /uploads/dicom/hasta1.dcm
    goruntu_tipi VARCHAR(20), -- X-ray, MRI, CT
    yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE AnalizSonuclari (
    analiz_id SERIAL PRIMARY KEY,
    goruntu_id INT REFERENCES Goruntuler(goruntu_id) ON DELETE CASCADE,
    tahmin_sonucu VARCHAR(50), -- Pneumonia veya Normal
    dogruluk_orani DECIMAL(5,2), -- Örn: 94.50
    isleme_suresi_sn DECIMAL(4,2), -- NFR'deki 5 saniye sınırı takibi için
    analiz_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Raporlar (
    rapor_id SERIAL PRIMARY KEY,
    analiz_id INT REFERENCES AnalizSonuclari(analiz_id),
    rapor_dosya_yolu TEXT NOT NULL,
    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
