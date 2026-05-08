"""
ATGAS — Veritabanı ER Diyagramı Üretici (PNG)

Çalıştırma:
    python docs/db_semasi_olustur.py

Çıktı: docs/ATGAS_DB_Semasi.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


RENK = {
    "lacivert":   "#0D2B4F",
    "mavi":       "#1C6EF2",
    "mavi_a":     "#E8F0FE",
    "yesil":      "#1F8B4C",
    "yesil_a":    "#E8F5E9",
    "turuncu":    "#E07A1F",
    "turuncu_a":  "#FDF2E5",
    "kirmizi":    "#C0392B",
    "gri":        "#5C6770",
    "gri_a":      "#F4F6F8",
    "kenar":      "#A8B0BA",
    "metin":      "#1B1F23",
    "beyaz":      "#FFFFFF",
}


def tablo_ciz(ax, x, y, w, baslik, satirlar, renk_baslik="lacivert"):
    """ER diagramı tarzı tablo: başlık şeridi + sütun listesi.

    satirlar: list of (anahtar_simgesi, sutun_adi, tip)
       anahtar_simgesi: 'PK', 'FK', '🔑', '' vb.
    """
    baslik_h = 0.45
    satir_h = 0.36
    h = baslik_h + len(satirlar) * satir_h + 0.10

    # Dış çerçeve
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        facecolor=RENK["beyaz"], edgecolor=RENK[renk_baslik],
        linewidth=1.8, zorder=2,
    ))

    # Başlık şeridi (rounded sadece üstte istenir ama matplotlib basit
    # doğal değil — düz dolgu kullanıyoruz)
    ax.add_patch(FancyBboxPatch(
        (x, y + h - baslik_h), w, baslik_h,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        facecolor=RENK[renk_baslik], edgecolor=RENK[renk_baslik],
        linewidth=0, zorder=3,
    ))
    ax.text(x + w / 2, y + h - baslik_h / 2 - 0.03, baslik,
            ha="center", va="center", fontsize=12,
            fontweight="bold", color=RENK["beyaz"], zorder=4)

    # Sütunlar
    for i, (sim, ad, tip) in enumerate(satirlar):
        cy = y + h - baslik_h - (i + 0.5) * satir_h - 0.05
        # Zebra
        if i % 2 == 1:
            ax.add_patch(FancyBboxPatch(
                (x + 0.04, cy - satir_h / 2 + 0.02),
                w - 0.08, satir_h - 0.04,
                boxstyle="round,pad=0,rounding_size=0",
                facecolor=RENK["gri_a"], edgecolor="none", zorder=2.5,
            ))
        # Anahtar simgesi (PK / FK)
        if sim:
            renk = RENK["turuncu"] if sim == "PK" else (
                RENK["mavi"] if sim == "FK" else RENK["gri"])
            ax.text(x + 0.18, cy, sim, ha="left", va="center",
                    fontsize=8, fontweight="bold", color=renk, zorder=4)
        # Sütun adı
        fw = "bold" if sim in ("PK", "FK") else "normal"
        ax.text(x + 0.65, cy, ad, ha="left", va="center",
                fontsize=10, fontweight=fw, color=RENK["metin"], zorder=4)
        # Tip (sağa hizalı)
        ax.text(x + w - 0.18, cy, tip, ha="right", va="center",
                fontsize=8.5, color=RENK["gri"], style="italic", zorder=4)

    return h  # toplam yükseklik döner — bağlantı oklarını yerleştirmek için


def iliski_ok(ax, x1, y1, x2, y2, etiket="1 : N", renk="lacivert"):
    """İki tablo arasında ilişki oku — '1 : N' kardinalitesi ile."""
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="->", mutation_scale=18,
        color=RENK[renk], linewidth=2.0, zorder=5,
        connectionstyle="arc3,rad=0",
    )
    ax.add_patch(a)
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    ax.text(mx, my + 0.20, etiket, ha="center", va="bottom",
            fontsize=10, fontweight="bold", color=RENK[renk], zorder=6,
            bbox=dict(facecolor=RENK["beyaz"], edgecolor=RENK[renk],
                      boxstyle="round,pad=0.25", linewidth=1.0))


def main():
    fig, ax = plt.subplots(figsize=(15, 10), dpi=200)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # Başlık
    fig.suptitle("ATGAS — Veritabanı Şeması (ER Diyagramı)",
                 fontsize=18, fontweight="bold",
                 color=RENK["lacivert"], y=0.97)
    ax.text(7.5, 9.55,
            "PostgreSQL · Supabase · SQLAlchemy 2.0 ORM",
            ha="center", fontsize=11, color=RENK["gri"], style="italic")

    # === DOKTORLAR tablosu (sol) ===
    doktorlar_satirlar = [
        ("PK",  "id",                    "INTEGER · auto"),
        ("",    "ad_soyad",              "VARCHAR(100)"),
        ("UQ",  "eposta",                "VARCHAR(150) · idx"),
        ("",    "sifre",                 "VARCHAR(255)"),
        ("",    "brans",                 "VARCHAR(50)"),
        ("",    "unvan",                 "VARCHAR(50)"),
        ("",    "rol",                   "VARCHAR(20) · idx"),
        ("",    "olusturulma_tarihi",    "DATETIME"),
    ]
    h_d = tablo_ciz(ax, 0.7, 4.5, 5.4,
                    "doktorlar   (Doktor)", doktorlar_satirlar,
                    renk_baslik="mavi")

    # === ANALIZ_RAPORLARI tablosu (sağ) ===
    analiz_satirlar = [
        ("PK",  "id",                       "INTEGER · auto"),
        ("FK",  "doktor_id",                "→ doktorlar.id"),
        ("",    "tarama_tipi",              "VARCHAR(10)"),
        ("",    "uzman_kodu",               "VARCHAR(20)"),
        ("",    "goruntu_dosya_yolu",       "VARCHAR(500)"),
        ("",    "isaretli_goruntu_yolu",    "VARCHAR(500)"),
        ("",    "tf_tahmin_sonucu",         "VARCHAR(100)"),
        ("",    "ham_sinif",                "VARCHAR(50)"),
        ("",    "dogruluk_orani",           "NUMERIC(5,2)"),
        ("",    "yapay_zeka_yorumu",        "TEXT"),
        ("",    "doktor_notu",              "TEXT"),
        ("",    "durum",                    "VARCHAR(20) · idx"),
        ("",    "seviye",                   "VARCHAR(20)"),
        ("",    "hasta_ad_soyad",           "VARCHAR(200)"),
        ("",    "hasta_dogum_tarihi",       "DATE"),
        ("",    "hasta_tc",                 "VARCHAR(11)"),
        ("",    "protokol_no",              "VARCHAR(200)"),
        ("",    "islem_tarihi",             "DATETIME · idx"),
    ]
    h_a = tablo_ciz(ax, 8.4, 1.5, 5.9,
                    "analiz_raporlari   (AnalizRaporu)", analiz_satirlar,
                    renk_baslik="turuncu")

    # === İlişki oku: doktorlar.id  →  analiz_raporlari.doktor_id ===
    # Sol tablonun sağ kenarından, sağ tablonun sol üst kısmına
    iliski_ok(ax,
              0.7 + 5.4, 4.5 + h_d / 2,        # doktorlar sağ orta
              8.4, 1.5 + h_a - 0.55,           # analiz_raporlari sol üst
              etiket="1 : N", renk="lacivert")

    # === Roller bilgi kutusu (sol alt) ===
    rol_kutu = FancyBboxPatch(
        (0.7, 1.5), 5.4, 2.4,
        boxstyle="round,pad=0.04,rounding_size=0.10",
        facecolor=RENK["mavi_a"], edgecolor=RENK["mavi"],
        linewidth=1.2, zorder=2,
    )
    ax.add_patch(rol_kutu)
    ax.text(0.7 + 5.4 / 2, 1.5 + 2.4 - 0.30,
            "Rol Değerleri (rol sütunu)",
            ha="center", fontsize=11, fontweight="bold",
            color=RENK["mavi"])

    rol_satirlari = [
        ("admin",        "Sistem yöneticisi · tüm rapor + kullanıcı"),
        ("doktor",       "Yeni tarama · kendi raporları"),
        ("radyolog",     "Tüm raporlar · denetim · silme YOK"),
        ("akademisyen",  "TensorBoard · model metrikleri"),
    ]
    for i, (rol, aciklama) in enumerate(rol_satirlari):
        y = 1.5 + 2.4 - 0.85 - i * 0.40
        ax.text(0.95, y, f"• {rol}", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color=RENK["lacivert"])
        ax.text(2.55, y, aciklama, ha="left", va="center",
                fontsize=8.5, color=RENK["metin"])

    # === Lejant ===
    leg_y = 0.55
    ax.text(0.7, leg_y + 0.20, "Lejant:", fontsize=9,
            fontweight="bold", color=RENK["metin"])
    legends = [
        ("PK", "Primary Key", "turuncu"),
        ("FK", "Foreign Key", "mavi"),
        ("UQ", "Unique",       "gri"),
        ("idx", "Indexed",     "gri"),
    ]
    for i, (sim, ad, c) in enumerate(legends):
        x = 1.55 + i * 2.4
        ax.text(x, leg_y + 0.20, sim, fontsize=9, fontweight="bold",
                color=RENK[c])
        ax.text(x + 0.50, leg_y + 0.20, ad, fontsize=9, color=RENK["metin"])

    # === Notlar (sağ alt) ===
    not_metin = (
        "Notlar:\n"
        "  • doktor_id ON DELETE RESTRICT — rapor sahibi doktor silinemez\n"
        "  • goruntu_dosya_yolu DB'de yalnız dosya adı tutar (taşınabilirlik)\n"
        "  • ham_sinif ≠ 'Normal' iken anomali kabul edilir\n"
        "  • durum ∈ {'Taslak', 'Kaydedildi'} — flow state\n"
        "  • seviye ∈ {'Kritik', 'Orta', 'Temiz'} — UI rozeti"
    )
    ax.text(8.4, 1.0, not_metin, fontsize=8, va="top", ha="left",
            color=RENK["gri"], family="monospace",
            bbox=dict(facecolor=RENK["gri_a"], edgecolor=RENK["kenar"],
                      boxstyle="round,pad=0.4", linewidth=0.8))

    # Footer
    plt.figtext(0.5, 0.02,
                "Üretildi: docs/db_semasi_olustur.py  ·  "
                "Kaynak: modul_veritabani/modeller.py",
                ha="center", fontsize=8, color=RENK["gri"])

    cikti = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ATGAS_DB_Semasi.png")
    plt.savefig(cikti, bbox_inches="tight", dpi=200,
                facecolor="white", edgecolor="none")
    plt.close(fig)
    boyut_kb = round(os.path.getsize(cikti) / 1024, 1)
    print(f"[OK] DB semasi: {cikti} ({boyut_kb} KB)")
    return cikti


if __name__ == "__main__":
    main()
