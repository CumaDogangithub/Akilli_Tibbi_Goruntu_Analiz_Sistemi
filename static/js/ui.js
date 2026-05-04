/* ATGAS - Genel UI yardımcıları */

function toast(mesaj, tip = "basarili", sure = 3500) {
  const eski = document.querySelector(".toast");
  if (eski) eski.remove();
  const t = document.createElement("div");
  t.className = "toast " + tip;
  t.innerHTML = `<span>${tip === "hata" ? "✕" : tip === "uyari" ? "⚠" : "✓"}</span><span>${mesaj}</span>`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), sure);
}

function tabloFiltrele(arama, tabloId, secici = ".rozet, td") {
  const tablo = document.getElementById(tabloId);
  if (!tablo) return;
  const sorgu = arama.trim().toLowerCase();
  tablo.querySelectorAll("tbody tr").forEach((tr) => {
    const metin = tr.innerText.toLowerCase();
    tr.style.display = !sorgu || metin.includes(sorgu) ? "" : "none";
  });
}

function cipFiltrele(secilen, grupAdi, tabloId, sutunIndex) {
  const tablo = document.getElementById(tabloId);
  if (!tablo) return;
  const cipler = document.querySelectorAll(`[data-cip-grup="${grupAdi}"]`);
  cipler.forEach((c) => c.classList.toggle("aktif", c.dataset.deger === secilen));

  tablo.querySelectorAll("tbody tr").forEach((tr) => {
    if (secilen === "tumu") {
      tr.style.display = "";
      return;
    }
    const hucre = tr.children[sutunIndex];
    const metin = hucre ? hucre.innerText.trim().toLowerCase() : "";
    tr.style.display = metin.includes(secilen.toLowerCase()) ? "" : "none";
  });
}

async function jsonPOST(url, veri) {
  const yanit = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(veri),
  });
  return await yanit.json();
}

async function jsonDELETE(url) {
  const yanit = await fetch(url, { method: "DELETE" });
  return await yanit.json();
}

/* ============ MOBİL SIDEBAR (HAMBURGER) ============ */
function sidebarToggle() {
  const sb = document.getElementById("sidebar");
  const ov = document.getElementById("sidebar-overlay");
  if (!sb) return;
  const acik = sb.classList.toggle("acik");
  ov?.classList.toggle("acik", acik);
  document.body.style.overflow = acik ? "hidden" : "";
}
function sidebarKapat() {
  document.getElementById("sidebar")?.classList.remove("acik");
  document.getElementById("sidebar-overlay")?.classList.remove("acik");
  document.body.style.overflow = "";
}
// Sidebar içindeki bir linke tıklandığında otomatik kapansın (mobilde)
document.addEventListener("click", (e) => {
  if (window.innerWidth > 768) return;
  const sb = document.getElementById("sidebar");
  if (sb && sb.classList.contains("acik") && e.target.closest("a")) {
    setTimeout(sidebarKapat, 100);
  }
});

/* ============ HEADER DOKTOR DROPDOWN MENÜ ============ */
function doktorMenuToggle(e) {
  e.stopPropagation();
  const dropdown = document.getElementById("doktor-dropdown");
  const btn = document.getElementById("doktor-toggle");
  if (!dropdown || !btn) return;
  const acik = dropdown.classList.toggle("acik");
  btn.classList.toggle("acik", acik);
}

// Sayfa içinde herhangi bir yere tıklanınca dropdown'ı kapat
document.addEventListener("click", (e) => {
  const dropdown = document.getElementById("doktor-dropdown");
  const btn = document.getElementById("doktor-toggle");
  if (!dropdown || !btn) return;
  if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
    dropdown.classList.remove("acik");
    btn.classList.remove("acik");
  }
});

// ESC tuşuyla da kapansın
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.getElementById("doktor-dropdown")?.classList.remove("acik");
    document.getElementById("doktor-toggle")?.classList.remove("acik");
  }
});
