"""
 Frontend İçin Çıktı Formatı Düzenlendi
"""

import os
# --- 🛡️ KRİTİK HATA KALKANI ---
os.environ['TF_XLA_FLAGS'] = '--tf_xla_auto_jit=0 --tf_xla_cpu_global_jit=0'
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_AUTOTUNE_THRESHOLD'] = '1'

# NOT: TensorFlow'u kesinlikle bu ayarlardan SONRA import etmelisin!
import tensorflow as tf

# Keras/TF içinden XLA JIT derlemesini zorla kapatıyoruz:
tf.config.optimizer.set_jit(False) 
# ---------------------------------------------------------


import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')

class AtgasAnalizMotoru:
    def __init__(self):
        # Modeller klasörünün yolunu bul
        self.MEVCUT_DIZIN = os.path.dirname(os.path.abspath(__file__))
        self.MODEL_KLASORU = os.path.join(self.MEVCUT_DIZIN, "modeller")
        
        # 🌟 KRİTİK DEĞİŞİKLİK: Çıktıları Flask'ın okuyabileceği 'static/img' klasörüne yönlendiriyoruz
        ANA_PROJE_DIZINI = os.path.dirname(self.MEVCUT_DIZIN) 
        self.CIKTI_KLASORU = os.path.join(ANA_PROJE_DIZINI, "static", "img", "analiz_sonuclari")
        
        self.img_size = (384, 384)
        
        self.uzman_kutuphanesi = {
            "xray": {"dosya": "atgas_xray_uzmani.h5", "siniflar": ['Covid_19', 'Normal', 'Tuberkuloz', 'Zaturre'], "gercek_isim": "Akciğer X-Ray Taraması"},
            "ct_akciger": {"dosya": "atgas_akciger_nodulu_uzmani.h5", "siniflar": ['Hastalikli', 'Normal'], "gercek_isim": "Akciğer Nodülü"},
            "ct_beyin": {"dosya": "atgas_beyin_kanamasi_uzmani.h5", "siniflar": ['EDH', 'IPH', 'IVH', 'Normal', 'SAH', 'SDH'], "gercek_isim": "Beyin Kanaması"},
            "mri_fitik": {"dosya": "atgas_bel_fitigi_uzmani.h5", "siniflar": ['Hastalikli', 'Normal'], "gercek_isim": "Lomber Disk Hernisi (Bel Fıtığı)"},
            "mri_tumor": {"dosya": "atgas_meningioma_uzmani.h5", "siniflar": ['Hastalikli', 'Normal'], "gercek_isim": "Meningioma (Beyin Tümörü)"}
        }
        self.yuklu_modeller = {}

    def _model_yukle(self, uzman_kodu):
        if uzman_kodu not in self.yuklu_modeller:
            model_yolu = os.path.join(self.MODEL_KLASORU, self.uzman_kutuphanesi[uzman_kodu]["dosya"])
            if not os.path.exists(model_yolu):
                raise FileNotFoundError(f"❌ Model bulunamadı: {model_yolu}")
            self.yuklu_modeller[uzman_kodu] = tf.keras.models.load_model(model_yolu, compile=False)
        return self.yuklu_modeller[uzman_kodu]

    def _isi_haritasi_cikar(self, img_array, model):
        
        tf.config.run_functions_eagerly(True) # Tüm fonksiyonları graph yapmadan çalıştır

        base_model = None
        for layer in model.layers:
            try:
                layer.get_layer('top_conv')
                base_model = layer
                break
            except ValueError:
                pass
                
        if base_model is None:
            raise ValueError("Asıl beyin bulunamadı!")
            
        top_conv_layer = base_model.get_layer('top_conv')
        
        base_grad_model = tf.keras.models.Model(
            inputs=base_model.inputs, outputs=[top_conv_layer.output, base_model.output]
        )
        
        yeni_girdi = tf.keras.Input(shape=(384, 384, 3))
        x = yeni_girdi
        base_gecildi_mi = False
        sonraki_katmanlar = []
        
        for layer in model.layers:
            if layer == base_model:
                base_gecildi_mi = True
                continue
            if not base_gecildi_mi:
                x = layer(x, training=False)
            else:
                sonraki_katmanlar.append(layer)
                
        conv_ciktisi, beyin_ciktisi = base_grad_model(x)
        
        tahmin_sonucu = beyin_ciktisi
        for layer in sonraki_katmanlar[:-1]: 
            tahmin_sonucu = layer(tahmin_sonucu, training=False)
            
        feature_extractor_model = tf.keras.models.Model(
            inputs=yeni_girdi, outputs=[conv_ciktisi, tahmin_sonucu]
        )

        son_katman = sonraki_katmanlar[-1]

        with tf.GradientTape() as tape:
            katman_ciktisi, ozellikler = feature_extractor_model(img_array)
            logits = tf.matmul(ozellikler, son_katman.kernel)
            if son_katman.bias is not None:
                logits += son_katman.bias
                
            hedef_sinif_indeksi = tf.argmax(logits[0])
            hedef_sinif_skoru = logits[:, hedef_sinif_indeksi]

        gradyanlar = tape.gradient(hedef_sinif_skoru, katman_ciktisi)
        gradyan_agirliklari = tf.reduce_mean(gradyanlar, axis=(0, 1, 2))

        katman_ciktisi = katman_ciktisi[0]
        isi_haritasi = katman_ciktisi @ gradyan_agirliklari[..., tf.newaxis]
        isi_haritasi = tf.squeeze(isi_haritasi)
        
        isi_haritasi = tf.maximum(isi_haritasi, 0)
        maksimim_deger = tf.math.reduce_max(isi_haritasi)
        
        if maksimim_deger == 0:
            return np.zeros(isi_haritasi.shape)
            
        isi_haritasi = isi_haritasi / maksimim_deger
        return isi_haritasi.numpy()

    def _yorum_uret(self, ham_teshis, hastalik_gercek_ismi, guven_orani):
        """Çıkan sonuçlara göre dinamik ve tıbbi bir açıklama metni yazar."""
        if ham_teshis == "Normal":
            if guven_orani > 90:
                return f"Yapay zeka modeli %{round(guven_orani, 1)} gibi çok yüksek bir güven oranıyla görüntüde herhangi bir patolojik bulguya rastlamamıştır. Görüntü radyolojik olarak temiz (Normal) görünmektedir."
            else:
                return f"Görüntüde belirgin bir patoloji tespit edilmemiş olup, ancak modelin güven skoru %{round(guven_orani, 1)} seviyesindedir. Klinik şüphe durumunda radyolog kontrolü tavsiye edilir."
        else:
            if guven_orani > 85:
                return f"Sistem, %{round(guven_orani, 1)} yüksek güven oranıyla {hastalik_gercek_ismi} teşhisi koymuştur. Hastalığa dair potansiyel lezyon odakları ısı haritasında (kırmızı/sarı bölgeler) işaretlenmiştir. İvedi uzman hekim değerlendirmesi önerilir."
            else:
                return f"Görüntüde {hastalik_gercek_ismi} bulgusu şüphesi taşınmakta olup, modelin teşhis güven skoru %{round(guven_orani, 1)} olarak hesaplanmıştır. Kesin klinik tanı için radyolog onayı ve ek tetkikler gereklidir."

    def analizi_baslat(self, resim_yolu, uzman_kodu):
        if uzman_kodu not in self.uzman_kutuphanesi:
            return {"durum": "hata", "mesaj": "Geçersiz uzman departmanı!"}
            
        if not os.path.exists(resim_yolu):
            return {"durum": "hata", "mesaj": "Görüntü bulunamadı!"}

        try:
            model = self._model_yukle(uzman_kodu)
            siniflar = self.uzman_kutuphanesi[uzman_kodu]["siniflar"]
            hastalik_gercek_ismi = self.uzman_kutuphanesi[uzman_kodu]["gercek_isim"]

            img = tf.keras.utils.load_img(resim_yolu, target_size=self.img_size)
            img_array = tf.keras.utils.img_to_array(img)
            img_array = tf.expand_dims(img_array, 0)

            tahminler = model(img_array, training=False).numpy()
            en_yuksek_index = np.argmax(tahminler[0])
            ham_teshis = siniflar[en_yuksek_index]
            guven_orani = float(tahminler[0][en_yuksek_index]) * 100

            if ham_teshis == "Hastalikli":
                doktor_teshisi = f"Tespit Edildi ({hastalik_gercek_ismi})"
            elif ham_teshis == "Normal":
                doktor_teshisi = "Temiz (Bulgu Rastlanmadı)"
            else:
                doktor_teshisi = f"{ham_teshis} ({hastalik_gercek_ismi})"

            isi_haritasi_matrisi = self._isi_haritasi_cikar(img_array, model)

            orijinal_cv2 = cv2.imread(resim_yolu)
            orijinal_cv2 = cv2.resize(orijinal_cv2, self.img_size)
            
            isi_haritasi_cv2 = cv2.resize(isi_haritasi_matrisi, self.img_size)
            isi_haritasi_cv2 = np.uint8(255 * isi_haritasi_cv2)
            isi_haritasi_renkli = cv2.applyColorMap(isi_haritasi_cv2, cv2.COLORMAP_JET)

            birlestirilmis_resim = orijinal_cv2.copy()
            maske = isi_haritasi_cv2 > 50 
            birlestirilmis_resim[maske] = cv2.addWeighted(orijinal_cv2, 0.4, isi_haritasi_renkli, 0.6, 0)[maske]

            # Klasörü oluştur ve kaydet
            os.makedirs(self.CIKTI_KLASORU, exist_ok=True)
            dosya_adi = f"sonuc_{os.path.basename(resim_yolu)}"
            kayit_yolu = os.path.join(self.CIKTI_KLASORU, dosya_adi)
            cv2.imwrite(kayit_yolu, birlestirilmis_resim)

            # Yorumu üret
            yapay_zeka_yorumu = self._yorum_uret(ham_teshis, hastalik_gercek_ismi, guven_orani)

            # Ozan'ın Frontend'de kullanacağı kusursuz JSON mimarisi
            return {
                "durum": "basarili",
                "veri": {
                    "teshis_basligi": doktor_teshisi,
                    "ham_sinif": ham_teshis,
                    "guven_orani_yuzde": round(guven_orani, 2),
                    "yapay_zeka_yorumu": yapay_zeka_yorumu,
                    "islenmis_resim_yolu": kayit_yolu
                }
            }

        except Exception as e:
            return {"durum": "hata", "mesaj": str(e)}

