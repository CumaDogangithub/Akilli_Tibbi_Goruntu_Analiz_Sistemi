from pdf_generator import pdf_olustur

# Tasarimdaki TÜM alanlar (Protokol No dahil) burada tanimli
data = {
    "rapor_id": "7",
    "patient_name": "Mo**** Ka****",
    "patient_tc": "28*******92",
    "patient_birthday": "01.01.1985",
    "protocol_no": "PRK-2026-04782",  # Eksik olan bilgi eklendi
    "doctor_name": "Dr. Ahmet Yilmaz",
    "doctor_branch": "Radyoloji Uzmani",
    "doctor_email": "ahmet.yilmaz@hastane.com",
    "process_date": "09.04.2026",
    "findings": "Glioblastom Tespit Edildi",
    "confidence_score": "94.70",
    "note": "Yapilan MR analizi sonucunda sol frontal lobda yaklasik 3.2 cm boyutlarinda lezyon izlenmistir. Yapay zeka modeli yuksek dogrulukla tumor bulgusu tespit etmistir. Klinik korelasyon onerilir."
}

if __name__ == "__main__":
    try:
        print("Final Raporu Hazirlaniyor... ⏳")
        pdf_olustur(data)
        print("Islem Basarili! ✅ 'analiz_raporu.pdf' dosyasini acip kontrol edebilirsin.")
    except Exception as e:
        # Hata olusursa ne oldugunu anlamak icin detayli yazdiriyoruz
        print(f"Hata olustu: {e}")