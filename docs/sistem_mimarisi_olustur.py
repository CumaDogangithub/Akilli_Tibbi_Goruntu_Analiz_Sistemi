"""
ATGAS — Sistem Mimarisi Diyagramı (Clean Edition)

Çalıştırma:
    python docs/sistem_mimarisi_olustur.py

Çıktı: docs/ATGAS_Sistem_Mimarisi.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle


# ============================================================================
# Sade renk paleti — tek vurgu (indigo) + kategori bazlı 3 accent
# ============================================================================
RENK = {
    # Ana çerçeve & yapı
    "indigo":       "#1E3A8A",
    "indigo_orta":  "#3B5BCB",
    "indigo_acik":  "#EEF2FF",   # layer band background
    "indigo_xa":    "#F8FAFF",

    # Layer accent renkleri (sadece sol şerit + başlıklar için)
    "kullanici":    "#0E7490",   # teal
    "kullanici_a":  "#ECFEFF",
    "ag":           "#0369A1",   # sky blue
    "ag_a":         "#F0F9FF",
    "uygulama":     "#1E3A8A",   # indigo (ana)
    "uygulama_a":   "#EEF2FF",
    "veri":         "#047857",   # emerald
    "veri_a":       "#ECFDF5",

    # Genel
    "siyah":     "#0F172A",
    "metin":     "#1F2937",
    "metin_a":   "#6B7280",
    "kenar":     "#E5E7EB",
    "beyaz":     "#FFFFFF",
    "kanvas":    "#FAFBFC",
    "golge":     "#0F172A",
}


# ============================================================================
# Yardımcılar
# ============================================================================
def golge(ax, x, y, w, h, kose=0.10, dx=0.04, dy=-0.04, alpha=0.07):
    s = FancyBboxPatch(
        (x + dx, y + dy), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={kose}",
        facecolor=RENK["golge"], edgecolor="none",
        alpha=alpha, zorder=1.5,
    )
    ax.add_patch(s)


def kart(ax, x, y, w, h, baslik, alt_satirlar=None,
         renk_aksent="indigo", baslik_boyut=11, alt_boyut=8.5,
         baslik_yuksek=False, kose=0.08, golge_var=True):
    """Beyaz kart + üst kenar boyunca ince renkli accent çubuğu.

    Renkli başlık şeridi YERİNE üstte sadece 0.04 kalınlığında accent çizgi.
    Başlık metni siyah/koyu — daha sakin görünüm.
    """
    if golge_var:
        golge(ax, x, y, w, h, kose=kose)

    # Beyaz ana gövde
    ana = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={kose}",
        facecolor=RENK["beyaz"], edgecolor=RENK["kenar"],
        linewidth=1.0, zorder=2,
    )
    ax.add_patch(ana)

    # Üst accent şeridi (4 piksel yükseklikte)
    aks_h = 0.06
    aks = FancyBboxPatch(
        (x, y + h - aks_h), w, aks_h,
        boxstyle=f"round,pad=0,rounding_size={kose}",
        facecolor=RENK[renk_aksent], edgecolor="none", zorder=2.5,
    )
    ax.add_patch(aks)

    # Başlık konumu (üstte)
    bas_y = y + h - aks_h - 0.20 if alt_satirlar else y + h - aks_h - h / 2 + 0.15
    if baslik_yuksek:
        bas_y = y + h - aks_h - 0.30

    ax.text(x + w / 2, bas_y, baslik,
            ha="center", va="top", fontsize=baslik_boyut,
            fontweight="bold", color=RENK["siyah"], zorder=4)

    # Alt satırlar
    if alt_satirlar:
        if isinstance(alt_satirlar, str):
            alt_satirlar = [alt_satirlar]
        # İlk satır başlığın altında ~0.30
        y_kursoru = bas_y - 0.30
        for satir in alt_satirlar:
            ax.text(x + w / 2, y_kursoru, satir,
                    ha="center", va="top", fontsize=alt_boyut,
                    color=RENK["metin_a"], zorder=4)
            y_kursoru -= 0.26


def layer_band(ax, x, y, w, h, no, baslik, renk_arka, renk_aks):
    """Hafif tonlu arka plan + sol kenarda accent çubuk. Layer label
    band'ın HEMEN ÜSTÜNDE — kartlarla çakışmasın."""
    # Arka plan
    bg = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.0,rounding_size=0.10",
        facecolor=RENK[renk_arka], edgecolor="none", zorder=0.7,
    )
    ax.add_patch(bg)

    # Sol dikey accent çubuk
    aks = Rectangle(
        (x, y), 0.10, h,
        facecolor=RENK[renk_aks], edgecolor="none", zorder=0.8,
    )
    ax.add_patch(aks)

    # Layer etiketi: band'ın ÜSTÜNDE (dış), küçük ve sade
    label_y = y + h + 0.18
    # No kapsülü
    ax.text(x + 0.20, label_y, no, ha="left", va="center",
            fontsize=10, fontweight="bold", color=RENK["beyaz"], zorder=1.5,
            bbox=dict(facecolor=RENK[renk_aks], edgecolor="none",
                      boxstyle="round,pad=0.30", linewidth=0))
    # Başlık (no'nun yanında, daha sakin)
    ax.text(x + 0.70, label_y, baslik, ha="left", va="center",
            fontsize=10.5, fontweight="bold", color=RENK[renk_aks],
            zorder=1.5)


def dikey_ok(ax, x, y_top, y_bot, etiket=None, renk="indigo_orta",
             pill_yan=0.40):
    """Tam dikey ok. Pill etiketi ok'un sağına ofsetlenmiş."""
    a = FancyArrowPatch(
        (x, y_top), (x, y_bot),
        arrowstyle="-|>", mutation_scale=18,
        color=RENK[renk], linewidth=2.0, zorder=4,
    )
    ax.add_patch(a)
    if etiket:
        my = (y_top + y_bot) / 2
        ax.text(x + pill_yan, my, etiket,
                ha="left", va="center", fontsize=8.5,
                fontweight="bold", color=RENK[renk], zorder=6,
                bbox=dict(facecolor=RENK["beyaz"], edgecolor=RENK[renk],
                          boxstyle="round,pad=0.30", linewidth=1.0))


def ince_baglanti(ax, x1, y1, x2, y2, renk="indigo_orta", lw=1.0):
    """[Eski] Düz ince bağlantı çizgisi — dağınık görünüm."""
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=10,
        color=RENK[renk], linewidth=lw, zorder=3.5, alpha=0.55,
    )
    ax.add_patch(a)


def manifold_baglanti(ax, x_kaynak, y_kaynak_alt,
                      hedef_xler, y_hedef_ust,
                      renk="indigo_orta", lw=1.6):
    """Köşeli 'manifold' bağlantı: kaynak kartından tek dikey ok yatay
    bus çubuğuna iner, oradan her hedef karta tek dikey ok iner.
    Tüm dirsekler 90°.

    x_kaynak: kaynak kart x merkezi
    y_kaynak_alt: kaynak kartın alt y'si (oktan başlayacak)
    hedef_xler: hedef kartların x merkezleri (liste)
    y_hedef_ust: hedeflerin üst y'si
    """
    # Bus çubuğunun y konumu — iki seviye arası ortada
    y_bus = (y_kaynak_alt + y_hedef_ust) / 2

    # 1) Kaynaktan bus'a düşey hat (ok başsız, sade çizgi)
    ax.plot([x_kaynak, x_kaynak], [y_kaynak_alt, y_bus],
            color=RENK[renk], linewidth=lw, zorder=3, solid_capstyle="round")

    # 2) Yatay bus — tüm hedefleri ve kaynağı kapsar
    x_min = min(hedef_xler + [x_kaynak])
    x_max = max(hedef_xler + [x_kaynak])
    ax.plot([x_min, x_max], [y_bus, y_bus],
            color=RENK[renk], linewidth=lw + 0.4, zorder=3,
            solid_capstyle="round")

    # 3) Bus'tan her hedefe düşey ok (uçta ok başı)
    for x in hedef_xler:
        a = FancyArrowPatch(
            (x, y_bus), (x, y_hedef_ust),
            arrowstyle="-|>", mutation_scale=14,
            color=RENK[renk], linewidth=lw, zorder=3.5,
        )
        ax.add_patch(a)

    # 4) Bus üzerine küçük "node" daireleri — kavşak görsel ipucu
    for x in hedef_xler + [x_kaynak]:
        ax.plot(x, y_bus, "o", markersize=5,
                markerfacecolor=RENK[renk],
                markeredgecolor=RENK["beyaz"],
                markeredgewidth=1.2, zorder=4)


# ============================================================================
# Ana çizim
# ============================================================================
def main():
    fig, ax = plt.subplots(figsize=(17, 12), dpi=200)
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(RENK["kanvas"])

    # ============== BAŞLIK ==============
    ax.add_patch(Rectangle((0.5, 11.55), 16, 0.06,
                          facecolor=RENK["indigo"], edgecolor="none",
                          zorder=1))
    ax.text(8.5, 11.15, "ATGAS", ha="center", va="center",
            fontsize=30, fontweight="bold", color=RENK["indigo"])
    ax.text(8.5, 10.65, "S i s t e m   M i m a r i s i",
            ha="center", va="center", fontsize=14,
            color=RENK["metin_a"], style="italic")

    # Sağ üst sürüm rozeti
    ax.text(16.0, 11.15, "v2.1", ha="right", va="center",
            fontsize=9, fontweight="bold", color=RENK["indigo"],
            bbox=dict(facecolor=RENK["indigo_acik"],
                      edgecolor=RENK["indigo"],
                      boxstyle="round,pad=0.4", linewidth=1.0))
    ax.text(16.0, 10.75, "atgas.cumadogan.com",
            ha="right", va="center", fontsize=8,
            color=RENK["metin_a"], family="monospace")

    # ============== KATMAN 1 — KULLANICI ==============
    L1_y = 9.05
    L1_h = 1.05
    layer_band(ax, 0.5, L1_y, 16.0, L1_h,
               "01", "KULLANICI",
               "kullanici_a", "kullanici")

    # 4 rol kartı geniş aralıklı
    rol_y = L1_y + 0.20
    rol_h = 0.65
    rol_w = 3.40
    rol_gap = 0.30
    rol_baslangic = (16.0 - 4 * rol_w - 3 * rol_gap) / 2 + 0.5

    roller = [
        ("Doktor",        "Görüntü yükle · AI analizi"),
        ("Radyolog",      "Tüm raporları denetle"),
        ("Yönetici",      "Kullanıcı + rapor yönetimi"),
        ("Akademisyen",   "TB metrikleri + analiz"),
    ]
    for i, (ad, alt) in enumerate(roller):
        x = rol_baslangic + i * (rol_w + rol_gap)
        kart(ax, x, rol_y, rol_w, rol_h, ad,
             alt_satirlar=[alt],
             renk_aksent="kullanici",
             baslik_boyut=11, alt_boyut=8.5, kose=0.08)

    # KATMAN 1 → 2 dikey ok (orta)
    dikey_ok(ax, 8.5, 9.00, 8.50, etiket="HTTPS  ·  443",
             renk="indigo_orta")

    # ============== KATMAN 2 — AĞ ==============
    L2_y = 7.10
    L2_h = 1.05
    layer_band(ax, 0.5, L2_y, 16.0, L2_h,
               "02", "AĞ + CDN",
               "ag_a", "ag")

    # Cloudflare merkezi tek kart
    kart(ax, 4.5, L2_y + 0.20, 8, 0.65,
         "Cloudflare  CDN + SSL/TLS",
         alt_satirlar=["DNS · Edge Cache · DDoS koruma · WAF · "
                      "Origin 37.157.255.26"],
         renk_aksent="ag",
         baslik_boyut=11.5, alt_boyut=8, kose=0.08)

    # KATMAN 2 → 3
    dikey_ok(ax, 8.5, 7.05, 6.55, etiket="TLS terminate",
             renk="indigo_orta")

    # ============== KATMAN 3 — UYGULAMA ==============
    L3_y = 2.40
    L3_h = 4.30
    layer_band(ax, 0.5, L3_y, 16.0, L3_h,
               "03", "UYGULAMA  ·  VPS + DOCKER",
               "uygulama_a", "uygulama")

    # Nginx
    kart(ax, 4.5, 5.85, 8, 0.65,
         "Nginx  ·  Reverse Proxy",
         alt_satirlar=["/  →  Flask:5001     /tensorboard/  →  TB:6006"],
         renk_aksent="uygulama",
         baslik_boyut=11.5, alt_boyut=8.5, kose=0.08)

    # Nginx → Flask oku
    dikey_ok(ax, 8.5, 5.80, 5.30, renk="indigo_orta", pill_yan=0)

    # Flask App — büyük orta kart (tek satır altyazılı, daha sıkışık)
    kart(ax, 3.5, 4.55, 10, 0.85,
         "Flask 3.0  Application",
         alt_satirlar=[
             "Werkzeug WSGI  ·  Jinja2  ·  Session auth  ·  "
             "@rol_gerekli  ·  4 rol  ·  24 endpoint  ·  Port 5001",
         ],
         renk_aksent="uygulama", baslik_yuksek=True,
         baslik_boyut=15, alt_boyut=8.5, kose=0.10)

    # Modüller — Flask altında 4 grid
    modul_y = 2.45
    modul_h = 1.55
    modul_w = 3.40
    modul_gap = 0.30
    modul_baslangic = (16.0 - 4 * modul_w - 3 * modul_gap) / 2 + 0.5

    moduller = [
        ("modul_yapay_zeka",
         ["TensorFlow 2.21",
          "Keras 3.14",
          "EfficientNetV2-M",
          "5 uzman model · DICOM"]),
        ("modul_goruntu_isleme",
         ["OpenCV-headless 4.8",
          "Resize · Mask · Heatmap",
          "Pillow · pydicom",
          "Format dönüştürme"]),
        ("modul_raporlama",
         ["reportlab 4.0",
          "Türkçe font (DejaVu)",
          "KVKK maskeleme",
          "PDF + zip rapor"]),
        ("modul_veritabani",
         ["SQLAlchemy 2.0",
          "Flask-Migrate",
          "pg8000 sürücü",
          "Doktor + AnalizRaporu"]),
    ]
    modul_xler = []
    for i, (ad, alt) in enumerate(moduller):
        x = modul_baslangic + i * (modul_w + modul_gap)
        kart(ax, x, modul_y, modul_w, modul_h, ad,
             alt_satirlar=alt,
             renk_aksent="uygulama",
             baslik_boyut=12, alt_boyut=8, kose=0.08,
             baslik_yuksek=True)
        modul_xler.append(x + modul_w / 2)

    # Flask → modüller manifold bağlantı (köşeli, tek bus)
    manifold_baglanti(ax, x_kaynak=8.5, y_kaynak_alt=4.55,
                      hedef_xler=modul_xler,
                      y_hedef_ust=modul_y + modul_h,
                      renk="indigo_orta", lw=1.6)

    # ============== KATMAN 4 — VERİ ==============
    L4_y = 0.55
    L4_h = 1.55
    layer_band(ax, 0.5, L4_y, 16.0, L4_h,
               "04", "VERİ + SÜREÇ",
               "veri_a", "veri")

    # 3 yan yana eşit kart
    veri_y = L4_y + 0.15
    veri_h = 1.10
    veri_w = 4.85
    veri_gap = 0.40
    veri_baslangic = (16.0 - 3 * veri_w - 2 * veri_gap) / 2 + 0.5

    veri_kartlari = [
        ("TensorBoard",
         ["Port 6006 · subprocess",
          "--path_prefix=/tensorboard",
          "modul_yapay_zeka/logs/"]),
        ("Persistent Volumes",
         ["./uploads",
          "./analiz_sonuclari",
          "./logs (bind mount)"]),
        ("Supabase PostgreSQL",
         ["Pooler 6543 · IPv4",
          "500 MB free tier",
          "pg8000 dialect"]),
    ]
    veri_xler = []
    for i, (ad, alt) in enumerate(veri_kartlari):
        x = veri_baslangic + i * (veri_w + veri_gap)
        kart(ax, x, veri_y, veri_w, veri_h, ad,
             alt_satirlar=alt,
             renk_aksent="veri",
             baslik_boyut=13, alt_boyut=8.5, kose=0.08,
             baslik_yuksek=True)
        veri_xler.append(x + veri_w / 2)

    # Modüller → veri kartları manifold bağlantı: tüm modüllerin ALT noktasından
    # ortak bir yatay bus'a iner, oradan her veri kartına ok ile çıkar.
    # Modüllerin merkez x'i ortalama alınarak tek bir "kaynak çıkış noktası"
    # olarak kullanılır (manifold yapısının üst tarafı zaten 4 inişi var).
    # Burada SOURCE'lar 4 modül, TARGET'lar 3 veri kartı olduğu için
    # iki yönlü manifold gerekiyor: önce modüllerden bus'a, sonra bus'tan
    # veri kartlarına.
    y_modul_alt = modul_y
    y_veri_ust = veri_y + veri_h
    y_bus = (y_modul_alt + y_veri_ust) / 2

    # Her modülden bus'a düşey hat
    for x in modul_xler:
        ax.plot([x, x], [y_modul_alt, y_bus],
                color=RENK["indigo_orta"], linewidth=1.6, zorder=3,
                solid_capstyle="round")
        # Kavşak nokta dairesi
        ax.plot(x, y_bus, "o", markersize=5,
                markerfacecolor=RENK["indigo_orta"],
                markeredgecolor=RENK["beyaz"],
                markeredgewidth=1.2, zorder=4)

    # Bus çubuğu — tüm modül + veri kartlarını kapsayan yatay hat
    x_min = min(modul_xler + veri_xler)
    x_max = max(modul_xler + veri_xler)
    ax.plot([x_min, x_max], [y_bus, y_bus],
            color=RENK["indigo_orta"], linewidth=2.0, zorder=3,
            solid_capstyle="round")

    # Bus'tan her veri kartına düşey ok
    for x in veri_xler:
        a = FancyArrowPatch(
            (x, y_bus), (x, y_veri_ust),
            arrowstyle="-|>", mutation_scale=14,
            color=RENK["indigo_orta"], linewidth=1.6, zorder=3.5,
        )
        ax.add_patch(a)
        # Veri kartı kavşak noktası
        ax.plot(x, y_bus, "o", markersize=5,
                markerfacecolor=RENK["indigo_orta"],
                markeredgecolor=RENK["beyaz"],
                markeredgewidth=1.2, zorder=4)

    # ============== FOOTER ==============
    ax.text(0.5, 0.20,
            "docs/sistem_mimarisi_olustur.py",
            ha="left", va="center", fontsize=8,
            color=RENK["metin_a"], family="monospace")
    ax.text(16.5, 0.20,
            "Stack: Flask · TensorFlow · PostgreSQL · Docker · Nginx",
            ha="right", va="center", fontsize=8,
            color=RENK["metin_a"], family="monospace")

    ax.set_ylim(0, 12)

    cikti = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ATGAS_Sistem_Mimarisi.png")
    plt.savefig(cikti, bbox_inches="tight", dpi=200,
                facecolor=RENK["kanvas"], edgecolor="none",
                pad_inches=0.4)
    plt.close(fig)
    boyut_kb = round(os.path.getsize(cikti) / 1024, 1)
    print(f"[OK] Sistem mimarisi: {cikti} ({boyut_kb} KB)")
    return cikti


if __name__ == "__main__":
    main()
