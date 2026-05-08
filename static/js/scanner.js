/* ATGAS — Yeni Tarama: Hiyerarşik tip seçimi, drop zone, aşamalı loader */

(function () {
  const dropZone = document.getElementById("drop-zone");
  if (!dropZone) return;

  const fileInput = document.getElementById("goruntu-input");
  const seciliDosyaEt = document.getElementById("secili-dosya");
  const onizleme = document.getElementById("onizleme");
  const analizBtn = document.getElementById("analiz-btn");
  const form = document.getElementById("tarama-form");
  const uzmanInput = document.getElementById("uzman_kodu");
  const dosyaKaldirBtn = document.getElementById("dosya-kaldir-btn");

  const anaTipKartlari = document.querySelectorAll(".ana-tip-kart");
  const altUzmanKartlari = document.querySelectorAll(".alt-uzman-kart");
  const altCt = document.getElementById("alt-ct");
  const altMri = document.getElementById("alt-mri");

  // Takvimde bugünden sonraki günlerin seçilmesini engelle
  const dtInputNode = document.getElementById("hasta_dogum_tarihi");
  if (dtInputNode) {
    dtInputNode.max = new Date().toISOString().split("T")[0]; // YYYY-MM-DD
  }

  // ============================================================
  // 1) HIYERARŞIK TIP SEÇIMI — Ana tip → (CT/MRI ise) alt tip
  // ============================================================
  anaTipKartlari.forEach((kart) => {
    kart.addEventListener("click", () => {
      anaTipKartlari.forEach((k) => k.classList.remove("aktif"));
      kart.classList.add("aktif");
      altUzmanKartlari.forEach((k) => k.classList.remove("aktif"));

      const anaTip = kart.dataset.anaTip;
      altCt.style.display = anaTip === "ct" ? "block" : "none";
      altMri.style.display = anaTip === "mri" ? "block" : "none";

      if (anaTip === "xray") {
        // X-Ray'in alt seçeneği yok → uzman direkt belirleniyor
        uzmanInput.value = kart.dataset.uzman;
      } else {
        // CT/MRI seçildi → alt seçim bekleniyor
        uzmanInput.value = "";
      }
      durumGuncelle();
    });
  });

  altUzmanKartlari.forEach((kart) => {
    kart.addEventListener("click", () => {
      // Sadece aynı grup içindeki diğerlerini temizle
      const grup = kart.closest(".alt-kategori");
      grup.querySelectorAll(".alt-uzman-kart").forEach((k) => k.classList.remove("aktif"));
      kart.classList.add("aktif");
      uzmanInput.value = kart.dataset.uzman;
      durumGuncelle();
    });
  });

  // ============================================================
  // 2) DROP ZONE — TEK DİALOG (label + sürükleme)
  // ============================================================
  // NOT: drop-zone bir <label for="goruntu-input"> olduğu için tıklayınca
  // tarayıcı otomatik dosya dialogunu açar. Manuel "click" çağrısına gerek YOK.
  ["dragover", "dragenter"].forEach((ev) =>
    dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    })
  );
  ["dragleave"].forEach((ev) =>
    dropZone.addEventListener(ev, () => dropZone.classList.remove("dragover"))
  );
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      dosyaSecildi();
    }
  });
  fileInput.addEventListener("change", dosyaSecildi);

  function arayuzuSifirla() {
    form.reset();
    fileInput.value = "";
    seciliDosyaEt.textContent = "Sürükleyip bırakın veya tıklayın";
    seciliDosyaEt.style.color = "";
    if (onizleme) {
      onizleme.src = "";
      onizleme.style.display = "none";
    }
    dropZone.classList.remove("hata");
    if (dosyaKaldirBtn) dosyaKaldirBtn.style.display = "none";
    const overlayEl = document.getElementById("analiz-overlay");
    if (overlayEl) overlayEl.style.display = "none";
    durumGuncelle();
  }

  if (dosyaKaldirBtn) {
    dosyaKaldirBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation(); // Tıklamanın drop-zone'a gidip dosya penceresini tekrar açmasını engeller

      arayuzuSifirla();

      // Sunucu tarafında varsa bekleyen analizi ve dosyaları temizle
      try {
        await fetch("/api/iptal", { method: "POST" });
      } catch (err) {
        console.error("Temizleme hatası:", err);
      }
    });
  }

  function dosyaSecildi() {
    const dosya = fileInput.files[0];
    if (!dosya) {
      if (dosyaKaldirBtn) dosyaKaldirBtn.style.display = "none";
      return;
    }

    // Tarayıcı tarafında sadece açıkça yasak olanları reddet (DICOM uzantısız da olabilir,
    // sunucu magic bytes ile son kararı verir).
    const yasakli = [".exe", ".sh", ".bat", ".js", ".html", ".php"];
    const uzanti = "." + dosya.name.split(".").pop().toLowerCase();
    if (yasakli.includes(uzanti)) {
      dropZone.classList.add("hata");
      seciliDosyaEt.textContent = "Bu tip dosya yüklenemez!";
      seciliDosyaEt.style.color = "var(--kirmizi)";
      if (dosyaKaldirBtn) dosyaKaldirBtn.style.display = "inline-block";
      return;
    }
    if (dosya.size > 50 * 1024 * 1024) {
      dropZone.classList.add("hata");
      seciliDosyaEt.textContent = "Dosya çok büyük (maks 50 MB)";
      if (dosyaKaldirBtn) dosyaKaldirBtn.style.display = "inline-block";
      return;
    }
    dropZone.classList.remove("hata");
    seciliDosyaEt.textContent = `✓ ${dosya.name} (${(dosya.size / 1024).toFixed(0)} KB)`;
    seciliDosyaEt.style.color = "var(--yesil)";
    if (dosyaKaldirBtn) dosyaKaldirBtn.style.display = "inline-block";

    // DICOM browser'da render edilemez → önizleme sadece resim mime'larında
    if (onizleme && dosya.type.startsWith("image/")) {
      const okuyucu = new FileReader();
      okuyucu.onload = (e) => {
        onizleme.src = e.target.result;
        onizleme.style.display = "block";
      };
      okuyucu.readAsDataURL(dosya);
    } else if (onizleme) {
      onizleme.style.display = "none";
    }
    durumGuncelle();
  }

  // ============================================================
  // 3) FORM VALİDASYONU
  // ============================================================
  form.querySelectorAll("input").forEach((inp) => inp.addEventListener("input", durumGuncelle));

  function durumGuncelle() {
    const tcInput = document.getElementById("hasta_tc");
    const tcDeger = tcInput.value.trim();
    if (tcDeger && (tcDeger.length !== 11 || !/^\d+$/.test(tcDeger))) {
      tcInput.style.borderColor = "var(--kirmizi)";
    } else {
      tcInput.style.borderColor = "";
    }

    const gerekli = ["hasta_ad_soyad", "hasta_tc", "hasta_dogum_tarihi", "protokol_no"];
    const tumDoldu = gerekli.every((id) => document.getElementById(id).value.trim());
    const dosyaVar = fileInput.files.length > 0;
    const uzmanVar = !!uzmanInput.value;
    const tcGecerli = tcDeger.length === 11 && /^\d+$/.test(tcDeger);

    analizBtn.disabled = !(tumDoldu && dosyaVar && uzmanVar && tcGecerli);
  }

  // ============================================================
  // 4) AŞAMALI LOADER OVERLAY
  // ============================================================
  const overlay = document.getElementById("analiz-overlay");
  const overlayYuzde = document.getElementById("overlay-yuzde");
  const overlayBar = document.getElementById("overlay-bar");
  const adimlar = document.querySelectorAll("#overlay-adimlar li");

  // Aşamaların görsel zamanlaması (ms). Toplam ~14sn — gerçek analiz biterse erken kapanır.
  const ASAMALAR = [
    { ad: "Görüntü yükleniyor",       sure: 1500 },
    { ad: "CLAHE + gürültü giderme",  sure: 2000 },
    { ad: "Model belleğe yükleniyor", sure: 3000 },
    { ad: "CNN katmanları işleniyor", sure: 4000 },
    { ad: "Grad-CAM ısı haritası",    sure: 2500 },
    { ad: "DB'ye kaydediliyor",       sure: 1000 },
  ];
  let mevcutAdim = 0;
  let zamanlayici = null;
  let analizBitti = false;
  let analizDevamEdiyor = false; // Sayfadan çıkış kontrolü için eklendi

  function loaderBaslat() {
    overlay.style.display = "flex";
    mevcutAdim = 0;
    analizBitti = false;
    analizDevamEdiyor = true;
    adimlar.forEach((li) => li.classList.remove("aktif", "tamam"));
    adimlar[0].classList.add("aktif");
    overlayYuzde.textContent = "0%";
    overlayBar.style.width = "0%";

    let baslangic = Date.now();
    let toplamSure = ASAMALAR.reduce((t, a) => t + a.sure, 0);

    zamanlayici = setInterval(() => {
      const gecen = Date.now() - baslangic;
      let kumulatif = 0;
      let yeniAdim = 0;
      for (let i = 0; i < ASAMALAR.length; i++) {
        kumulatif += ASAMALAR[i].sure;
        if (gecen < kumulatif) { yeniAdim = i; break; }
        yeniAdim = i + 1;
      }
      // Eğer son aşamayı geçtiyse, %95'te bekle (analiz bitene kadar)
      let yuzde = Math.min(95, Math.floor((gecen / toplamSure) * 95));

      if (yeniAdim !== mevcutAdim) {
        for (let i = 0; i < yeniAdim && i < adimlar.length; i++) {
          adimlar[i].classList.remove("aktif");
          adimlar[i].classList.add("tamam");
        }
        if (yeniAdim < adimlar.length) {
          adimlar[yeniAdim].classList.add("aktif");
        }
        mevcutAdim = yeniAdim;
      }
      overlayYuzde.textContent = yuzde + "%";
      overlayBar.style.width = yuzde + "%";

      if (analizBitti) {
        clearInterval(zamanlayici);
      }
    }, 200);
  }

  function loaderBitir(basarili) {
    analizBitti = true;
    analizDevamEdiyor = false;
    clearInterval(zamanlayici);
    if (basarili) {
      adimlar.forEach((li) => {
        li.classList.remove("aktif");
        li.classList.add("tamam");
      });
      overlayYuzde.textContent = "100%";
      overlayBar.style.width = "100%";
      overlayBar.style.background = "var(--yesil)";
    } else {
      overlay.style.display = "none";
    }
  }

  // ============================================================
  // 5) FORM GÖNDER
  // ============================================================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (analizBtn.disabled) return;

    // DOĞUM TARİHİ DOĞRULAMASI
    const dtStr = dtInputNode.value;
    const bugunStr = new Date().toISOString().split("T")[0];
    
    if (dtStr > bugunStr) {
      toast("Doğum tarihi gelecek bir tarih olamaz.", "hata");
      dtInputNode.focus();
      return;
    }
    if (dtStr < "1900-01-01") {
      toast("Mantıksız doğum yılı (1900'den eski olamaz).", "hata");
      dtInputNode.focus();
      return;
    }

    const fd = new FormData(form);
    analizBtn.disabled = true;
    loaderBaslat();

    try {
      const yanit = await fetch("/api/analiz", { method: "POST", body: fd });
      const veri = await yanit.json();
      if (veri.durum === "basarili") {
        loaderBitir(true);
        setTimeout(() => (window.location.href = veri.redirect_url), 600);
      } else {
        loaderBitir(false);
        toast(veri.mesaj || "Analiz hatası", "hata");
        analizBtn.disabled = false;
      }
    } catch (err) {
      loaderBitir(false);
      toast("Sunucu hatası: " + err.message, "hata");
      analizBtn.disabled = false;
    }
  });

  // ============================================================
  // 6) Önceden seçili tip (dashboard'tan gelen ?tip= parametresi)
  // ============================================================
  const onSecili = document.body.dataset.onSecili;
  if (onSecili) {
    // Eğer tam uzman kodu geldiyse (örn "ct_akciger") önce ana tipi tıkla, sonra alt
    if (onSecili === "xray") {
      document.querySelector(`.ana-tip-kart[data-ana-tip="xray"]`)?.click();
    } else if (onSecili.startsWith("ct_")) {
      document.querySelector(`.ana-tip-kart[data-ana-tip="ct"]`)?.click();
      document.querySelector(`.alt-uzman-kart[data-uzman="${onSecili}"]`)?.click();
    } else if (onSecili.startsWith("mri_")) {
      document.querySelector(`.ana-tip-kart[data-ana-tip="mri"]`)?.click();
      document.querySelector(`.alt-uzman-kart[data-uzman="${onSecili}"]`)?.click();
    }
  }

  // ============================================================
  // 7) SAYFADAN ÇIKIŞ KONTROLÜ (Analiz Devam Ederken)
  // ============================================================
  window.addEventListener("pageshow", (e) => {
    // Kullanıcı tarayıcının geri/ileri tuşuyla bu sayfaya dönerse tüm verileri sıfırla
    const geridenMiGeldi = e.persisted || (window.performance && window.performance.getEntriesByType && window.performance.getEntriesByType("navigation")[0]?.type === "back_forward");
    
    if (geridenMiGeldi) {
      analizDevamEdiyor = false;
      arayuzuSifirla();
      navigator.sendBeacon("/api/iptal");
    } else {
      form.reset(); // Normal sayfa yenilemede de form eski verilerini temizle
    }
  });

  window.addEventListener("beforeunload", (e) => {
    if (analizDevamEdiyor) {
      e.preventDefault();
      e.returnValue = "Analiz devam ediyor, sayfadan çıkmak istediğinize emin misiniz?";
      return e.returnValue;
    }
  });

  window.addEventListener("unload", () => {
    if (analizDevamEdiyor) {
      navigator.sendBeacon("/api/iptal"); // Sayfa kapanırken arka planda temizlik isteği atar
    }
  });

  document.addEventListener("click", (e) => {
    if (!analizDevamEdiyor) return;
    const a = e.target.closest("a");
    if (!a) return;
    const href = a.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("javascript:")) return;

    if (!confirm("Analiz devam ediyor, sayfadan çıkmak istediğinize emin misiniz?")) {
      e.preventDefault();
    } else {
      analizDevamEdiyor = false; // Tekrar beforeunload tetiklenmesini engelle
      navigator.sendBeacon("/api/iptal");
    }
  });
})();
