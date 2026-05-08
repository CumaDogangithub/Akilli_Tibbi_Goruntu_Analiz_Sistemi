"""
ATGAS PDF Rapor Üretici (DARK TEMA + TÜRKÇE FONT)
- Karanlık zemin (#0D1117) — UI'la birebir uyumlu
- Türkçe karakter desteği (Windows Arial TTF kayıtlı)
- KVKK: TC ve isim kısmen maskelenir
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, Image,
)
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ANA_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAPOR_KLASORU = os.path.join(ANA_DIZIN, "raporlar")

# ============================================================================
# TÜRKÇE FONT KAYDI
# ============================================================================
def _font_kaydet():
    """Windows Arial veya yedek bir Unicode TTF kaydet. Başarısızsa Helvetica."""
    adaylar = [
        ("ATGAS",      "C:/Windows/Fonts/arial.ttf"),
        ("ATGAS-Bold", "C:/Windows/Fonts/arialbd.ttf"),
        ("ATGAS-Italic", "C:/Windows/Fonts/ariali.ttf"),
    ]
    yedek = [
        ("ATGAS",      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("ATGAS-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    try:
        for ad, yol in adaylar:
            if os.path.exists(yol):
                pdfmetrics.registerFont(TTFont(ad, yol))
        # En azından ATGAS ve ATGAS-Bold yüklendiyse
        if "ATGAS" in pdfmetrics.getRegisteredFontNames() and "ATGAS-Bold" in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFontFamily(
                "ATGAS",
                normal="ATGAS",
                bold="ATGAS-Bold",
                italic="ATGAS-Italic" if "ATGAS-Italic" in pdfmetrics.getRegisteredFontNames() else "ATGAS",
                boldItalic="ATGAS-Bold",
            )
            return "ATGAS"
        # Linux yedeği dene
        for ad, yol in yedek:
            if os.path.exists(yol):
                pdfmetrics.registerFont(TTFont(ad, yol))
        if "ATGAS" in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFontFamily("ATGAS", normal="ATGAS", bold="ATGAS-Bold")
            return "ATGAS"
    except Exception:
        pass
    return "Helvetica"


FONT = _font_kaydet()
FONT_BOLD = "ATGAS-Bold" if FONT == "ATGAS" else "Helvetica-Bold"

# ============================================================================
# RENK PALETİ (UI ile birebir)
# ============================================================================
P = {
    "ana_arka":   colors.HexColor("#0D1117"),
    "panel":      colors.HexColor("#161B22"),
    "yuzey":      colors.HexColor("#21262D"),
    "kenarlik":   colors.HexColor("#30363D"),
    "mavi":       colors.HexColor("#1C6EF2"),
    "yesil":      colors.HexColor("#61AF64"),
    "sari":       colors.HexColor("#EFB429"),
    "kirmizi":    colors.HexColor("#E24B4A"),
    "metin":      colors.HexColor("#E6EDF3"),
    "metin_sonuk": colors.HexColor("#7D8590"),
}


# ============================================================================
# YARDIMCILAR (KVKK)
# ============================================================================
def tc_maskele(tc: str) -> str:
    if not tc or len(tc) < 5:
        return "***"
    return f"{tc[:3]}{'*' * (len(tc) - 5)}{tc[-2:]}"


def ad_maskele(ad: str) -> str:
    parcalar = (ad or "").strip().split()
    if not parcalar:
        return "***"
    return " ".join(p[:2] + "***" for p in parcalar)


def tarih_maskele(tarih: str) -> str:
    s = str(tarih or "")
    # ISO format YYYY-MM-DD → yıl ilk 4 hanede
    if len(s) >= 4 and s[:4].isdigit():
        return f"**.**.{s[:4]}"
    # GG.AA.YYYY veya GG/AA/YYYY → yıl son 4 hanede
    if len(s) >= 4 and s[-4:].isdigit():
        return f"**.**.{s[-4:]}"
    return "**.**.****"


def seviye_belirle(ham_sinif, dogruluk):
    if ham_sinif == "Normal":
        return "Temiz", P["yesil"]
    if dogruluk >= 85:
        return "Kritik", P["kirmizi"]
    return "Orta", P["sari"]


# ============================================================================
# DARK ARKA PLAN — Her sayfaya çiziliyor
# ============================================================================
def _dark_arkaplan(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(P["ana_arka"])
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Sayfa numarası
    canvas.setFont(FONT, 8)
    canvas.setFillColor(P["metin_sonuk"])
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"ATGAS · Sayfa {doc.page}")
    canvas.restoreState()


# ============================================================================
# RAPOR ÜRETİCİ
# ============================================================================
def rapor_olustur(rapor_id, veri, cikti_yolu=None):
    if cikti_yolu is None:
        os.makedirs(RAPOR_KLASORU, exist_ok=True)
        cikti_yolu = os.path.join(RAPOR_KLASORU, f"rapor_{rapor_id}.pdf")

    doc = BaseDocTemplate(
        cikti_yolu, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"ATGAS Rapor #{rapor_id}",
        author="ATGAS",
    )
    cerceve = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        showBoundary=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="dark", frames=[cerceve], onPage=_dark_arkaplan)
    ])

    # ----- STİLLER -----
    h_baslik = ParagraphStyle(
        "atgB", fontName=FONT_BOLD, fontSize=24, leading=28,
        textColor=P["mavi"], spaceAfter=2,
    )
    h_alt_baslik = ParagraphStyle(
        "atgA", fontName=FONT, fontSize=9, leading=12,
        textColor=P["metin_sonuk"], spaceAfter=12,
    )
    h_bolum = ParagraphStyle(
        "atgBl", fontName=FONT_BOLD, fontSize=11, leading=14,
        textColor=P["mavi"], spaceBefore=12, spaceAfter=8,
    )
    h_metin = ParagraphStyle(
        "atgM", fontName=FONT, fontSize=10, leading=14,
        textColor=P["metin"],
    )
    h_metin_sonuk = ParagraphStyle(
        "atgMs", fontName=FONT, fontSize=9, leading=12,
        textColor=P["metin_sonuk"],
    )
    h_uyari = ParagraphStyle(
        "atgU", fontName=FONT, fontSize=8, leading=11,
        textColor=P["metin_sonuk"],
    )

    icerik = []

    # ============= ÜST BAŞLIK =============
    durum = veri["analiz"].get("durum", "Taslak")
    durum_renk = P["yesil"] if durum == "Kaydedildi" else P["sari"]

    ust = Table(
        [[
            Paragraph("<b>ATGAS</b>", h_baslik),
            Paragraph(
                f'<para align="right"><font color="{P["metin"].hexval()}" size=11><b>Rapor #{rapor_id}</b></font><br/>'
                f'<font color="{P["metin_sonuk"].hexval()}" size=8>'
                f'{veri["analiz"].get("islem_tarihi", datetime.now().strftime("%d.%m.%Y · %H:%M"))}'
                f'</font><br/>'
                f'<font color="{durum_renk.hexval()}" size=9>● {durum}</font></para>',
                h_metin,
            ),
        ]],
        colWidths=[10 * cm, 7 * cm],
    )
    ust.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    icerik.append(ust)
    icerik.append(Paragraph("Akıllı Tıbbi Görüntü Analiz Sistemi", h_alt_baslik))

    # ============= HASTA + DOKTOR =============
    icerik.append(Paragraph("● HASTA &amp; DOKTOR BİLGİLERİ", h_bolum))
    hasta = veri["hasta"]
    doktor = veri["doktor"]

    bilgi = Table(
        [
            ["Hasta Ad Soyad", ad_maskele(hasta["ad_soyad"]),
             "Doktor Ad Soyad", doktor["ad_soyad"]],
            ["TC Kimlik", tc_maskele(hasta["tc"]),
             "Branş", doktor["brans"]],
            ["Doğum Tarihi", tarih_maskele(hasta["dogum_tarihi"]),
             "E-posta", doktor.get("eposta", "-")],
            ["Protokol No", hasta["protokol_no"],
             "İşlem Tarihi", veri["analiz"].get("islem_tarihi", "-")],
        ],
        colWidths=[3.5 * cm, 5 * cm, 3.5 * cm, 5 * cm],
    )
    bilgi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P["panel"]),
        ("TEXTCOLOR", (0, 0), (0, -1), P["metin_sonuk"]),
        ("TEXTCOLOR", (2, 0), (2, -1), P["metin_sonuk"]),
        ("TEXTCOLOR", (1, 0), (1, -1), P["metin"]),
        ("TEXTCOLOR", (3, 0), (3, -1), P["metin"]),
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTNAME", (1, 0), (1, -1), FONT_BOLD),
        ("FONTNAME", (3, 0), (3, -1), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    icerik.append(bilgi)

    # ============= GÖRÜNTÜ ANALİZİ =============
    icerik.append(Paragraph("● GÖRÜNTÜ ANALİZİ", h_bolum))

    orijinal = veri["analiz"].get("goruntu_dosya_yolu")
    isaretli = veri["analiz"].get("isaretli_goruntu_yolu")

    def _resim(yol):
        if yol and os.path.exists(yol):
            try:
                return Image(yol, width=8 * cm, height=8 * cm, kind="proportional")
            except Exception:
                pass
        return Paragraph(
            f"<font color='{P['metin_sonuk'].hexval()}'><i>Görüntü mevcut değil</i></font>",
            h_metin,
        )

    gor_baslik_stil = ParagraphStyle(
        "gB", parent=h_metin, fontName=FONT_BOLD,
        fontSize=9, textColor=P["metin"], alignment=1,
    )
    gor_baslik_kirmizi = ParagraphStyle(
        "gBk", parent=h_metin, fontName=FONT_BOLD,
        fontSize=9, textColor=P["kirmizi"], alignment=1,
    )

    gor_tablo = Table(
        [
            [Paragraph("● ORİJİNAL GÖRÜNTÜ", gor_baslik_stil),
             Paragraph("● TENSORFLOW ANALİZ ÇIKTISI", gor_baslik_kirmizi)],
            [_resim(orijinal), _resim(isaretli)],
        ],
        colWidths=[8.5 * cm, 8.5 * cm],
        rowHeights=[0.8 * cm, 8.5 * cm],
    )
    gor_tablo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P["yuzey"]),
        ("BACKGROUND", (0, 1), (-1, 1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
    ]))
    icerik.append(gor_tablo)

    # ============= TF TAHMİN + DOĞRULUK (yeniden tasarlanmış kartlar) =============
    analiz = veri["analiz"]
    seviye, sev_renk = seviye_belirle(
        analiz.get("ham_sinif", "Normal"),
        float(analiz.get("dogruluk_orani", 0)),
    )
    tahmin = analiz.get("tf_tahmin_sonucu", "-")
    dogruluk = float(analiz.get("dogruluk_orani", 0))
    ham_sinif = analiz.get("ham_sinif", "Normal")
    guven = "Yüksek Güven" if dogruluk >= 90 else ("Orta Güven" if dogruluk >= 70 else "Düşük Güven")

    # Anlamlı durum etiketi (TF tahmin altında)
    if ham_sinif == "Normal":
        durum_etiketi = "Patolojik bulguya rastlanmadı"
    elif dogruluk >= 85:
        durum_etiketi = "Anomali tespit edildi — uzman değerlendirmesi gerekir"
    else:
        durum_etiketi = "Şüpheli bulgu — ek tetkik ve uzman onayı önerilir"

    # Yardımcı: doğruluk için zarif yuvarlatılmış ilerleme barı
    def _bar(yuzde, renk, genislik_cm=7.0):
        G = genislik_cm * cm
        H = 0.22 * cm
        d = Drawing(G, H)
        # Arka şerit (yuvarlatılmış)
        d.add(Rect(0, 0, G, H,
                   fillColor=P["yuzey"], strokeColor=None,
                   rx=H / 2, ry=H / 2))
        dolu_g = G * max(0.0, min(yuzde, 100.0)) / 100.0
        if dolu_g > 0:
            d.add(Rect(0, 0, dolu_g, H,
                       fillColor=renk, strokeColor=None,
                       rx=H / 2, ry=H / 2))
        return d

    # Büyük rakam/başlık için leading'leri uyarlanmış stiller (descender çakışmasını önler)
    h_etiket = ParagraphStyle(
        "etiket", parent=h_metin, fontName=FONT_BOLD,
        fontSize=8, leading=10, textColor=P["metin_sonuk"],
        spaceAfter=0,
    )
    h_buyuk_tahmin = ParagraphStyle(
        "btahmin", parent=h_metin, fontName=FONT_BOLD,
        fontSize=22, leading=26, textColor=sev_renk,
        spaceAfter=0,
    )
    h_buyuk_yuzde = ParagraphStyle(
        "byuzde", parent=h_metin, fontName=FONT_BOLD,
        fontSize=26, leading=30, textColor=P["metin"],
        spaceAfter=0,
    )
    h_alt_etiket = ParagraphStyle(
        "alte", parent=h_metin,
        fontSize=9, leading=12, textColor=P["metin"],
    )

    # ----- SOL: TF Tahmin Sonucu -----
    tf_inner = Table(
        [
            [Paragraph("TF TAHMİN SONUCU", h_etiket)],
            [Paragraph(tahmin, h_buyuk_tahmin)],
            [Paragraph(
                f"<font color='{sev_renk.hexval()}'>● </font>{durum_etiketi}",
                h_alt_etiket,
            )],
        ],
        colWidths=[7.5 * cm],
    )
    tf_inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 12),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 12),
        ("TOPPADDING", (0, 2), (0, 2), 0),
        ("BOTTOMPADDING", (0, 2), (0, 2), 0),
    ]))

    # ----- SAĞ: Doğruluk Oranı -----
    dog_inner = Table(
        [
            [Paragraph("DOĞRULUK ORANI", h_etiket)],
            [Paragraph(f"%{dogruluk:.2f}", h_buyuk_yuzde)],
            [_bar(dogruluk, sev_renk)],
            [Paragraph(
                f"<font color='{sev_renk.hexval()}'><b>● {guven}</b></font>",
                h_alt_etiket,
            )],
        ],
        colWidths=[7.5 * cm],
    )
    dog_inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 12),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 14),  # büyük rakam altına nefes alanı
        ("TOPPADDING", (0, 2), (0, 2), 0),
        ("BOTTOMPADDING", (0, 2), (0, 2), 10),
        ("TOPPADDING", (0, 3), (0, 3), 0),
        ("BOTTOMPADDING", (0, 3), (0, 3), 0),
    ]))

    # Outer kartlar — yan yana, sol kenarda renkli vurgu şeridi
    sonuc = Table(
        [[tf_inner, dog_inner]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    sonuc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P["panel"]),
        ("BOX", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("LINEAFTER", (0, 0), (0, 0), 0.5, P["kenarlik"]),  # iki kart arası ayraç
        ("LINEBEFORE", (0, 0), (0, 0), 4, sev_renk),         # SOL kart sol şerit (sınıfa göre)
        ("LINEBEFORE", (1, 0), (1, 0), 4, P["mavi"]),        # SAĞ kart sol şerit (mavi)
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    icerik.append(Spacer(1, 0.3 * cm))
    icerik.append(sonuc)

    # ============= TEKNİK DETAYLAR =============
    icerik.append(Paragraph("● TEKNİK DETAYLAR", h_bolum))
    teknik = Table(
        [
            ["Rapor ID", f"analiz_raporlari.id → {rapor_id}"],
            ["Tarama Tipi", analiz.get("tarama_tipi", "-")],
            ["TF Tahmin Sonucu", tahmin],
            ["Doğruluk Oranı", f"{dogruluk:.2f}"],
            ["Seviye", seviye],
            ["Durum", durum],
            ["Protokol No", hasta["protokol_no"]],
            ["İşlem Tarihi", analiz.get("islem_tarihi", "-")],
        ],
        colWidths=[5 * cm, 12 * cm],
    )
    teknik.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P["panel"]),
        ("TEXTCOLOR", (0, 0), (0, -1), P["metin_sonuk"]),
        ("TEXTCOLOR", (1, 0), (1, -1), P["metin"]),
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTNAME", (1, 0), (1, -1), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, P["kenarlik"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    icerik.append(teknik)

    # ============= DOKTOR NOTU =============
    icerik.append(Paragraph("● DOKTOR NOTU", h_bolum))
    yz_yorum = analiz.get("yapay_zeka_yorumu") or "-"
    dr_notu = analiz.get("doktor_notu") or "<i>(Doktor notu girilmedi.)</i>"

    not_kart = Table(
        [
            [Paragraph(
                f"<font color='{P['mavi'].hexval()}'><b>YZ Yorumu:</b></font> "
                f"<font color='{P['metin'].hexval()}'>{yz_yorum}</font>",
                h_metin,
            )],
            [Paragraph(
                f"<font color='{P['mavi'].hexval()}'><b>Doktor Yorumu:</b></font> "
                f"<font color='{P['metin'].hexval()}'>{dr_notu}</font>",
                h_metin,
            )],
            [Paragraph(
                f"<font color='{P['metin_sonuk'].hexval()}' size=8>"
                f"— {doktor['ad_soyad']} · {doktor['brans']} · "
                f"{datetime.now().strftime('%d.%m.%Y')}</font>",
                h_metin,
            )],
        ],
        colWidths=[17 * cm],
    )
    not_kart.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P["panel"]),
        ("BOX", (0, 0), (-1, -1), 0.5, P["kenarlik"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    icerik.append(not_kart)

    # ============= KVKK / YASAL =============
    icerik.append(Spacer(1, 0.4 * cm))
    yasal = Table(
        [[Paragraph(
            "<font size=8 color='" + P["sari"].hexval() + "'>(!) </font>"
            "<font size=8 color='" + P["metin_sonuk"].hexval() + "'>"
            "Bu rapor ATGAS Yapay Zeka Sistemi (TensorFlow / Keras) tarafından "
            "otomatik olarak üretilmiştir ve kesin tanı niteliği taşımaz. Klinik "
            "değerlendirme ve uzman doktor onayı ile birlikte yorumlanmalıdır. "
            "Hasta bilgileri KVKK uyumu için kısmen maskelenmiştir; tam bilgilere "
            "yalnızca yetkili sağlık personeli sistem üzerinden erişebilir."
            "</font>",
            h_metin,
        )]],
        colWidths=[17 * cm],
    )
    yasal.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a1410")),
        ("BOX", (0, 0), (-1, -1), 0.5, P["sari"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    icerik.append(yasal)

    icerik.append(Spacer(1, 0.3 * cm))
    icerik.append(Paragraph(
        f"<font color='{P['mavi'].hexval()}'>● TensorFlow / Keras · EfficientNetV2-M</font> "
        f"&nbsp;&nbsp;&nbsp; "
        f"<font color='{P['metin_sonuk'].hexval()}'>"
        f"ATGAS v1.0 · Rapor #{rapor_id} · Protokol: {hasta['protokol_no']} · "
        f"© {datetime.now().year} ATGAS"
        f"</font>",
        h_uyari,
    ))

    doc.build(icerik)
    return cikti_yolu
