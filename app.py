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
    db, db_init, ornek_doktor_ekle, rol_kolonu_garanti_et, maskelenmis_url,
    Doktor, AnalizRaporu, ROLLER,
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
TENSORBOARD_LOGS_KLASORU = os.path.join(ANA_DIZIN, "modul_yapay_zeka", "logs")
os.makedirs(YUKLEME_KLASORU, exist_ok=True)
os.makedirs(ISLENMIS_KLASORU, exist_ok=True)
os.makedirs(TENSORBOARD_LOGS_KLASORU, exist_ok=True)   # akademisyen panelinde log özeti için


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

# Tablo + demo kullanıcılar (her rol için bir tane) — ilk kurulumda
with app.app_context():
    db.create_all()
    rol_kolonu_garanti_et()   # eski Supabase tablolarına 'rol' sütunu ekler (idempotent)
    ornek_doktor_ekle()       # admin / doktor / radyolog / akademisyen demo hesapları

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


def rol_gerekli(*izinli_roller):
    """Belirli rollere sahip kullanıcılara erişim verir.
    Kullanım: @rol_gerekli('admin') veya @rol_gerekli('admin', 'akademisyen')."""
    def dekorator(fn):
        @wraps(fn)
        def sarmalayici(*args, **kwargs):
            if "doktor_id" not in session:
                if request.is_json:
                    return jsonify({"durum": "hata", "mesaj": "Yetkisiz"}), 401
                flash("Lütfen önce giriş yapın.", "uyari")
                return redirect(url_for("login"))
            kul_rolu = session.get("doktor_rol", "doktor")
            if kul_rolu not in izinli_roller:
                if request.is_json:
                    return jsonify({"durum": "hata", "mesaj": "Bu sayfaya erişim yetkiniz yok."}), 403
                flash("Bu sayfaya erişim yetkiniz yok.", "uyari")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return sarmalayici
    return dekorator


def aktif_doktor() -> Doktor | None:
    if "doktor_id" not in session:
        return None
    return db.session.get(Doktor, session["doktor_id"])


def aktif_rol() -> str:
    """Oturumdaki rol — yoksa 'doktor' varsayılır (geriye dönük uyumluluk)."""
    return session.get("doktor_rol", "doktor")


@app.context_processor
def kullanici_baglami():
    """Tüm template'lerde {{ aktif_rol }} ve {{ rol_etiketi }} kullanılabilir kılar."""
    if "doktor_id" not in session:
        return {}
    rol = session.get("doktor_rol", "doktor")
    etiketler = {
        "admin": "Yönetici",
        "doktor": "Doktor",
        "radyolog": "Radyolog",
        "akademisyen": "Akademisyen",
    }
    return {"aktif_rol": rol, "rol_etiketi": etiketler.get(rol, "Doktor")}


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
    """Sidebar'daki Raporlarım altına en son 5 taramayı enjekte eder.
    - Doktor → kendi taramaları (diğer doktorların taramaları görünmez)
    - Admin → sistemdeki tüm son 5 tarama
    - Radyolog → kendi (rapor üretmez ama tutarlılık için kendi)
    - Akademisyen → sidebar'da liste yok (TensorBoard sayfası başka)
    Aktif sayfa rapor detayı ise o rapor_id 'aktif_rapor_id' olarak verilir."""
    if "doktor_id" not in session:
        return {}
    rol = session.get("doktor_rol", "doktor")

    # URL'deki /analiz/sonucu/<id> ise aktif rapor id'sini yakala
    aktif_rapor_id = None
    if request.endpoint == "rapor_detay":
        aktif_rapor_id = request.view_args.get("rapor_id") if request.view_args else None

    if rol == "akademisyen":
        return {"son_taramalar": None, "aktif_rapor_id": aktif_rapor_id}

    sorgu = AnalizRaporu.query.order_by(AnalizRaporu.islem_tarihi.desc())
    # admin + radyolog tüm sistemdeki son taramaları görür; doktor sadece kendi
    if rol not in ("admin", "radyolog"):
        sorgu = sorgu.filter_by(doktor_id=session["doktor_id"])
    son = sorgu.limit(5).all()
    return {"son_taramalar": son, "aktif_rapor_id": aktif_rapor_id}


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
            session["doktor_rol"] = doktor.rol or "doktor"
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
    rol = aktif_rol()

    # Admin → /admin sayfasına yönlendir (yönetim merkezi)
    if rol == "admin":
        return redirect(url_for("admin_panel"))
    # Akademisyen → /akademik sayfasına yönlendir (TensorBoard)
    if rol == "akademisyen":
        return redirect(url_for("akademik_panel"))

    # Doktor + Radyolog → sadece kendi taramaları (doktor-to-doctor isolation)
    # Admin asla buraya gelmez (admin_panel'e yönlendirildi)
    sorgu = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
        func.coalesce(func.avg(AnalizRaporu.dogruluk_orani), 0).label("ortalama"),
        func.count(case((AnalizRaporu.durum == "Taslak", 1))).label("taslak"),
    )
    son_sorgu = AnalizRaporu.query.order_by(AnalizRaporu.islem_tarihi.desc())
    sorgu = sorgu.filter(AnalizRaporu.doktor_id == doktor_id)
    son_sorgu = son_sorgu.filter_by(doktor_id=doktor_id)

    stats = sorgu.one()
    son_analizler = son_sorgu.limit(5).all()

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
# YENİ TARAMA — sadece doktor (admin'in de erişebilmesi için 'admin' eklendi)
# ============================================================================
@app.route("/tarama")
@rol_gerekli("doktor", "admin")
def tarama():
    return render_template(
        "analysis.html",
        doktor=aktif_doktor(),
        on_secili_tip=request.args.get("tip", ""),
        mod="yeni",
    )


@app.route("/api/analiz", methods=["POST"])
@rol_gerekli("doktor", "admin")
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
@rol_gerekli("doktor", "admin")
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
    # admin + radyolog tüm raporları görür; diğer roller yalnız kendi raporlarını.
    sorgu = AnalizRaporu.query.filter_by(id=rapor_id)
    if aktif_rol() not in ("admin", "radyolog"):
        sorgu = sorgu.filter_by(doktor_id=session["doktor_id"])
    rapor = sorgu.first()
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
@rol_gerekli("doktor", "admin")
def api_save_draft():
    return _kayit_guncelle("Taslak")


@app.route("/api/save_report", methods=["POST"])
@rol_gerekli("doktor", "admin")
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
    rol = aktif_rol()
    if rol == "akademisyen":
        # Akademisyen rapor sayfasında değil, TensorBoard'da çalışır
        return redirect(url_for("akademik_panel"))

    doktor_id = session["doktor_id"]

    # Admin opsiyonel doktor filtresi: ?doktor_id=N
    secili_doktor_id = request.args.get("doktor_id", type=int)

    sorgu_liste = AnalizRaporu.query.order_by(AnalizRaporu.islem_tarihi.desc())
    sorgu_say = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.durum == "Kaydedildi", 1))).label("kaydedildi"),
        func.count(case((AnalizRaporu.durum == "Taslak", 1))).label("taslak"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
    )

    # ROL ZORUNLULUKLARI:
    # - admin / radyolog → TÜM raporlar (anomali işaretlemelerini incelemek için)
    # - doktor → yalnız kendi raporları
    tum_raporlari_gorur = rol in ("admin", "radyolog")

    if tum_raporlari_gorur:
        if secili_doktor_id:
            sorgu_liste = sorgu_liste.filter_by(doktor_id=secili_doktor_id)
            sorgu_say = sorgu_say.filter(AnalizRaporu.doktor_id == secili_doktor_id)
    else:
        sorgu_liste = sorgu_liste.filter_by(doktor_id=doktor_id)
        sorgu_say = sorgu_say.filter(AnalizRaporu.doktor_id == doktor_id)

    rapor_listesi = sorgu_liste.all()
    sayilar = sorgu_say.one()

    # admin + radyolog → doktor filtreleme açılır listesi
    doktor_listesi = []
    if tum_raporlari_gorur:
        doktor_listesi = (
            Doktor.query
            .filter(Doktor.rol == "doktor")
            .order_by(Doktor.ad_soyad.asc())
            .all()
        )

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
        doktor_listesi=doktor_listesi,
        secili_doktor_id=secili_doktor_id,
    )


@app.route("/api/raporlar/<int:rapor_id>", methods=["DELETE"])
@giris_gerekli
def api_rapor_sil(rapor_id):
    # Doktor sadece kendi raporlarını silebilir; admin tümünü silebilir.
    # Radyolog/akademisyen rapor silemez.
    rol = aktif_rol()
    if rol not in ("doktor", "admin"):
        return jsonify({"durum": "hata", "mesaj": "Silme yetkiniz yok."}), 403
    sorgu = AnalizRaporu.query.filter_by(id=rapor_id)
    if rol != "admin":
        sorgu = sorgu.filter_by(doktor_id=session["doktor_id"])
    rapor = sorgu.first()
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
    # admin + radyolog tüm raporların PDF'ini indirebilir; doktor sadece kendi raporları
    sorgu = AnalizRaporu.query.filter_by(id=rapor_id)
    if aktif_rol() not in ("admin", "radyolog"):
        sorgu = sorgu.filter_by(doktor_id=session["doktor_id"])
    rapor = sorgu.first()
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
# ADMIN PANELİ — kullanıcı yönetimi (sadece 'admin' rolü)
# ============================================================================
EPOSTA_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


@app.route("/admin")
@rol_gerekli("admin")
def admin_panel():
    """Tüm kullanıcıların listesi + sistem istatistikleri."""
    kullanicilar = Doktor.query.order_by(Doktor.olusturulma_tarihi.desc()).all()

    # Rol başına sayım
    rol_sayilari = dict(
        db.session.query(Doktor.rol, func.count(Doktor.id)).group_by(Doktor.rol).all()
    )
    sistem_stats = db.session.query(
        func.count(AnalizRaporu.id).label("toplam_rapor"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
    ).one()

    return render_template(
        "admin.html",
        doktor=aktif_doktor(),
        kullanicilar=kullanicilar,
        rol_sayilari=rol_sayilari,
        sistem_stats={
            "toplam_rapor": sistem_stats.toplam_rapor or 0,
            "anomali": sistem_stats.anomali or 0,
            "toplam_kullanici": len(kullanicilar),
        },
        roller=ROLLER,
    )


@app.route("/admin/kullanici-ekle", methods=["POST"])
@rol_gerekli("admin")
def admin_kullanici_ekle():
    """Yeni kullanıcı kaydı oluşturur."""
    ad_soyad = request.form.get("ad_soyad", "").strip()
    eposta   = request.form.get("eposta", "").strip().lower()
    sifre    = request.form.get("sifre", "")
    brans    = request.form.get("brans", "").strip()
    unvan    = request.form.get("unvan", "").strip() or "Uzman"
    rol      = request.form.get("rol", "doktor").strip().lower()

    # Doğrulama
    if not all([ad_soyad, eposta, sifre, brans]):
        flash("Ad Soyad, e-posta, şifre ve branş zorunlu alanlardır.", "danger")
        return redirect(url_for("admin_panel"))
    if not EPOSTA_REGEX.match(eposta):
        flash("Geçersiz e-posta formatı.", "danger")
        return redirect(url_for("admin_panel"))
    if len(sifre) < 6:
        flash("Şifre en az 6 karakter olmalıdır.", "danger")
        return redirect(url_for("admin_panel"))
    if rol not in ROLLER:
        flash(f"Geçersiz rol. Geçerli değerler: {', '.join(ROLLER)}.", "danger")
        return redirect(url_for("admin_panel"))
    if Doktor.query.filter_by(eposta=eposta).first():
        flash(f"'{eposta}' zaten kayıtlı.", "danger")
        return redirect(url_for("admin_panel"))

    try:
        yeni = Doktor(
            ad_soyad=ad_soyad, eposta=eposta, brans=brans,
            unvan=unvan, rol=rol,
        )
        yeni.sifre_ayarla(sifre)
        db.session.add(yeni)
        db.session.commit()
        flash(f"✓ {yeni.rol_etiketi} kaydı eklendi: {ad_soyad} ({eposta})", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Kayıt hatası: {e}", "danger")

    return redirect(url_for("admin_panel"))


@app.route("/admin/kullanici/<int:kid>")
@rol_gerekli("admin")
def admin_kullanici_detay(kid):
    """Bir kullanıcının profilini ve istatistiklerini gösterir + düzenleme formu."""
    k = db.session.get(Doktor, kid)
    if not k:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("admin_panel"))

    # Bu kullanıcıya ait rapor istatistikleri
    rapor_stats = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.count(case((AnalizRaporu.durum == "Kaydedildi", 1))).label("kaydedildi"),
        func.count(case((AnalizRaporu.durum == "Taslak", 1))).label("taslak"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
    ).filter(AnalizRaporu.doktor_id == kid).one()

    son_raporlari = (
        AnalizRaporu.query
        .filter_by(doktor_id=kid)
        .order_by(AnalizRaporu.islem_tarihi.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin_kullanici.html",
        doktor=aktif_doktor(),
        hedef=k,
        rapor_stats={
            "toplam":     rapor_stats.toplam or 0,
            "kaydedildi": rapor_stats.kaydedildi or 0,
            "taslak":     rapor_stats.taslak or 0,
            "anomali":    rapor_stats.anomali or 0,
        },
        son_raporlari=son_raporlari,
        roller=ROLLER,
    )


@app.route("/admin/kullanici/<int:kid>/guncelle", methods=["POST"])
@rol_gerekli("admin")
def admin_kullanici_guncelle(kid):
    """Bir kullanıcının bilgilerini günceller (ad/eposta/branş/unvan/rol)."""
    k = db.session.get(Doktor, kid)
    if not k:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("admin_panel"))

    yeni_ad     = request.form.get("ad_soyad", "").strip()
    yeni_eposta = request.form.get("eposta", "").strip().lower()
    yeni_brans  = request.form.get("brans", "").strip()
    yeni_unvan  = request.form.get("unvan", "").strip() or "Uzman"
    yeni_rol    = request.form.get("rol", k.rol).strip().lower()

    if not all([yeni_ad, yeni_eposta, yeni_brans]):
        flash("Ad, e-posta ve branş zorunlu.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))
    if not EPOSTA_REGEX.match(yeni_eposta):
        flash("Geçersiz e-posta formatı.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))
    if yeni_rol not in ROLLER:
        flash("Geçersiz rol.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))
    # Kendi rolünü admin'den çıkarmasını engelle (kilitlenme önlemi)
    if k.id == session["doktor_id"] and yeni_rol != "admin":
        flash("Kendi yönetici rolünüzü değiştiremezsiniz.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))
    # E-posta benzersizliği
    cakisma = Doktor.query.filter(Doktor.eposta == yeni_eposta, Doktor.id != kid).first()
    if cakisma:
        flash(f"'{yeni_eposta}' başka bir kullanıcıya ait.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))

    try:
        k.ad_soyad = yeni_ad
        k.eposta = yeni_eposta
        k.brans = yeni_brans
        k.unvan = yeni_unvan
        k.rol = yeni_rol
        db.session.commit()
        flash("✓ Bilgiler güncellendi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Güncelleme hatası: {e}", "danger")
    return redirect(url_for("admin_kullanici_detay", kid=kid))


@app.route("/admin/kullanici/<int:kid>/sifre", methods=["POST"])
@rol_gerekli("admin")
def admin_kullanici_sifre(kid):
    """Yöneticinin başka kullanıcının şifresini sıfırlaması."""
    k = db.session.get(Doktor, kid)
    if not k:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("admin_panel"))
    yeni = request.form.get("yeni_sifre", "")
    if len(yeni) < 6:
        flash("Şifre en az 6 karakter olmalıdır.", "danger")
        return redirect(url_for("admin_kullanici_detay", kid=kid))
    try:
        k.sifre_ayarla(yeni)
        db.session.commit()
        flash(f"✓ {k.ad_soyad} kullanıcısının şifresi güncellendi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Şifre güncelleme hatası: {e}", "danger")
    return redirect(url_for("admin_kullanici_detay", kid=kid))


@app.route("/admin/kullanici/<int:kid>/sil", methods=["POST"])
@rol_gerekli("admin")
def admin_kullanici_sil(kid):
    """Kullanıcı silme — kendi hesabını silmeyi engeller."""
    if kid == session["doktor_id"]:
        flash("Kendi hesabınızı silemezsiniz.", "danger")
        return redirect(url_for("admin_panel"))
    k = db.session.get(Doktor, kid)
    if not k:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("admin_panel"))

    # Doktor silinmek isteniyor ama raporları varsa: AnalizRaporu.doktor_id ondelete=RESTRICT.
    # FK nedeniyle hata almamak için önce kontrol et.
    rapor_sayisi = AnalizRaporu.query.filter_by(doktor_id=kid).count()
    if rapor_sayisi > 0:
        flash(
            f"Bu kullanıcının {rapor_sayisi} raporu var. Önce raporları silmelisiniz.",
            "danger",
        )
        return redirect(url_for("admin_panel"))

    try:
        db.session.delete(k)
        db.session.commit()
        flash(f"✓ {k.ad_soyad} silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Silme hatası: {e}", "danger")
    return redirect(url_for("admin_panel"))


# ============================================================================
# AKADEMİK PANEL — TensorBoard (sadece 'akademisyen' ve 'admin')
# ============================================================================
TENSORBOARD_PORT = _env_int("TENSORBOARD_PORT", 6006)
TENSORBOARD_LOGDIR = os.path.join(ANA_DIZIN, "modul_yapay_zeka", "logs")
_tensorboard_proc = {"p": None, "log": ""}  # subprocess referansı + son log çıktısı


def _tensorboard_calisiyor_mu() -> bool:
    p = _tensorboard_proc.get("p")
    return p is not None and p.poll() is None


def _port_dinleniyor_mu(port: int, host: str = "127.0.0.1", zaman_asimi: float = 0.5) -> bool:
    """Verilen port bir TCP servisi tarafından dinleniyor mu?"""
    import socket
    try:
        with socket.create_connection((host, port), timeout=zaman_asimi):
            return True
    except OSError:
        return False


def _tensorboard_baslat():
    """Arka planda TensorBoard sunucusunu başlatır.
    Birden fazla launcher dener (tensorboard CLI → python -m tensorboard.main → tensorboard).
    Süreç ÖLMEMİŞSE referansı saklanır — port hemen açılmasa bile (TB ilk açılışta yavaş)."""
    import subprocess, sys, shutil, time

    if _tensorboard_calisiyor_mu():
        return True, "Zaten çalışıyor.", _tensorboard_proc["p"].pid

    # Eğer port bizim subprocess'imiz olmadan dinleniyorsa: önceki Flask çalışmasından
    # kalmış olabilir. Onu adopte edelim — yeniden başlatmaya gerek yok.
    if _port_dinleniyor_mu(TENSORBOARD_PORT):
        pid = _port_uzerindeki_pidi_bul(TENSORBOARD_PORT)
        if pid:
            _tensorboard_proc["adopted_pid"] = pid
        return True, f"Port {TENSORBOARD_PORT} zaten dinleniyor (PID {pid or '?'})", pid

    # Log klasörü yoksa oluştur (TensorBoard boş klasörle de ayağa kalkar; kullanıcıya
    # boş ekran gösterir ama hata vermez). Akademisyen sonradan model değerlendirme
    # ile log üretebilir.
    os.makedirs(TENSORBOARD_LOGDIR, exist_ok=True)

    args_ortak = [
        "--logdir", TENSORBOARD_LOGDIR,
        "--host", "127.0.0.1",
        "--port", str(TENSORBOARD_PORT),
        "--reload_interval", "5",
    ]

    # Sırayla denenecek launcher'lar
    launchers = []
    tb_bin = shutil.which("tensorboard")
    if tb_bin:
        launchers.append([tb_bin])
    launchers.append([sys.executable, "-m", "tensorboard.main"])
    launchers.append([sys.executable, "-m", "tensorboard"])

    creationflags = 0
    if sys.platform == "win32":
        # CREATE_NEW_PROCESS_GROUP + DETACHED_PROCESS → Flask kapansa bile çocuk yaşar
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        )

    son_hata = "Bilinmeyen hata."
    for launcher in launchers:
        cmd = launcher + args_ortak
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=ANA_DIZIN,
                creationflags=creationflags,
                close_fds=True,
            )
        except FileNotFoundError as e:
            son_hata = f"Komut bulunamadı: {' '.join(launcher)} ({e})"
            continue
        except Exception as e:
            son_hata = f"Başlatma hatası ({' '.join(launcher)}): {e}"
            continue

        # Süreci 3 saniye boyunca izle — bu sürede ölürse hemen anla, ölmediyse ayakta say
        baslangic = time.time()
        port_acildi = False
        sure_sinir = 3.0
        while time.time() - baslangic < sure_sinir:
            if p.poll() is not None:
                break  # süreç ölmüş — bir sonraki launcher'ı dene
            if _port_dinleniyor_mu(TENSORBOARD_PORT):
                port_acildi = True
                break
            time.sleep(0.25)

        if p.poll() is None:
            # Süreç hâlâ çalışıyor → BAŞARI. Port henüz açılmadıysa bile saklarız;
            # TF'in ilk yükleme süresi 8-15 sn olabilir, frontend'de iframe daha sonra
            # otomatik refresh edilecek.
            _tensorboard_proc["p"] = p
            _tensorboard_proc.pop("adopted_pid", None)
            mesaj = (
                f"TensorBoard hazır (PID {p.pid})." if port_acildi
                else f"TensorBoard başlatıldı (PID {p.pid}) — port birkaç saniye içinde açılacak."
            )
            return True, mesaj, p.pid

        # Süreç ölmüş → log oku, sonraki launcher'a geç
        try:
            cikti = (p.stdout.read() if p.stdout else b"") or b""
            cikti_str = cikti.decode("utf-8", errors="replace")[:600]
        except Exception:
            cikti_str = ""
        son_hata = f"[{' '.join(launcher)}] çıkış kodu={p.returncode} | log: {cikti_str.strip() or '(boş)'}"

    return False, f"TensorBoard başlatılamadı. Son hata: {son_hata}", None


def _port_uzerindeki_pidi_bul(port: int) -> int | None:
    """Verilen TCP portunu LISTENING durumda dinleyen sürecin PID'ini döner.
    Windows ve POSIX desteklenir."""
    import subprocess, sys
    try:
        if sys.platform == "win32":
            r = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=5,
            )
            arama = f":{port}"
            for satir in r.stdout.splitlines():
                if arama in satir and "LISTENING" in satir:
                    parcalar = satir.split()
                    pid = parcalar[-1].strip()
                    if pid.isdigit():
                        return int(pid)
        else:
            r = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=5,
            )
            for pid in r.stdout.split():
                if pid.isdigit():
                    return int(pid)
    except Exception:
        return None
    return None


def _pid_oldur(pid: int) -> bool:
    """Verilen PID'i sonlandırır (Windows: taskkill /F, POSIX: kill -9)."""
    import subprocess, sys
    try:
        if sys.platform == "win32":
            r = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
        else:
            r = subprocess.run(
                ["kill", "-9", str(pid)],
                capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
    except Exception:
        return False


def _tensorboard_durdur():
    """Çalışan TB sürecini durdurur. Önce kendi subprocess referansını dener;
    referans yoksa veya farklı bir süreç port'u dinliyorsa PID'i bulup öldürür."""
    import subprocess

    p = _tensorboard_proc.get("p")
    if p is not None:
        try:
            p.terminate()
            try:
                p.wait(timeout=4)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        _tensorboard_proc["p"] = None
        return True, "TensorBoard süreci sonlandırıldı."

    # Subprocess referansımız yok — port'u dinleyen başka bir TB var mı?
    pid = _port_uzerindeki_pidi_bul(TENSORBOARD_PORT)
    if pid:
        if _pid_oldur(pid):
            _tensorboard_proc.pop("adopted_pid", None)
            return True, f"Bağımsız TensorBoard süreci sonlandırıldı (PID {pid})."
        return False, f"PID {pid} sonlandırılamadı (yetki sorunu olabilir)."

    return False, "Çalışan TensorBoard süreci yok."


@app.route("/akademik/tensorboard-durdur", methods=["POST"])
@rol_gerekli("akademisyen", "admin")
def akademik_tb_durdur():
    durduruldu, mesaj = _tensorboard_durdur()
    # Port hâlâ kapalı mı doğrula
    hala_calisiyor = _tensorboard_calisiyor_mu() or _port_dinleniyor_mu(TENSORBOARD_PORT)
    return jsonify({
        "durum": "basarili" if durduruldu else "hata",
        "mesaj": mesaj,
        "calisiyor": hala_calisiyor,
    })


@app.route("/akademik")
@rol_gerekli("akademisyen", "admin")
def akademik_panel():
    """TensorBoard + model performans metrik özeti."""
    # Mevcut log klasörlerini özetle (akademisyen ham metrikleri görsün)
    log_kayitlari = []
    if os.path.isdir(TENSORBOARD_LOGDIR):
        for ad in sorted(os.listdir(TENSORBOARD_LOGDIR), reverse=True):
            yol = os.path.join(TENSORBOARD_LOGDIR, ad)
            if not os.path.isdir(yol):
                continue
            ozet = {}
            ozet_yolu = os.path.join(yol, "ozet_metrikler.json")
            if os.path.exists(ozet_yolu):
                try:
                    import json
                    with open(ozet_yolu, "r", encoding="utf-8") as fh:
                        ozet = json.load(fh) or {}
                except Exception:
                    ozet = {}
            log_kayitlari.append({"ad": ad, "ozet": ozet})

    # Sistemdeki AI değerlendirme metrikleri (DB'den)
    metrikler = db.session.query(
        func.count(AnalizRaporu.id).label("toplam"),
        func.coalesce(func.avg(AnalizRaporu.dogruluk_orani), 0).label("ort_dogruluk"),
        func.count(case((AnalizRaporu.ham_sinif != "Normal", 1))).label("anomali"),
        func.count(case((AnalizRaporu.ham_sinif == "Normal", 1))).label("normal"),
    ).one()

    tb_calisiyor = _tensorboard_calisiyor_mu() or _port_dinleniyor_mu(TENSORBOARD_PORT)
    return render_template(
        "akademik.html",
        doktor=aktif_doktor(),
        log_kayitlari=log_kayitlari,
        tensorboard_url=f"http://127.0.0.1:{TENSORBOARD_PORT}/",
        tensorboard_calisiyor=tb_calisiyor,
        metrikler={
            "toplam": metrikler.toplam or 0,
            "ort_dogruluk": round(float(metrikler.ort_dogruluk or 0), 1),
            "anomali": metrikler.anomali or 0,
            "normal": metrikler.normal or 0,
        },
    )


@app.route("/akademik/tensorboard-baslat", methods=["POST"])
@rol_gerekli("akademisyen", "admin")
def akademik_tb_baslat():
    ok, mesaj, pid = _tensorboard_baslat()
    return jsonify({
        "durum": "basarili" if ok else "hata",
        "mesaj": mesaj,
        "url": f"http://127.0.0.1:{TENSORBOARD_PORT}/",
        "pid": pid,
        "port_acik": _port_dinleniyor_mu(TENSORBOARD_PORT),
        "calisiyor": _tensorboard_calisiyor_mu() or _port_dinleniyor_mu(TENSORBOARD_PORT),
    })


@app.route("/akademik/tensorboard-durum")
@rol_gerekli("akademisyen", "admin")
def akademik_tb_durum():
    """Frontend'in TB hazır mı diye kısa kısa yokladığı uçnokta."""
    return jsonify({
        "calisiyor": _tensorboard_calisiyor_mu() or _port_dinleniyor_mu(TENSORBOARD_PORT),
        "port_acik": _port_dinleniyor_mu(TENSORBOARD_PORT),
        "url": f"http://127.0.0.1:{TENSORBOARD_PORT}/",
    })


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

    print("\n[ATGAS] Flask Sunucusu baslatiliyor...")
    print(f"   * ORM:          SQLAlchemy 2.0 + Flask-SQLAlchemy")
    print(f"   * DB URL:       {maskelenmis_url()[:80]}...")
    print(f"   * Yuklemeler:   {YUKLEME_KLASORU}")
    print(f"   * PDF Raporlar: {RAPOR_KLASORU}")
    print(f"   * Maks Upload:  {MAX_UPLOAD_MB} MB")
    print(f"   * Debug:        {FLASK_DEBUG}")
    print(f"   * TensorBoard:  http://127.0.0.1:{TENSORBOARD_PORT} (akademisyen panelinde baslatilir)")
    print(f"   * Demo Hesaplar (rol bazli):")
    print(f"       - Doktor      : {os.environ.get('DEMO_DOKTOR_EPOSTA',      'doktor@atgas.local')} / {os.environ.get('DEMO_DOKTOR_SIFRE',      '123456')}")
    print(f"       - Admin       : {os.environ.get('DEMO_ADMIN_EPOSTA',       'admin@atgas.local')} / {os.environ.get('DEMO_ADMIN_SIFRE',       'admin123')}")
    print(f"       - Radyolog    : {os.environ.get('DEMO_RADYOLOG_EPOSTA',    'radyolog@atgas.local')} / {os.environ.get('DEMO_RADYOLOG_SIFRE',    'radyolog123')}")
    print(f"       - Akademisyen : {os.environ.get('DEMO_AKADEMISYEN_EPOSTA', 'akademisyen@atgas.local')} / {os.environ.get('DEMO_AKADEMISYEN_SIFRE', 'akademisyen123')}")
    print(f"   * URL:          http://{FLASK_HOST}:{FLASK_PORT}\n")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
