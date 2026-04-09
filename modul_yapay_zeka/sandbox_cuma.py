from cnn_model import AtgasAnalizMotoru

if __name__ == "__main__":
    print("🛠️ Cuma'nın Kum Havuzuna (Sandbox) Hoş Geldiniz!\n")
    
    # Sistemi başlat
    motor = AtgasAnalizMotoru()
    
    # Kendi bilgisayarındaki test resmi yolunu buraya gir
    test_resmi = "ornek_test_verileri/ct/Akciger_Nodulu/Normal/5.png" # Senin resmin
    secilen_departman = "ct_akciger" # Seçenekler: xray, ct_akciger, ct_beyin, mri_fitik, mri_tumor 
    
    print(f"🚀 {secilen_departman.upper()} analizi başlatılıyor...")
    sonuc = motor.analizi_baslat(test_resmi, secilen_departman)
    
    print("\n📊 ANALİZ SONUCU:")
    if sonuc["durum"] == "basarili":
        # Veri paketini açıyoruz
        veri = sonuc["veri"] 
        
        print(f"  > BAŞLIK: {veri['teshis_basligi']}")
        print(f"  > SINIF: {veri['ham_sinif']}")
        print(f"  > GÜVEN ORANI: %{veri['guven_orani_yuzde']}")
        print(f"  > YZ YORUMU:\n    {veri['yapay_zeka_yorumu']}")
        print(f"\n✅ Isı haritalı resim kaydedildi: \n    {veri['islenmis_resim_yolu']}")
    else:
        print(f"  > DURUM: Hata")
        print(f"  > MESAJ: {sonuc.get('mesaj')}")



        """
        Çalıştırma Komutu:python3.11 sandbox_cuma.py
        
        Örnek Resim Yolları:
        
        -------------------------------

        ornek_test_verileri/ct/Akciger_Nodulu/Hastalikli/1.png
        ornek_test_verileri/ct/Akciger_Nodulu/Hastalikli/2.png
        ornek_test_verileri/ct/Akciger_Nodulu/Hastalikli/3.png
        ornek_test_verileri/ct/Akciger_Nodulu/Hastalikli/4.png
        ornek_test_verileri/ct/Akciger_Nodulu/Normal/5.png
        ornek_test_verileri/ct/Akciger_Nodulu/Normal/6.png
        ornek_test_verileri/ct/Akciger_Nodulu/Normal/7.png
        ornek_test_verileri/ct/Akciger_Nodulu/Normal/8.png
        ornek_test_verileri/ct/Beyin_Kanamasi/EDH/10.jpeg
        ornek_test_verileri/ct/Beyin_Kanamasi/EDH/11.jpeg
        ornek_test_verileri/ct/Beyin_Kanamasi/EDH/12.jpeg
        ornek_test_verileri/ct/Beyin_Kanamasi/EDH/9.jpeg
        ornek_test_verileri/ct/Beyin_Kanamasi/IPH/13.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IPH/14.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IPH/15.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IPH/16.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IVH/17.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IVH/18.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IVH/19.png
        ornek_test_verileri/ct/Beyin_Kanamasi/IVH/20.png
        ornek_test_verileri/ct/Beyin_Kanamasi/Normal/21.png
        ornek_test_verileri/ct/Beyin_Kanamasi/Normal/22.png
        ornek_test_verileri/ct/Beyin_Kanamasi/Normal/23.png
        ornek_test_verileri/ct/Beyin_Kanamasi/Normal/24.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SAH/25.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SAH/26.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SAH/27.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SAH/28.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SDH/29.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SDH/30.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SDH/31.png
        ornek_test_verileri/ct/Beyin_Kanamasi/SDH/32.png
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Hastalikli/33.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Hastalikli/34.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Hastalikli/35.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Hastalikli/36.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Normal/37.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Normal/38.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Normal/39.jpg
        ornek_test_verileri/mri/Lomber_Disk_Hernisi/Normal/40.jpg
        ornek_test_verileri/mri/Meningioma/Hastalikli/41.jpeg
        ornek_test_verileri/mri/Meningioma/Hastalikli/42.jpeg
        ornek_test_verileri/mri/Meningioma/Hastalikli/43.jpeg
        ornek_test_verileri/mri/Meningioma/Hastalikli/44.jpeg
        ornek_test_verileri/mri/Meningioma/Normal/45.jpg
        ornek_test_verileri/mri/Meningioma/Normal/46.jpg
        ornek_test_verileri/mri/Meningioma/Normal/47.jpg
        ornek_test_verileri/mri/Meningioma/Normal/48.jpg
        ornek_test_verileri/xray/Covid_19/49.png
        ornek_test_verileri/xray/Covid_19/50.png
        ornek_test_verileri/xray/Covid_19/51.png
        ornek_test_verileri/xray/Covid_19/52.png
        ornek_test_verileri/xray/Normal/53.jpeg
        ornek_test_verileri/xray/Normal/54.jpeg
        ornek_test_verileri/xray/Normal/55.jpeg
        ornek_test_verileri/xray/Normal/56.jpeg
        ornek_test_verileri/xray/Tuberkuloz/57.jpg
        ornek_test_verileri/xray/Tuberkuloz/58.jpg
        ornek_test_verileri/xray/Tuberkuloz/59.jpg
        ornek_test_verileri/xray/Tuberkuloz/60.jpg
        ornek_test_verileri/xray/Zaturre/61.jpeg
        ornek_test_verileri/xray/Zaturre/62.jpeg
        ornek_test_verileri/xray/Zaturre/63.jpeg
        ornek_test_verileri/xray/Zaturre/64.jpeg

        """