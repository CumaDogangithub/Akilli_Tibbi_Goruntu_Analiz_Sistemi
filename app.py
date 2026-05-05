"""
ATGAS — Akıllı Tıbbi Görüntü Analiz Sistemi
Flask Backend (SQLAlchemy ORM + PostgreSQL/Supabase)
"""

import os
import re
import uuid
from datetime import datetime, date
from functools import wraps

# .env dosyasındaki ortam değişkenlerini yükle (DATABASE_URL, ATGAS_SECRET vs.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, send_file, flash, abort,
)
from sqlalchemy import func, case
from werkzeug.utils import secure_filename

# --- ATGAS Modülleri ---
from modul_veritabani import (
    db, db_init, ornek_doktor_ekle, maskelenmis_url,
    Doktor, AnalizRaporu,
)
from modul_goruntu_isleme import (
    hazirla as goruntu_hazirla,
    format_kontrol_et,
    dicom_onizleme_uret,
    dicom_dosyasi_mi,
    DICOM_UZANTILARI,
)
from modul_yapay_zeka import AtgasAnalizMotoru
from modul_raporlama import rapor_olustur, RAPOR_KLASORU


# ============================================================================
# DOSYA SİSTEMİ YERLEŞİMİ — taşınabilir
# DB'ye sadece dosya ADI yazılır (örn: 'orig_xxx.png').
# Diskteki tam yol  =  ANA_DIZIN + UPLOADS_DIR (.env)  +  dosya_adi
# Bu sayede DB kayıtları başka makineye/cloud'a aktarıldığında bozulmaz.
# ============================================================================
ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR_REL = os.environ.get("UPLOADS_DIR", "static/uploads").replace("\\", "/")
RESULTS_DIR_REL = os.environ.get("RESULTS_DIR", "static/img/analiz_sonuclari").replace("\\", "/")

YUKLEME_KLASORU = os.path.join(ANA_DIZIN, *UPLOADS_DIR_REL.split("/"))
ISLENMIS_KLASORU = os.path.join(ANA_DIZIN, *RESULTS_DIR_REL.split("/"))
os.makedirs(YUKLEME_KLASORU, exist_ok=True)
os.makedirs(ISLENMIS_KLASORU, exist_ok=True)


def _basename_norm(yol: str) -> str:
    """Hem Windows hem Linux ayraçlı yoldan dosya adını çıkarır (defansif)."""
    if not yol:
        return ""
    return str(yol).replace("\\", "/").rsplit("/", 1)[-1]


def yukleme_yolu(yol_veya_dosya_adi: str) -> str:
    """DB'deki dosya adından (veya eski absolute path'ten) diskteki tam yolu üretir.
    Eski kayıtlarda absolute path olabileceği ihtimaline karşı defansif."""
    f = _basename_norm(yol_veya_dosya_adi)
    return os.path.join(YUKLEME_KLASORU, f) if f else ""


def sonuc_yolu(yol_veya_dosya_adi: str) -> str:
    """analiz_sonuclari klasöründeki tam yolu üretir (defansif)."""
    f = _basename_norm(yol_veya_dosya_adi)
    return os.path.join(ISLENMIS_KLASORU, f) if f else ""

# ============================================================================
# UYGULAMA YAPILANDIRMASI — tümü .env'den
# ============================================================================
def _env_int(ad, varsayilan):
    try: return int(os.environ.get(ad, varsayilan))
    except (TypeError, ValueError): return varsayilan

def _env_bool(ad, varsayilan=False):
    return str(os.environ.get(ad, varsayilan)).strip().lower() in ("1", "true", "yes", "evet")

FLASK_HOST    = os.environ.get("FLASK_HOST", "127.0.0.1")
FLASK_PORT    = _env_int("FLASK_PORT", 5001)
FLASK_DEBUG   = _env_bool("FLASK_DEBUG", False)
MAX_UPLOAD_MB = _env_int("MAX_UPLOAD_MB", 50)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ATGAS_SECRET") or "atgas-degistir-bu-secret"
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# SQLAlchemy + Flask-Migrate
db_init(app)

# Tablo + demo doktor — ilk kurulumda
with app.app_context():
    db.create_all()
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


def aktif_doktor() -> Doktor | None:
    if "doktor_id" not in session:
        return None
    return db.session.get(Doktor, session["doktor_id"])


@app.template_filter("kisa_tarih")
def _kisa_tarih(deger):
    """Hem datetime objesi hem string için 'YYYY-MM-DD HH:MM' formatına çevirir."""
    if deger is None:
        return ""
    if hasattr(deger, "strftime"):
        return deger.strftime("%Y-%m-%d %H:%M")
    return str(deger)[:16]


@app.template_filter("kisa_gun")
def _kisa_gun(deger):
    """Hem date/datetime hem string için 'YYYY-MM-DD' formatına çevirir."""
    if deger is None:
        return ""
    if hasattr(deger, "strftime"):
        return deger.strftime("%Y-%m-%d")
    return str(deger)[:10]


@app.template_filter("dosya_adi")
def _dosya_adi(yol):
    """Hem absolute (Windows/Linux) hem relative path'ten dosya adı döner.
    Eski kayıtların absolute path içermesi durumuna karşı defansif."""
    if not yol:
        return ""
    # Hem Windows hem Linux ayraçlarını desteklemek için normalleştir
    return str(yol).replace("\\", "/").rsplit("/", 1)[-1]


@app.context_processor
def kenar_cubugu_son_taramalar():
    """Sidebar'daki Raporlarım altına en son 5 taramayı enjekte eder."""
    if "doktor_id" not in session:
        return {}
    son = (
        AnalizRaporu.query
        .filter_by(doktor_id=session["doktor_id"])
        .order_by(AnalizRaporu.islem_tarihi.desc())
        .limit(5)
        .all()
    )
    return {"son_taramalar": son}


def seviye_belirle(ham_sinif: str, dogruluk: float) -> str:
    if ham_sinif == "Normal":
        return "Temiz"
    if dogruluk >= 85:
        return "Kritik"
    return "Orta"


def _str_to_date(s: str) -> date:
    """'YYYY-MM-DD' → date. Hatalıysa ValueError."""
    return datetime.strptime(s, "%Y-%m-%d").date()


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
        doktor = Doktor.query.filter_by(eposta=eposta).first()
        if doktor and doktor.sifre_dogrula(sifre):
            session["doktor_id"] = doktor.id
            session["doktor_ad"] = doktor.ad_soyad
            session["doktor_brans"] = doktor.brans
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

    # Tek sorguda tüm istatistikler (aggregate)
    stats = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
        func.coalesce(func.avg(AnalizRaporu.dogruluk_orani), 0).label("ortalama"),
        func.count(case((AnalizRaporu.durum == "Taslak", 1))).label("taslak"),
    ).filter(AnalizRaporu.doktor_id == doktor_id).one()

    son_analizler = (
        AnalizRaporu.query
        .filter_by(doktor_id=doktor_id)
        .order_by(AnalizRaporu.islem_tarihi.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        doktor=aktif_doktor(),
        istatistikler={
            "toplam": stats.toplam or 0,
            "anomali": stats.anomali or 0,
            "ortalama_dogruluk": round(float(stats.ortalama or 0), 1),
            "taslak": stats.taslak or 0,
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
    """Görüntü yükle → ön işle → AI analiz et → session'a 'bekleyen' olarak koy."""
    if "goruntu" not in request.files:
        return jsonify({"durum": "hata", "mesaj": "Görüntü dosyası gerekli."}), 400

    dosya = request.files["goruntu"]
    if not dosya or not dosya.filename:
        return jsonify({"durum": "hata", "mesaj": "Geçersiz dosya."}), 400

    uzman_kodu = request.form.get("uzman_kodu", "")
    hasta_ad = request.form.get("hasta_ad_soyad", "").strip()
    hasta_tc = request.form.get("hasta_tc", "").strip()
    hasta_dogum = request.form.get("hasta_dogum_tarihi", "").strip()
    protokol = request.form.get("protokol_no", "").strip()

    if not all([uzman_kodu, hasta_ad, hasta_tc, hasta_dogum, protokol]):
        return jsonify({"durum": "hata", "mesaj": "Tüm hasta bilgileri ve uzman kodu zorunludur."}), 400
    if len(hasta_tc) != 11 or not hasta_tc.isdigit():
        return jsonify({"durum": "hata", "mesaj": "TC Kimlik 11 haneli rakam olmalıdır."}), 400

    # Dosyayı diske kaydet
    benzersiz = uuid.uuid4().hex[:12]
    guvenli_ad = secure_filename(dosya.filename) or "goruntu"
    kayit_adi = f"{benzersiz}_{guvenli_ad}"
    kayit_yolu = os.path.join(YUKLEME_KLASORU, kayit_adi)
    dosya.save(kayit_yolu)

    if not format_kontrol_et(kayit_yolu):
        try: os.remove(kayit_yolu)
        except OSError: pass
        return jsonify({"durum": "hata",
                        "mesaj": "Desteklenmeyen format. DICOM (.dcm/.dicom/.dic/.ima) veya PNG/JPG/JPEG yükleyin."}), 400

    # DICOM ise browser-uyumlu PNG önizleme
    onizleme_yolu = kayit_yolu  # disk full path
    if dicom_dosyasi_mi(kayit_yolu):
        try:
            onizleme_yolu = os.path.join(YUKLEME_KLASORU, f"orig_{kayit_adi}.png")
            dicom_onizleme_uret(kayit_yolu, onizleme_yolu)
        except Exception as e:
            return jsonify({"durum": "hata", "mesaj": f"DICOM önizleme hatası: {e}"}), 500

    # CLAHE + gürültü giderme
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
    isaretli_yolu = veri["islenmis_resim_yolu"]  # disk full path
    seviye = seviye_belirle(veri["ham_sinif"], float(veri["guven_orani_yuzde"]))

    tarama_tipi = (
        "MR" if uzman_kodu.startswith("mri_")
        else "CT" if uzman_kodu.startswith("ct_")
        else "X-Ray"
    )

    # DB'ye/Session'a SADECE DOSYA ADI yaz (taşınabilirlik için)
    session["bekleyen_analiz"] = {
        "tarama_tipi": tarama_tipi,
        "uzman_kodu": uzman_kodu,
        "goruntu_dosya_yolu":   os.path.basename(onizleme_yolu),
        "isaretli_goruntu_yolu": os.path.basename(isaretli_yolu),
        "tf_tahmin_sonucu": veri["teshis_basligi"],
        "ham_sinif": veri["ham_sinif"],
        "dogruluk_orani": veri["guven_orani_yuzde"],
        "yapay_zeka_yorumu": veri["yapay_zeka_yorumu"],
        "seviye": seviye,
        "hasta_ad_soyad": hasta_ad,
        "hasta_dogum_tarihi": hasta_dogum,
        "hasta_tc": hasta_tc,
        "protokol_no": protokol,
        "olusturulma": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return jsonify({
        "durum": "basarili",
        "redirect_url": url_for("rapor_onizleme"),
        "veri": veri,
        "seviye": seviye,
    })


@app.route("/analiz/onizleme")
@giris_gerekli
def rapor_onizleme():
    bekleyen = session.get("bekleyen_analiz")
    if not bekleyen:
        flash("Görüntülenecek bekleyen analiz yok. Yeni bir tarama başlatın.", "uyari")
        return redirect(url_for("tarama"))
    return render_template(
        "analysis.html",
        doktor=aktif_doktor(),
        mod="onizleme",
        rapor=bekleyen,
    )


# ============================================================================
# ANALİZ DETAY
# ============================================================================
@app.route("/analiz/sonucu/<int:rapor_id>")
@giris_gerekli
def rapor_detay(rapor_id):
    rapor = AnalizRaporu.query.filter_by(id=rapor_id, doktor_id=session["doktor_id"]).first()
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

    bekleyen = session.get("bekleyen_analiz")

    # YENİ AKIŞ: rapor_id yok ama bekleyen analiz var → ilk INSERT
    if not rapor_id and bekleyen:
        try:
            rapor = AnalizRaporu(
                doktor_id=session["doktor_id"],
                tarama_tipi=bekleyen["tarama_tipi"],
                uzman_kodu=bekleyen["uzman_kodu"],
                goruntu_dosya_yolu=bekleyen["goruntu_dosya_yolu"],
                isaretli_goruntu_yolu=bekleyen["isaretli_goruntu_yolu"],
                tf_tahmin_sonucu=bekleyen["tf_tahmin_sonucu"],
                ham_sinif=bekleyen["ham_sinif"],
                dogruluk_orani=bekleyen["dogruluk_orani"],
                yapay_zeka_yorumu=bekleyen["yapay_zeka_yorumu"],
                doktor_notu=doktor_notu,
                durum=yeni_durum,
                seviye=bekleyen["seviye"],
                hasta_ad_soyad=bekleyen["hasta_ad_soyad"],
                hasta_dogum_tarihi=_str_to_date(bekleyen["hasta_dogum_tarihi"]),
                hasta_tc=bekleyen["hasta_tc"],
                protokol_no=bekleyen["protokol_no"],
            )
            db.session.add(rapor)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"durum": "hata", "mesaj": f"Veritabanına yazılamadı: {e}"}), 500

        session.pop("bekleyen_analiz", None)
        return jsonify({
            "durum": "basarili",
            "rapor_id": rapor.id,
            "yeni_durum": yeni_durum,
            "yeni_url": url_for("rapor_detay", rapor_id=rapor.id),
        })

    # MEVCUT AKIŞ: var olan raporu güncelle
    if not rapor_id:
        return jsonify({"durum": "hata", "mesaj": "rapor_id gerekli veya bekleyen analiz yok."}), 400

    rapor = AnalizRaporu.query.filter_by(id=rapor_id, doktor_id=session["doktor_id"]).first()
    if not rapor:
        return jsonify({"durum": "hata", "mesaj": "Rapor bulunamadı."}), 404

    rapor.doktor_notu = doktor_notu
    rapor.durum = yeni_durum
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"durum": "hata", "mesaj": f"Güncelleme hatası: {e}"}), 500

    return jsonify({"durum": "basarili", "rapor_id": rapor.id, "yeni_durum": yeni_durum})


# ============================================================================
# RAPORLAR
# ============================================================================
@app.route("/raporlar")
@giris_gerekli
def raporlar():
    doktor_id = session["doktor_id"]

    rapor_listesi = (
        AnalizRaporu.query
        .filter_by(doktor_id=doktor_id)
        .order_by(AnalizRaporu.islem_tarihi.desc())
        .all()
    )

    sayilar = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.durum == "Kaydedildi", 1))).label("kaydedildi"),
        func.count(case((AnalizRaporu.durum == "Taslak", 1))).label("taslak"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
    ).filter(AnalizRaporu.doktor_id == doktor_id).one()

    return render_template(
        "reports.html",
        doktor=aktif_doktor(),
        raporlar=rapor_listesi,
        sayilar={
            "toplam": sayilar.toplam or 0,
            "kaydedildi": sayilar.kaydedildi or 0,
            "taslak": sayilar.taslak or 0,
            "anomali": sayilar.anomali or 0,
        },
    )


@app.route("/api/raporlar/<int:rapor_id>", methods=["DELETE"])
@giris_gerekli
def api_rapor_sil(rapor_id):
    rapor = AnalizRaporu.query.filter_by(id=rapor_id, doktor_id=session["doktor_id"]).first()
    if not rapor:
        return jsonify({"durum": "hata", "mesaj": "Bulunamadı."}), 404
    try:
        db.session.delete(rapor)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500
    return jsonify({"durum": "basarili"})


# ============================================================================
# PDF İNDİR
# ============================================================================
@app.route("/raporlar/<int:rapor_id>/pdf")
@giris_gerekli
def rapor_pdf(rapor_id):
    rapor = (
        AnalizRaporu.query
        .filter_by(id=rapor_id, doktor_id=session["doktor_id"])
        .first()
    )
    if not rapor:
        abort(404)

    veri = {
        "doktor": {
            "ad_soyad": rapor.doktor.ad_soyad,
            "brans": rapor.doktor.brans,
            "eposta": rapor.doktor.eposta,
        },
        "hasta": {
            "ad_soyad": rapor.hasta_ad_soyad,
            "tc": rapor.hasta_tc,
            "dogum_tarihi": rapor.hasta_dogum_tarihi.isoformat() if rapor.hasta_dogum_tarihi else "",
            "protokol_no": rapor.protokol_no,
        },
        "analiz": {
            "tarama_tipi": rapor.tarama_tipi,
            "tf_tahmin_sonucu": rapor.tf_tahmin_sonucu,
            "ham_sinif": rapor.ham_sinif,
            "dogruluk_orani": float(rapor.dogruluk_orani or 0),
            "yapay_zeka_yorumu": rapor.yapay_zeka_yorumu,
            "doktor_notu": rapor.doktor_notu,
            # DB'de sadece dosya adı var → PDF için runtime'da disk yoluna çevir
            "goruntu_dosya_yolu":  yukleme_yolu(rapor.goruntu_dosya_yolu),
            "isaretli_goruntu_yolu": sonuc_yolu(rapor.isaretli_goruntu_yolu),
            "durum": rapor.durum,
            "islem_tarihi": rapor.islem_tarihi.strftime("%Y-%m-%d %H:%M") if rapor.islem_tarihi else "",
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

        if islem == "bilgi_guncelle":
            doktor.ad_soyad = request.form.get("ad_soyad", "").strip()
            doktor.brans = request.form.get("brans", "").strip()
            doktor.eposta = request.form.get("eposta", "").strip().lower()
            doktor.unvan = request.form.get("unvan", "").strip() or "Uzman Doktor"
            try:
                db.session.commit()
                session["doktor_ad"] = doktor.ad_soyad
                session["doktor_brans"] = doktor.brans
                mesaj = "Bilgiler başarıyla güncellendi."
            except Exception as e:
                db.session.rollback()
                hata = f"Güncelleme hatası: {e}"

        elif islem == "sifre_degistir":
            mevcut = request.form.get("mevcut_sifre", "")
            yeni = request.form.get("yeni_sifre", "")
            tekrar = request.form.get("yeni_sifre_tekrar", "")

            if not doktor.sifre_dogrula(mevcut):
                hata = "Mevcut şifre hatalı."
            elif yeni != tekrar:
                hata = "Yeni şifreler uyuşmuyor."
            elif len(yeni) < 6:
                hata = "Şifre en az 6 karakter olmalıdır."
            else:
                doktor.sifre_ayarla(yeni)
                try:
                    db.session.commit()
                    mesaj = "Şifre güncellendi."
                except Exception as e:
                    db.session.rollback()
                    hata = f"Güncelleme hatası: {e}"

    # İstatistikler
    istat = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.durum == "Kaydedildi", 1))).label("kayitli"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
    ).filter(AnalizRaporu.doktor_id == doktor.id).one()

    return render_template(
        "profile.html",
        doktor=doktor,
        istat={
            "toplam": istat.toplam or 0,
            "kayitli": istat.kayitli or 0,
            "anomali": istat.anomali or 0,
        },
        mesaj=mesaj,
        hata=hata,
    )


# ============================================================================
# Statik dosya servisi
# ============================================================================
@app.route("/uploads/<path:dosya>")
@giris_gerekli
def yuklenen_dosya(dosya):
    yol = os.path.join(YUKLEME_KLASORU, dosya)
    if not os.path.exists(yol):
        abort(404)
    return send_file(yol)


@app.errorhandler(413)
def cok_buyuk(_):
    return jsonify({"durum": "hata", "mesaj": f"Dosya çok büyük (maks {MAX_UPLOAD_MB} MB)."}), 413


# ============================================================================
if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    demo_eposta = os.environ.get("DEMO_DOKTOR_EPOSTA", "doktor@atgas.local")
    demo_sifre  = os.environ.get("DEMO_DOKTOR_SIFRE", "123456")

    print("\n[ATGAS] Flask Sunucusu baslatiliyor...")
    print(f"   * ORM:          SQLAlchemy 2.0 + Flask-SQLAlchemy")
    print(f"   * DB URL:       {maskelenmis_url()[:80]}...")
    print(f"   * Yuklemeler:   {YUKLEME_KLASORU}")
    print(f"   * PDF Raporlar: {RAPOR_KLASORU}")
    print(f"   * Maks Upload:  {MAX_UPLOAD_MB} MB")
    print(f"   * Debug:        {FLASK_DEBUG}")
    print(f"   * Demo Hesap:   {demo_eposta} / {demo_sifre}")
    print(f"   * URL:          http://{FLASK_HOST}:{FLASK_PORT}\n")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
