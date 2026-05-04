"""
ATGAS — Akıllı Tıbbi Görüntü Analiz Sistemi
Flask Backend — Tüm modülleri (yapay zeka + görüntü işleme + raporlama + DB) bağlar.
"""

import os
import uuid
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, send_file, flash, abort,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# --- ATGAS Modülleri ---
from modul_veritabani import veritabani_baglantisi, veritabanini_kur, ornek_doktor_ekle
from modul_goruntu_isleme import hazirla as goruntu_hazirla, format_kontrol_et
from modul_yapay_zeka import AtgasAnalizMotoru
from modul_raporlama import rapor_olustur, RAPOR_KLASORU

# ============================================================================
ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
YUKLEME_KLASORU = os.path.join(ANA_DIZIN, "static", "uploads")
ISLENMIS_KLASORU = os.path.join(ANA_DIZIN, "static", "img", "analiz_sonuclari")
os.makedirs(YUKLEME_KLASORU, exist_ok=True)
os.makedirs(ISLENMIS_KLASORU, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ATGAS_SECRET", "atgas-gizli-2026-cuma")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Tek seferlik kurulum + AI motoru
veritabanini_kur()
ornek_doktor_ekle()
ANALIZ_MOTORU = AtgasAnalizMotoru()


# ============================================================================
# YARDIMCILAR
# ============================================================================
def giris_gerekli(fn):
    @wraps(fn)
    def sarmalayici(*args, **kwargs):
        if "doktor_id" not in session:
            if request.is_json:
                return jsonify({"durum": "hata", "mesaj": "Yetkisiz"}), 401
            flash("Lütfen önce giriş yapın.", "uyari")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return sarmalayici


def aktif_doktor():
    if "doktor_id" not in session:
        return None
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute("SELECT * FROM doktorlar WHERE id = ?", (session["doktor_id"],))
    doktor = cur.fetchone()
    baglanti.close()
    return doktor


@app.context_processor
def kenar_cubugu_son_taramalar():
    """Sidebar'daki Raporlarım altına en son 5 taramayı enjekte eder.
    Her template'de `son_taramalar` ve `aktif_doktor_objesi` olarak erişilebilir."""
    if "doktor_id" not in session:
        return {}
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT id, tarama_tipi, tf_tahmin_sonucu, ham_sinif, durum, islem_tarihi "
        "FROM analiz_raporlari WHERE doktor_id = ? "
        "ORDER BY islem_tarihi DESC LIMIT 5",
        (session["doktor_id"],),
    )
    son_taramalar = cur.fetchall()
    baglanti.close()
    return {"son_taramalar": son_taramalar}


def seviye_belirle(ham_sinif: str, dogruluk: float) -> str:
    if ham_sinif == "Normal":
        return "Temiz"
    if dogruluk >= 85:
        return "Kritik"
    return "Orta"


# ============================================================================
# AUTH
# ============================================================================
@app.route("/")
def kok():
    if "doktor_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    hata = None
    if request.method == "POST":
        eposta = request.form.get("eposta", "").strip().lower()
        sifre = request.form.get("sifre", "")
        baglanti = veritabani_baglantisi()
        cur = baglanti.cursor()
        cur.execute("SELECT * FROM doktorlar WHERE eposta = ?", (eposta,))
        doktor = cur.fetchone()
        baglanti.close()

        if doktor and check_password_hash(doktor["sifre"], sifre):
            session["doktor_id"] = doktor["id"]
            session["doktor_ad"] = doktor["ad_soyad"]
            session["doktor_brans"] = doktor["brans"]
            return redirect(url_for("dashboard"))
        hata = "Geçersiz e-posta veya şifre."
    return render_template("login.html", hata=hata)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================================
# DASHBOARD
# ============================================================================
@app.route("/dashboard")
@giris_gerekli
def dashboard():
    doktor_id = session["doktor_id"]
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()

    cur.execute("SELECT COUNT(*) AS adet FROM analiz_raporlari WHERE doktor_id = ?", (doktor_id,))
    toplam = cur.fetchone()["adet"]

    cur.execute(
        "SELECT COUNT(*) AS adet FROM analiz_raporlari "
        "WHERE doktor_id = ? AND ham_sinif != 'Normal'",
        (doktor_id,),
    )
    anomali = cur.fetchone()["adet"]

    cur.execute(
        "SELECT AVG(dogruluk_orani) AS ort FROM analiz_raporlari WHERE doktor_id = ?",
        (doktor_id,),
    )
    row = cur.fetchone()
    ortalama = round(row["ort"] or 0, 1)

    cur.execute(
        "SELECT COUNT(*) AS adet FROM analiz_raporlari WHERE doktor_id = ? AND durum = 'Taslak'",
        (doktor_id,),
    )
    taslak = cur.fetchone()["adet"]

    cur.execute(
        "SELECT * FROM analiz_raporlari WHERE doktor_id = ? "
        "ORDER BY islem_tarihi DESC LIMIT 5",
        (doktor_id,),
    )
    son_analizler = cur.fetchall()
    baglanti.close()

    return render_template(
        "dashboard.html",
        doktor=aktif_doktor(),
        istatistikler={
            "toplam": toplam,
            "anomali": anomali,
            "ortalama_dogruluk": ortalama,
            "taslak": taslak,
        },
        son_analizler=son_analizler,
    )


# ============================================================================
# YENİ TARAMA
# ============================================================================
@app.route("/tarama")
@giris_gerekli
def tarama():
    return render_template(
        "analysis.html",
        doktor=aktif_doktor(),
        on_secili_tip=request.args.get("tip", ""),
        mod="yeni",
    )


@app.route("/api/analiz", methods=["POST"])
@giris_gerekli
def api_analiz():
    """Görüntü yükle → ön işle → AI analiz et → DB'ye taslak olarak kaydet."""
    if "goruntu" not in request.files:
        return jsonify({"durum": "hata", "mesaj": "Görüntü dosyası gerekli."}), 400

    dosya = request.files["goruntu"]
    if not dosya or not dosya.filename:
        return jsonify({"durum": "hata", "mesaj": "Geçersiz dosya."}), 400

    if not format_kontrol_et(dosya.filename):
        return jsonify({"durum": "hata", "mesaj": "Desteklenmeyen format. PNG/JPG/JPEG/DICOM yükleyin."}), 400

    uzman_kodu = request.form.get("uzman_kodu", "")
    hasta_ad = request.form.get("hasta_ad_soyad", "").strip()
    hasta_tc = request.form.get("hasta_tc", "").strip()
    hasta_dogum = request.form.get("hasta_dogum_tarihi", "").strip()
    protokol = request.form.get("protokol_no", "").strip()

    if not all([uzman_kodu, hasta_ad, hasta_tc, hasta_dogum, protokol]):
        return jsonify({"durum": "hata", "mesaj": "Tüm hasta bilgileri ve uzman kodu zorunludur."}), 400

    if len(hasta_tc) != 11 or not hasta_tc.isdigit():
        return jsonify({"durum": "hata", "mesaj": "TC Kimlik 11 haneli rakam olmalıdır."}), 400

    # Dosyayı kaydet
    benzersiz = uuid.uuid4().hex[:12]
    guvenli_ad = secure_filename(dosya.filename) or "goruntu.png"
    kayit_adi = f"{benzersiz}_{guvenli_ad}"
    kayit_yolu = os.path.join(YUKLEME_KLASORU, kayit_adi)
    dosya.save(kayit_yolu)

    # Ön işleme (CLAHE + gürültü giderme)
    try:
        islenmis_yolu = goruntu_hazirla(
            kayit_yolu,
            cikti_yolu=os.path.join(YUKLEME_KLASORU, f"on_{kayit_adi}.png"),
        )
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": f"Ön işleme hatası: {e}"}), 500

    # AI analizi
    sonuc = ANALIZ_MOTORU.analizi_baslat(islenmis_yolu, uzman_kodu)
    if sonuc["durum"] != "basarili":
        return jsonify(sonuc), 500

    veri = sonuc["veri"]
    isaretli_yolu = veri["islenmis_resim_yolu"]
    seviye = seviye_belirle(veri["ham_sinif"], float(veri["guven_orani_yuzde"]))

    # Tarama tipi insan-okur formata dönüştür
    tarama_tipi = (
        "MR" if uzman_kodu.startswith("mri_")
        else "CT" if uzman_kodu.startswith("ct_")
        else "X-Ray"
    )

    # Veritabanına TASLAK olarak kaydet
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        """
        INSERT INTO analiz_raporlari (
            doktor_id, tarama_tipi, uzman_kodu,
            goruntu_dosya_yolu, isaretli_goruntu_yolu,
            tf_tahmin_sonucu, ham_sinif, dogruluk_orani,
            yapay_zeka_yorumu, doktor_notu, durum, seviye,
            hasta_ad_soyad, hasta_dogum_tarihi, hasta_tc, protokol_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["doktor_id"], tarama_tipi, uzman_kodu,
            kayit_yolu, isaretli_yolu,
            veri["teshis_basligi"], veri["ham_sinif"], veri["guven_orani_yuzde"],
            veri["yapay_zeka_yorumu"], "", "Taslak", seviye,
            hasta_ad, hasta_dogum, hasta_tc, protokol,
        ),
    )
    rapor_id = cur.lastrowid
    baglanti.commit()
    baglanti.close()

    return jsonify({
        "durum": "basarili",
        "rapor_id": rapor_id,
        "redirect_url": url_for("rapor_detay", rapor_id=rapor_id),
        "veri": veri,
        "seviye": seviye,
    })


# ============================================================================
# ANALİZ SONUCU / DETAY
# ============================================================================
@app.route("/analiz/sonucu/<int:rapor_id>")
@giris_gerekli
def rapor_detay(rapor_id):
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT * FROM analiz_raporlari WHERE id = ? AND doktor_id = ?",
        (rapor_id, session["doktor_id"]),
    )
    rapor = cur.fetchone()
    baglanti.close()

    if not rapor:
        abort(404)

    return render_template(
        "analysis.html",
        doktor=aktif_doktor(),
        mod="detay",
        rapor=rapor,
    )


# ============================================================================
# TASLAK / KAYDET
# ============================================================================
@app.route("/api/save_draft", methods=["POST"])
@giris_gerekli
def api_save_draft():
    return _kayit_guncelle("Taslak")


@app.route("/api/save_report", methods=["POST"])
@giris_gerekli
def api_save_report():
    return _kayit_guncelle("Kaydedildi")


def _kayit_guncelle(yeni_durum: str):
    veri = request.get_json(silent=True) or {}
    rapor_id = veri.get("rapor_id")
    doktor_notu = (veri.get("doktor_notu") or "").strip()

    if not rapor_id:
        return jsonify({"durum": "hata", "mesaj": "rapor_id gerekli."}), 400

    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT id FROM analiz_raporlari WHERE id = ? AND doktor_id = ?",
        (rapor_id, session["doktor_id"]),
    )
    if not cur.fetchone():
        baglanti.close()
        return jsonify({"durum": "hata", "mesaj": "Rapor bulunamadı."}), 404

    cur.execute(
        "UPDATE analiz_raporlari SET doktor_notu = ?, durum = ? WHERE id = ?",
        (doktor_notu, yeni_durum, rapor_id),
    )
    baglanti.commit()
    baglanti.close()
    return jsonify({"durum": "basarili", "rapor_id": rapor_id, "yeni_durum": yeni_durum})


# ============================================================================
# RAPORLAR
# ============================================================================
@app.route("/raporlar")
@giris_gerekli
def raporlar():
    doktor_id = session["doktor_id"]
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT * FROM analiz_raporlari WHERE doktor_id = ? "
        "ORDER BY islem_tarihi DESC",
        (doktor_id,),
    )
    raporlar = cur.fetchall()

    cur.execute(
        "SELECT "
        "  COUNT(*) AS toplam, "
        "  SUM(CASE WHEN durum = 'Kaydedildi' THEN 1 ELSE 0 END) AS kaydedildi, "
        "  SUM(CASE WHEN durum = 'Taslak' THEN 1 ELSE 0 END) AS taslak, "
        "  SUM(CASE WHEN ham_sinif != 'Normal' THEN 1 ELSE 0 END) AS anomali "
        "FROM analiz_raporlari WHERE doktor_id = ?",
        (doktor_id,),
    )
    sayilar = cur.fetchone()
    baglanti.close()

    return render_template(
        "reports.html",
        doktor=aktif_doktor(),
        raporlar=raporlar,
        sayilar=sayilar,
    )


@app.route("/api/raporlar/<int:rapor_id>", methods=["DELETE"])
@giris_gerekli
def api_rapor_sil(rapor_id):
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "DELETE FROM analiz_raporlari WHERE id = ? AND doktor_id = ?",
        (rapor_id, session["doktor_id"]),
    )
    silinen = cur.rowcount
    baglanti.commit()
    baglanti.close()
    if silinen == 0:
        return jsonify({"durum": "hata", "mesaj": "Bulunamadı."}), 404
    return jsonify({"durum": "basarili"})


# ============================================================================
# PDF İNDİR
# ============================================================================
@app.route("/raporlar/<int:rapor_id>/pdf")
@giris_gerekli
def rapor_pdf(rapor_id):
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT r.*, d.ad_soyad AS d_ad, d.brans AS d_brans, d.eposta AS d_eposta "
        "FROM analiz_raporlari r JOIN doktorlar d ON r.doktor_id = d.id "
        "WHERE r.id = ? AND r.doktor_id = ?",
        (rapor_id, session["doktor_id"]),
    )
    rapor = cur.fetchone()
    baglanti.close()

    if not rapor:
        abort(404)

    veri = {
        "doktor": {
            "ad_soyad": rapor["d_ad"],
            "brans": rapor["d_brans"],
            "eposta": rapor["d_eposta"],
        },
        "hasta": {
            "ad_soyad": rapor["hasta_ad_soyad"],
            "tc": rapor["hasta_tc"],
            "dogum_tarihi": rapor["hasta_dogum_tarihi"],
            "protokol_no": rapor["protokol_no"],
        },
        "analiz": {
            "tarama_tipi": rapor["tarama_tipi"],
            "tf_tahmin_sonucu": rapor["tf_tahmin_sonucu"],
            "ham_sinif": rapor["ham_sinif"],
            "dogruluk_orani": rapor["dogruluk_orani"],
            "yapay_zeka_yorumu": rapor["yapay_zeka_yorumu"],
            "doktor_notu": rapor["doktor_notu"],
            "goruntu_dosya_yolu": rapor["goruntu_dosya_yolu"],
            "isaretli_goruntu_yolu": rapor["isaretli_goruntu_yolu"],
            "durum": rapor["durum"],
            "islem_tarihi": rapor["islem_tarihi"],
        },
    }

    pdf_yolu = rapor_olustur(rapor_id, veri)
    return send_file(pdf_yolu, as_attachment=True, download_name=f"ATGAS_Rapor_{rapor_id}.pdf")


# ============================================================================
# PROFİL
# ============================================================================
@app.route("/profil", methods=["GET", "POST"])
@giris_gerekli
def profil():
    doktor = aktif_doktor()
    mesaj = None
    hata = None

    if request.method == "POST":
        islem = request.form.get("islem")
        baglanti = veritabani_baglantisi()
        cur = baglanti.cursor()

        if islem == "bilgi_guncelle":
            ad = request.form.get("ad_soyad", "").strip()
            brans = request.form.get("brans", "").strip()
            eposta = request.form.get("eposta", "").strip().lower()
            unvan = request.form.get("unvan", "").strip() or "Uzman Doktor"

            try:
                cur.execute(
                    "UPDATE doktorlar SET ad_soyad = ?, brans = ?, eposta = ?, unvan = ? "
                    "WHERE id = ?",
                    (ad, brans, eposta, unvan, doktor["id"]),
                )
                baglanti.commit()
                session["doktor_ad"] = ad
                session["doktor_brans"] = brans
                mesaj = "Bilgiler başarıyla güncellendi."
            except Exception as e:
                hata = f"Güncelleme hatası: {e}"

        elif islem == "sifre_degistir":
            mevcut = request.form.get("mevcut_sifre", "")
            yeni = request.form.get("yeni_sifre", "")
            tekrar = request.form.get("yeni_sifre_tekrar", "")

            if not check_password_hash(doktor["sifre"], mevcut):
                hata = "Mevcut şifre hatalı."
            elif yeni != tekrar:
                hata = "Yeni şifreler uyuşmuyor."
            elif len(yeni) < 6:
                hata = "Şifre en az 6 karakter olmalıdır."
            else:
                cur.execute(
                    "UPDATE doktorlar SET sifre = ? WHERE id = ?",
                    (generate_password_hash(yeni), doktor["id"]),
                )
                baglanti.commit()
                mesaj = "Şifre güncellendi."

        baglanti.close()
        doktor = aktif_doktor()

    # İstatistikler
    baglanti = veritabani_baglantisi()
    cur = baglanti.cursor()
    cur.execute(
        "SELECT "
        "  COUNT(*) AS toplam, "
        "  SUM(CASE WHEN durum = 'Kaydedildi' THEN 1 ELSE 0 END) AS kayitli, "
        "  SUM(CASE WHEN ham_sinif != 'Normal' THEN 1 ELSE 0 END) AS anomali "
        "FROM analiz_raporlari WHERE doktor_id = ?",
        (doktor["id"],),
    )
    istat = cur.fetchone()
    baglanti.close()

    return render_template(
        "profile.html",
        doktor=doktor,
        istat=istat,
        mesaj=mesaj,
        hata=hata,
    )


# ============================================================================
# Statik dosya servisleri (yüklemeler için)
# ============================================================================
@app.route("/uploads/<path:dosya>")
@giris_gerekli
def yuklenen_dosya(dosya):
    yol = os.path.join(YUKLEME_KLASORU, dosya)
    if not os.path.exists(yol):
        abort(404)
    return send_file(yol)


# ============================================================================
@app.errorhandler(413)
def cok_buyuk(_):
    return jsonify({"durum": "hata", "mesaj": "Dosya çok büyük (maks 50 MB)."}), 413


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n[ATGAS] Flask Sunucusu baslatiliyor...")
    print(f"   * Veritabani:   {os.path.join(ANA_DIZIN, 'veritabani', 'atgas.db')}")
    print(f"   * Yuklemeler:   {YUKLEME_KLASORU}")
    print(f"   * PDF Raporlar: {RAPOR_KLASORU}")
    print(f"   * Demo Hesap:   doktor@atgas.local / 123456")
    print(f"   * URL:          http://127.0.0.1:5000\n")
    app.run(debug=False, host="127.0.0.1", port=5000)
