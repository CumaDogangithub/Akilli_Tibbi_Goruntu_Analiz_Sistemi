"""
ATGAS — Model Değerlendirme Raporu (PDF) üreticisi.

Görev: "Model eğitim sürecinde kullanılan metriklerin izlenmesi ve TensorBoard
ile görselleştirilmesi" akademik dökümantasyonu.

Kullanım:
    1) Önce metrikleri üret:    python -m modul_yapay_zeka.degerlendirme
    2) PDF raporunu oluştur:    python -m modul_yapay_zeka.rapor_olustur
       → docs/Model_Degerlendirme_Raporu.pdf
"""

import os
import sys
import io
import json
import glob
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


ANA_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_KOK   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
# Proje dökümanları docs/ klasöründe tutulur (raporlar/ hasta analiz raporları içindir)
DOCS_KLASORU = os.path.join(ANA_DIZIN, "docs")
CIKTI = os.path.join(DOCS_KLASORU, "Model_Degerlendirme_Raporu.pdf")


# ============================================================================
# FONT KAYDI (Türkçe karakter desteği)
# ============================================================================
def _font_kaydet():
    adaylar = [
        ("ATG", "C:/Windows/Fonts/arial.ttf"),
        ("ATG-Bold", "C:/Windows/Fonts/arialbd.ttf"),
        ("ATG-Italic", "C:/Windows/Fonts/ariali.ttf"),
    ]
    yedek = [
        ("ATG", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("ATG-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    try:
        for ad, yol in adaylar:
            if os.path.exists(yol):
                pdfmetrics.registerFont(TTFont(ad, yol))
        if "ATG" in pdfmetrics.getRegisteredFontNames() and \
           "ATG-Bold" in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFontFamily(
                "ATG", normal="ATG", bold="ATG-Bold",
                italic="ATG-Italic" if "ATG-Italic" in pdfmetrics.getRegisteredFontNames() else "ATG",
            )
            return "ATG"
        for ad, yol in yedek:
            if os.path.exists(yol):
                pdfmetrics.registerFont(TTFont(ad, yol))
        if "ATG" in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFontFamily("ATG", normal="ATG", bold="ATG-Bold")
            return "ATG"
    except Exception:
        pass
    return "Helvetica"


FONT      = _font_kaydet()
FONT_BOLD = "ATG-Bold" if FONT == "ATG" else "Helvetica-Bold"


# ============================================================================
# RENK PALETİ (UI ile uyumlu)
# ============================================================================
P = {
    "ana_arka":    colors.HexColor("#0D1117"),
    "panel":       colors.HexColor("#161B22"),
    "yuzey":       colors.HexColor("#21262D"),
    "kenarlik":    colors.HexColor("#30363D"),
    "mavi":        colors.HexColor("#1C6EF2"),
    "yesil":       colors.HexColor("#61AF64"),
    "sari":        colors.HexColor("#EFB429"),
    "kirmizi":     colors.HexColor("#E24B4A"),
    "metin":       colors.HexColor("#E6EDF3"),
    "metin_sonuk": colors.HexColor("#7D8590"),
}


# ============================================================================
# YARDIMCILAR
# ============================================================================
def _dark_arkaplan(canvas, doc):
    """Her sayfaya dark arkaplan + sayfa numarası."""
    canvas.saveState()
    canvas.setFillColor(P["ana_arka"])
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(P["metin_sonuk"])
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"ATGAS · Sayfa {doc.page}")
    canvas.drawString(1.5 * cm, 1 * cm, "Model Değerlendirme Raporu")
    canvas.restoreState()


def en_son_metrik_dosyasi():
    """En son üretilen ozet_metrikler.json'u bul."""
    aday = sorted(glob.glob(os.path.join(LOG_KOK, "*", "ozet_metrikler.json")))
    if not aday:
        return None
    return aday[-1]


def cm_resim_olustur(cm_data, siniflar, baslik):
    """Confusion matrix matplotlib ile çiz, PNG bytes dön."""
    cm_arr = np.array(cm_data)
    fig, ax = plt.subplots(figsize=(6, 5), dpi=110)
    fig.patch.set_facecolor("#161B22")
    ax.set_facecolor("#0D1117")

    im = ax.imshow(cm_arr, cmap="Blues")
    ax.set_title(baslik, fontsize=11, pad=14, color="#E6EDF3", weight="bold")
    ax.set_xticks(range(len(siniflar)))
    ax.set_xticklabels(siniflar, rotation=35, ha="right", fontsize=9, color="#E6EDF3")
    ax.set_yticks(range(len(siniflar)))
    ax.set_yticklabels(siniflar, fontsize=9, color="#E6EDF3")
    ax.set_xlabel("Tahmin", fontsize=10, color="#7D8590")
    ax.set_ylabel("Gerçek", fontsize=10, color="#7D8590")
    ax.tick_params(colors="#E6EDF3")
    for spine in ax.spines.values():
        spine.set_color("#30363D")

    esik = cm_arr.max() / 2.0 if cm_arr.max() > 0 else 0.5
    for i in range(cm_arr.shape[0]):
        for j in range(cm_arr.shape[1]):
            ax.text(j, i, str(cm_arr[i, j]), ha="center", va="center",
                    color="white" if cm_arr[i, j] > esik else "#0D1117",
                    fontsize=10, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors="#E6EDF3")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="#161B22")
    plt.close(fig)
    buf.seek(0)
    return buf


def _renk_skor(deger):
    """Sayısal değere göre renk seç."""
    if deger >= 0.90:
        return P["yesil"]
    if deger >= 0.70:
        return P["sari"]
    return P["kirmizi"]


# ============================================================================
# RAPOR ÜRETİMİ
# ============================================================================
def rapor_olustur(metrik_yolu=None, cikti_yolu=CIKTI):
    if metrik_yolu is None:
        metrik_yolu = en_son_metrik_dosyasi()
    if not metrik_yolu or not os.path.exists(metrik_yolu):
        raise FileNotFoundError(
            "Metrik dosyası bulunamadı. Önce 'python -m modul_yapay_zeka.degerlendirme' çalıştırın."
        )

    with open(metrik_yolu, "r", encoding="utf-8") as f:
        metrikler = json.load(f)

    os.makedirs(os.path.dirname(cikti_yolu), exist_ok=True)

    # PDF iskeleti
    doc = BaseDocTemplate(
        cikti_yolu, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title="ATGAS Model Değerlendirme Raporu",
        author="ATGAS Ekibi",
    )
    cerceve = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, showBoundary=0)
    doc.addPageTemplates([PageTemplate(id="dark", frames=[cerceve], onPage=_dark_arkaplan)])

    # Stiller
    h_kapak = ParagraphStyle("kapak", fontName=FONT_BOLD, fontSize=32,
                             leading=38, textColor=P["mavi"], alignment=1)
    h_kapak_alt = ParagraphStyle("kapak_alt", fontName=FONT, fontSize=14,
                                 leading=18, textColor=P["metin"], alignment=1)
    h_kapak_kucuk = ParagraphStyle("kapak_k", fontName=FONT, fontSize=10,
                                   leading=14, textColor=P["metin_sonuk"], alignment=1)
    h_baslik1 = ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=18,
                               leading=24, textColor=P["mavi"],
                               spaceBefore=18, spaceAfter=10)
    h_baslik2 = ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=13,
                               leading=18, textColor=P["metin"],
                               spaceBefore=12, spaceAfter=6)
    h_metin = ParagraphStyle("p", fontName=FONT, fontSize=10, leading=14,
                             textColor=P["metin"])
    h_metin_sonuk = ParagraphStyle("ps", fontName=FONT, fontSize=9, leading=12,
                                   textColor=P["metin_sonuk"])
    h_kucuk = ParagraphStyle("kucuk", fontName=FONT, fontSize=8, leading=11,
                             textColor=P["metin_sonuk"])

    icerik = []

    # ============= KAPAK =============
    icerik.append(Spacer(1, 4 * cm))
    icerik.append(Paragraph("ATGAS", h_kapak))
    icerik.append(Paragraph("Akıllı Tıbbi Görüntü Analiz Sistemi", h_kapak_alt))
    icerik.append(Spacer(1, 2 * cm))
    # Mavi yatay ayraç çizgisi — boş paragrafa border ile
    ayrac = Table([[""]], colWidths=[8 * cm], rowHeights=[2])
    ayrac.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P["mavi"]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    icerik.append(ayrac)
    icerik.append(Spacer(1, 0.7 * cm))
    icerik.append(Paragraph("MODEL DEĞERLENDİRME", h_kapak_alt))
    icerik.append(Paragraph(
        "<font color='" + P["metin_sonuk"].hexval() + "'>RAPORU</font>",
        ParagraphStyle("kapak2", fontName=FONT_BOLD, fontSize=22,
                       textColor=P["metin"], alignment=1, leading=28),
    ))
    icerik.append(Spacer(1, 4 * cm))
    icerik.append(Paragraph(
        f"Eğitim Metriklerinin İzlenmesi ve TensorBoard ile Görselleştirilmesi",
        h_kapak_kucuk,
    ))
    icerik.append(Spacer(1, 0.5 * cm))
    icerik.append(Paragraph(
        f"Hazırlanma Tarihi: {datetime.now().strftime('%d.%m.%Y · %H:%M')}",
        h_kapak_kucuk,
    ))
    icerik.append(Paragraph(
        f"Hazırlayan: ATGAS Ekibi · Cuma Doğan",
        h_kapak_kucuk,
    ))
    icerik.append(PageBreak())

    # ============= 1. GÖREV TANIMI =============
    icerik.append(Paragraph("1. Görev Tanımı", h_baslik1))
    icerik.append(Paragraph(
        "Bu rapor, ATGAS projesi kapsamında geliştirilen 5 farklı yapay zeka modelinin "
        "test seti üzerinde değerlendirilmesi sürecini ve elde edilen performans "
        "metriklerini belgelemektedir. Görev kapsamında:",
        h_metin,
    ))
    icerik.append(Spacer(1, 0.3 * cm))
    for madde in [
        "Model eğitim sürecinde kullanılan metriklerin (doğruluk, kayıp vb.) düzenli olarak izlenmesi",
        "Bu metriklerin kalıcı olarak kaydedilmesi (JSON + TensorBoard event log)",
        "TensorBoard ile interaktif görselleştirme",
        "Confusion matrix ve sınıf bazlı detay analiz",
    ]:
        icerik.append(Paragraph(f"• {madde}", h_metin))

    # ============= 2. YÖNTEM =============
    icerik.append(Paragraph("2. Yöntem", h_baslik1))
    yontem_tablo = Table(
        [
            ["Bileşen", "Kullanım"],
            ["Framework", "TensorFlow 2.21 / Keras"],
            ["Model Mimarisi", "EfficientNetV2-M (transfer learning)"],
            ["Metrik Hesaplama", "scikit-learn (classification_report, confusion_matrix, roc_auc_score)"],
            ["Görselleştirme", "TensorBoard 2.20 (Scalars, Images, Text sekmeleri)"],
            ["Görüntü Boyutu", "384 × 384 piksel (3 kanal)"],
            ["Batch Boyutu", "8"],
        ],
        colWidths=[5 * cm, 12 * cm],
    )
    yontem_tablo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P["mavi"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("BACKGROUND", (0, 1), (-1, -1), P["panel"]),
        ("TEXTCOLOR",  (0, 1), (0, -1), P["metin_sonuk"]),
        ("TEXTCOLOR",  (1, 1), (1, -1), P["metin"]),
        ("FONTNAME",   (0, 1), (-1, -1), FONT),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    icerik.append(yontem_tablo)
    icerik.append(Spacer(1, 0.3 * cm))
    icerik.append(Paragraph("<b>Çalıştırma Komutu:</b>", h_metin))
    icerik.append(Paragraph(
        "<font face='Courier' color='" + P["yesil"].hexval() + "'>"
        "python -m modul_yapay_zeka.degerlendirme<br/>"
        "tensorboard --logdir modul_yapay_zeka/logs"
        "</font>",
        h_metin,
    ))

    # ============= 3. ÖZET METRİK TABLOSU =============
    icerik.append(Paragraph("3. Özet Metrikler", h_baslik1))
    icerik.append(Paragraph(
        "Tüm uzman modellerin test seti üzerindeki performans metrikleri:",
        h_metin_sonuk,
    ))
    icerik.append(Spacer(1, 0.3 * cm))

    ozet_satirlar = [["Model", "Test", "Accuracy", "Macro F1", "Macro Prec.", "Macro Rec.", "AUC"]]
    toplam_test = 0
    for kod, m in metrikler.items():
        toplam_test += m["test_ornek_sayisi"]
        auc_str = f"{m['auc']:.3f}" if m["auc"] is not None else "—"
        ozet_satirlar.append([
            kod,
            str(m["test_ornek_sayisi"]),
            f"{m['accuracy']:.3f}",
            f"{m['macro_f1']:.3f}",
            f"{m['macro_precision']:.3f}",
            f"{m['macro_recall']:.3f}",
            auc_str,
        ])
    # Toplam satır
    ozet_satirlar.append(["TOPLAM", str(toplam_test), "", "", "", "", ""])

    ozet_tablo = Table(ozet_satirlar, colWidths=[3.2 * cm, 1.5 * cm, 2.2 * cm, 2.2 * cm,
                                                  2.5 * cm, 2.4 * cm, 2 * cm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), P["mavi"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("BACKGROUND", (0, 1), (-1, -2), P["panel"]),
        ("BACKGROUND", (0, -1), (-1, -1), P["yuzey"]),
        ("FONTNAME",   (0, -1), (-1, -1), FONT_BOLD),
        ("TEXTCOLOR",  (0, 1), (-1, -1), P["metin"]),
        ("FONTNAME",   (0, 1), (-1, -2), FONT),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",      (0, 0), (0, -1),  "LEFT"),
        ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
    ]
    # Renk kodlu accuracy / F1
    for i, (kod, m) in enumerate(metrikler.items(), start=1):
        renk = _renk_skor(m["accuracy"])
        style.append(("TEXTCOLOR", (2, i), (3, i), renk))
        style.append(("FONTNAME",  (2, i), (3, i), FONT_BOLD))
    ozet_tablo.setStyle(TableStyle(style))
    icerik.append(ozet_tablo)

    # ============= 4. MODEL DETAYLARI =============
    icerik.append(PageBreak())
    icerik.append(Paragraph("4. Model Bazlı Detaylı Analiz", h_baslik1))
    icerik.append(Paragraph(
        "Her bir uzman model için confusion matrix, sınıf bazlı metrikler ve klinik yorum:",
        h_metin_sonuk,
    ))

    for idx, (kod, m) in enumerate(metrikler.items()):
        if idx > 0:
            icerik.append(PageBreak())

        # Model başlığı + özet rozet
        renk = _renk_skor(m["accuracy"])
        icerik.append(Spacer(1, 0.3 * cm))
        icerik.append(Paragraph(
            f"4.{idx + 1}. {m['isim']}",
            h_baslik2,
        ))
        icerik.append(Paragraph(
            f"<font color='{P['metin_sonuk'].hexval()}'>Kod:</font> "
            f"<font color='{P['mavi'].hexval()}'><b>{kod}</b></font> &nbsp;|&nbsp; "
            f"<font color='{P['metin_sonuk'].hexval()}'>Sınıf sayısı:</font> "
            f"<b>{len(m['siniflar'])}</b> &nbsp;|&nbsp; "
            f"<font color='{P['metin_sonuk'].hexval()}'>Test örneği:</font> "
            f"<b>{m['test_ornek_sayisi']}</b>",
            h_metin,
        ))
        icerik.append(Spacer(1, 0.2 * cm))

        # 4 metrik bilgi kutusu
        auc_str = f"{m['auc']:.3f}" if m["auc"] is not None else "—"
        metrik_kutu_satir = [
            [
                Paragraph(f"<font size=8 color='{P['metin_sonuk'].hexval()}'>ACCURACY</font><br/>"
                          f"<font size=18 color='{renk.hexval()}'><b>{m['accuracy']:.3f}</b></font>",
                          h_metin),
                Paragraph(f"<font size=8 color='{P['metin_sonuk'].hexval()}'>MACRO F1</font><br/>"
                          f"<font size=18 color='{_renk_skor(m['macro_f1']).hexval()}'><b>{m['macro_f1']:.3f}</b></font>",
                          h_metin),
                Paragraph(f"<font size=8 color='{P['metin_sonuk'].hexval()}'>MACRO REC.</font><br/>"
                          f"<font size=18 color='{_renk_skor(m['macro_recall']).hexval()}'><b>{m['macro_recall']:.3f}</b></font>",
                          h_metin),
                Paragraph(f"<font size=8 color='{P['metin_sonuk'].hexval()}'>AUC</font><br/>"
                          f"<font size=18 color='{P['metin'].hexval()}'><b>{auc_str}</b></font>",
                          h_metin),
            ]
        ]
        metrik_kutu = Table(metrik_kutu_satir, colWidths=[4.25 * cm] * 4)
        metrik_kutu.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), P["panel"]),
            ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
            ("INNERGRID",  (0, 0), (-1, -1), 0.5, P["kenarlik"]),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ]))
        icerik.append(metrik_kutu)
        icerik.append(Spacer(1, 0.3 * cm))

        # Confusion matrix görseli
        icerik.append(Paragraph(
            f"<font color='{P['mavi'].hexval()}'>● Confusion Matrix</font>",
            h_metin,
        ))
        cm_buf = cm_resim_olustur(m["confusion_matrix"], m["siniflar"], m["isim"])
        icerik.append(Spacer(1, 0.1 * cm))
        try:
            icerik.append(Image(cm_buf, width=14 * cm, height=11 * cm, kind="proportional"))
        except Exception:
            icerik.append(Paragraph("<i>Görsel oluşturulamadı</i>", h_kucuk))

        icerik.append(Spacer(1, 0.3 * cm))

        # Per-class metrik tablosu
        icerik.append(Paragraph(
            f"<font color='{P['mavi'].hexval()}'>● Sınıf Bazlı Metrikler</font>",
            h_metin,
        ))
        pc_satirlar = [["Sınıf", "Precision", "Recall", "F1-Score", "Support"]]
        for sinif in m["siniflar"]:
            pc = m["per_class"].get(sinif, {})
            pc_satirlar.append([
                sinif,
                f"{pc.get('precision', 0):.3f}",
                f"{pc.get('recall', 0):.3f}",
                f"{pc.get('f1', 0):.3f}",
                str(pc.get("support", 0)),
            ])
        pc_tablo = Table(pc_satirlar, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm, 2.5 * cm])
        pc_tablo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), P["mavi"]),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
            ("BACKGROUND", (0, 1), (-1, -1), P["panel"]),
            ("TEXTCOLOR",  (0, 1), (-1, -1), P["metin"]),
            ("FONTNAME",   (0, 1), (-1, -1), FONT),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
            ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
            ("INNERGRID",  (0, 0), (-1, -1), 0.25, P["kenarlik"]),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]))
        icerik.append(pc_tablo)

    # ============= 5. SONUÇ ve YORUM =============
    icerik.append(PageBreak())
    icerik.append(Paragraph("5. Sonuç ve Yorum", h_baslik1))

    basarili = [k for k, m in metrikler.items() if m["accuracy"] >= 0.90]
    iyilestirme = [k for k, m in metrikler.items() if m["accuracy"] < 0.90]

    icerik.append(Paragraph("<b>Genel Performans</b>", h_baslik2))
    icerik.append(Paragraph(
        f"Toplam {len(metrikler)} uzman model {toplam_test} test örneği üzerinde değerlendirildi. "
        f"<font color='{P['yesil'].hexval()}'><b>{len(basarili)} model</b></font> "
        f"%90 ve üzeri doğrulukla başarılı bulunmuş; "
        f"<font color='{P['sari'].hexval()}'><b>{len(iyilestirme)} model</b></font> "
        f"iyileştirme alanı tespit edilmiştir.",
        h_metin,
    ))
    icerik.append(Spacer(1, 0.3 * cm))

    icerik.append(Paragraph("<b>Başarılı Modeller</b>", h_baslik2))
    for kod in basarili:
        m = metrikler[kod]
        icerik.append(Paragraph(
            f"• <b>{kod}</b> ({m['isim']}): "
            f"Accuracy <font color='{P['yesil'].hexval()}'>%{m['accuracy']*100:.1f}</font>, "
            f"F1 {m['macro_f1']:.3f}"
            + (f", AUC {m['auc']:.3f}" if m['auc'] is not None else ""),
            h_metin,
        ))

    if iyilestirme:
        icerik.append(Spacer(1, 0.3 * cm))
        icerik.append(Paragraph("<b>İyileştirme Alanı</b>", h_baslik2))
        for kod in iyilestirme:
            m = metrikler[kod]
            cm_arr = np.array(m["confusion_matrix"])
            # En çok karışan sınıfları bul
            karisik = []
            for i in range(cm_arr.shape[0]):
                for j in range(cm_arr.shape[1]):
                    if i != j and cm_arr[i, j] > 0:
                        karisik.append((m["siniflar"][i], m["siniflar"][j], int(cm_arr[i, j])))
            karisik.sort(key=lambda x: -x[2])
            sik_karisan = ", ".join([f"{a}↔{b} ({n})" for a, b, n in karisik[:3]])
            icerik.append(Paragraph(
                f"• <b>{kod}</b> ({m['isim']}): "
                f"Accuracy <font color='{P['sari'].hexval()}'>%{m['accuracy']*100:.1f}</font>, "
                f"F1 {m['macro_f1']:.3f}",
                h_metin,
            ))
            if sik_karisan:
                icerik.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;<font color='{P['metin_sonuk'].hexval()}' size=9>"
                    f"En çok karışan: {sik_karisan}</font>",
                    h_metin,
                ))

    icerik.append(Spacer(1, 0.4 * cm))
    icerik.append(Paragraph("<b>TensorBoard ile Görselleştirme</b>", h_baslik2))
    icerik.append(Paragraph(
        "Tüm metrikler TensorBoard formatında loglanmaktadır. Loglar üç ayrı sekmede "
        "interaktif olarak incelenebilir:",
        h_metin,
    ))
    tb_tablo = Table(
        [
            ["Sekme", "İçerik"],
            ["Scalars", "71 metrik (accuracy, AUC, macro F1/Precision/Recall, per-class F1)"],
            ["Images",  "5 confusion matrix (renkli ısı haritası)"],
            ["Text",    "Her model için scikit-learn classification report"],
        ],
        colWidths=[3 * cm, 14 * cm],
    )
    tb_tablo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P["mavi"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("BACKGROUND", (0, 1), (-1, -1), P["panel"]),
        ("TEXTCOLOR",  (0, 1), (-1, -1), P["metin"]),
        ("FONTNAME",   (0, 1), (-1, -1), FONT),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    icerik.append(tb_tablo)
    icerik.append(Spacer(1, 0.3 * cm))
    icerik.append(Paragraph(
        f"<b>TensorBoard erişim adresi:</b> "
        f"<font color='{P['mavi'].hexval()}'>http://localhost:6006</font>",
        h_metin,
    ))

    icerik.append(Spacer(1, 0.5 * cm))
    icerik.append(Paragraph("<b>Çıktı Dosyaları</b>", h_baslik2))
    cikti_tablo = Table(
        [
            ["Dosya", "Açıklama"],
            ["modul_yapay_zeka/logs/<tarih>/", "TensorBoard event dosyaları"],
            ["modul_yapay_zeka/logs/<tarih>/ozet_metrikler.json", "Yapısal metrik özeti (JSON)"],
            ["docs/Model_Degerlendirme_Raporu.pdf", "Bu rapor"],
        ],
        colWidths=[8 * cm, 9 * cm],
    )
    cikti_tablo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P["yuzey"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), P["metin"]),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("BACKGROUND", (0, 1), (-1, -1), P["panel"]),
        ("TEXTCOLOR",  (0, 1), (-1, -1), P["metin_sonuk"]),
        ("FONTNAME",   (0, 1), (-1, -1), FONT),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("BOX",        (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    icerik.append(cikti_tablo)

    icerik.append(Spacer(1, 1 * cm))
    icerik.append(Paragraph(
        f"<font color='{P['metin_sonuk'].hexval()}'>"
        f"© {datetime.now().year} ATGAS Ekibi · Akıllı Tıbbi Görüntü Analiz Sistemi · "
        f"Cuma Doğan, Nihal Eylül İl, Ozan Diyar Ay, Esmanur Ulu, Elif İkra Çakmak"
        f"</font>",
        h_kucuk,
    ))

    doc.build(icerik)
    return cikti_yolu


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print(" ATGAS — Model Değerlendirme Raporu (PDF) Üretici")
    print("=" * 70)

    metrik = en_son_metrik_dosyasi()
    if not metrik:
        print("\n❌ Henüz metrik verisi yok. Önce şu komutu çalıştırın:")
        print("   python -m modul_yapay_zeka.degerlendirme")
        sys.exit(1)

    print(f"\n📂 Metrik kaynak: {metrik}")
    yol = rapor_olustur(metrik_yolu=metrik)
    boyut_kb = os.path.getsize(yol) / 1024
    print(f"\n✅ PDF üretildi: {yol}")
    print(f"   Boyut: {boyut_kb:.0f} KB")
    print(f"   Sayfa: ~7-10 (kapak + 5 model bölümü + sonuç)")


if __name__ == "__main__":
    main()
