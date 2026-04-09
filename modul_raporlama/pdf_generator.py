import pdfkit
import os

def html_olustur(data):
    # Görsel yollarını merkezi 'static' klasörüne göre ayarlar
    base_path = os.path.abspath(os.path.dirname(__file__))
    logo_path = os.path.join(base_path, "static", "img", "atgas_logo_dark.png")
    orig_path = os.path.join(base_path, "static", "img", "original_image.png")
    tf_path = os.path.join(base_path, "static", "img", "tf_output.png")

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background-color: #0B0C10; color: #E8E9ED; font-family: 'Segoe UI', Arial, sans-serif; padding: 15px; font-size: 10px; }}
            .container {{ max-width: 800px; margin: auto; }}
            
            /* Header */
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1F2833; padding-bottom: 10px; margin-bottom: 15px; }}
            .logo {{ width: 50px; margin-right: 15px; }}
            .status-badge {{ background: #004D40; color: #66FCF1; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 8px; display: inline-block; }}
            
            /* Kart Yapıları */
            .card {{ background: #1B1B23; border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid #1F2330; }}
            .info-grid {{ display: flex; gap: 10px; margin-bottom: 10px; }}
            
            /* Görsel Alanı */
            .image-row {{ display: flex; gap: 10px; justify-content: space-between; margin-bottom: 10px; }}
            .image-box {{ width: 49%; text-align: center; background: #16161D; padding: 10px; border-radius: 8px; border: 1px solid #1F2330; }}
            .report-img {{ max-width: 100%; max-height: 170px; border-radius: 6px; margin-top: 5px; }}
            
            /* Teknik Tablo */
            .tech-table {{ width: 100%; border-collapse: collapse; }}
            .tech-table td {{ padding: 6px 0; border-bottom: 1px solid #2A2A35; }}
            .tech-label {{ color: #8E9196; font-size: 9px; }}
            .tech-value {{ text-align: right; color: #FFFFFF; font-weight: 600; font-size: 10px; }}

            /* Uyarı ve Footer */
            .warning-footer {{ background: #1A1810; border: 1px solid #D4AF37; padding: 10px; color: #D4AF37; font-size: 8px; border-radius: 6px; margin-top: 15px; text-align: justify; }}
            .final-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 10px; border-top: 1px solid #1F2833; }}
            .tf-badge {{ background-color: #0E1629; border: 1px solid #1F2833; border-radius: 6px; padding: 8px 15px; color: #66FCF1; font-weight: bold; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="display:flex; align-items:center;">
                    <img src="{logo_path}" class="logo">
                    <div>
                        <h1 style="color:#66FCF1; margin:0; font-size:22px;">ATGAS</h1>
                        <p style="margin:0; font-size:9px;">AKILLI TIBBI GORUNTULEME SISTEMI</p>
                    </div>
                </div>
                <div style="text-align:right;">
                    <b>Rapor #{data['rapor_id']}</b><br>{data['process_date']}<br>
                    <div class="status-badge">KAYDEDILDI</div>
                </div>
            </div>

            <div class="info-grid">
                <div class="card" style="flex:1;">
                    <h3 style="color:#66FCF1; margin:0 0 10px 0; font-size:11px;">HASTA BILGILERI</h3>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">Ad Soyad:</span><span>{data['patient_name']}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">TC No:</span><span>{data['patient_tc']}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">Dogum T.:</span><span>{data['patient_birthday']}</span></div>
                </div>
                <div class="card" style="flex:1;">
                    <h3 style="color:#388E3C; margin:0 0 10px 0; font-size:11px;">DOKTOR BILGILERI</h3>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">Ad Soyad:</span><span>{data['doctor_name']}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">Brans:</span><span>{data['doctor_branch']}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#8E9196;">E-posta:</span><span>{data['doctor_email']}</span></div>
                </div>
            </div>

            <div class="card">
                <h3 style="color:#66FCF1; margin:0 0 8px 0; font-size:11px;">TEKNIK DETAYLAR</h3>
                <table class="tech-table">
                    <tr><td class="tech-label">Rapor ID</td><td class="tech-value">analiz_raporlari.id → {data['rapor_id']}</td></tr>
                    <tr><td class="tech-label">Tarama Tipi</td><td class="tech-value">MR</td></tr>
                    <tr><td class="tech-label">TF Tahmin Sonucu</td><td class="tech-value" style="color:#EF4444;">{data['findings']}</td></tr>
                    <tr><td class="tech-label">Dogruluk Orani</td><td class="tech-value">%{data['confidence_score']}</td></tr>
                    <tr><td class="tech-label">Durum</td><td class="tech-value"><div class="status-badge">KAYDEDILDI</div></td></tr>
                    <tr><td class="tech-label">Protokol No</td><td class="tech-value">{data['protocol_no']}</td></tr>
                    <tr><td class="tech-label">Islem Tarihi</td><td class="tech-value">{data['process_date']}</td></tr>
                </table>
            </div>

            <div class="image-row">
                <div class="image-box">
                    <div style="color:#66FCF1; font-weight:bold; margin-bottom:5px;">ORIJINAL GORUNTU</div>
                    <img src="{orig_path}" class="report-img">
                </div>
                <div class="image-box">
                    <div style="color:#66FCF1; font-weight:bold;">TENSORFLOW ANALIZ CIKTISI</div>
                    <div style="color:#8E9196; font-size:7px; font-style:italic;">(Grad-CAM Isi Haritasi)</div>
                    <img src="{tf_path}" class="report-img">
                </div>
            </div>

            <div class="warning-footer">
                <b>DIKKAT:</b> Bu rapor ATGAS Yapay Zeka Sistemi (TensorFlow/Keras) tarafindan otomatik olarak üretilmistir ve kesin tani niteligi tasimaz. Klinik degerlendirme uzman doktor onayi ile birlikte yorumlanmalidir.
            </div>

            <div class="final-footer">
                <div class="tf-badge">◇ TensorFlow/Keras · ResNet50 CNN</div>
                <div style="text-align:right; color:#8E9196; font-size:8px;">
                    ATGAS v1.0 | Akilli Tibbi Goruntuleme<br>
                    Rapor #{data['rapor_id']} · Protokol: {data['protocol_no']}<br>
                    © 2026 ATGAS — Tüm haklari saklidir.
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def pdf_olustur(data):
    # Bilgisayarındaki wkhtmltopdf yolunu ayarlar
    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    
    # HTML içeriğini oluşturur
    html_content = html_olustur(data)
    
    # PDF çıktı ayarları
    options = {
        'enable-local-file-access': None, 
        'encoding': "UTF-8", 
        'page-size': 'A4', 
        'margin-top': '0.2in',
        'margin-right': '0.2in',
        'margin-bottom': '0.2in',
        'margin-left': '0.2in',
        'quiet': ''
    }
    
    # PDF dosyasını üretir
    pdfkit.from_string(html_content, "analiz_raporu.pdf", configuration=config, options=options)