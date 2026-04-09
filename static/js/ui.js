(function () {
	const DEMO_REPORTS = [
		{ id: "TRK-20260409-001", type: "MR", diagnosis: "Glioblastom Multiforme", score: 94.7, level: "Kritik", status: "Kaydedildi", date: "09.04.2026" },
		{ id: "TRK-20260409-002", type: "CT", diagnosis: "Pulmoner Emboli", score: 91.2, level: "Kritik", status: "Kaydedildi", date: "09.04.2026" },
		{ id: "TRK-20260408-004", type: "X-Ray", diagnosis: "Pnömoni", score: 88.1, level: "Orta", status: "Taslak", date: "08.04.2026" },
		{ id: "TRK-20260408-001", type: "MR", diagnosis: "Menenjiyom", score: 92.4, level: "Orta", status: "Kaydedildi", date: "08.04.2026" },
		{ id: "TRK-20260407-006", type: "CT", diagnosis: "Akciğer Nodülü", score: 86.8, level: "Orta", status: "Taslak", date: "07.04.2026" },
		{ id: "TRK-20260407-003", type: "X-Ray", diagnosis: "Normal Bulgular", score: 97.9, level: "Temiz", status: "Kaydedildi", date: "07.04.2026" },
		{ id: "TRK-20260406-002", type: "MR", diagnosis: "Lomber Disk Hernisi", score: 89.3, level: "Orta", status: "Kaydedildi", date: "06.04.2026" },
		{ id: "TRK-20260405-005", type: "CT", diagnosis: "Beyin Kanaması (SDH)", score: 93.5, level: "Kritik", status: "Kaydedildi", date: "05.04.2026" },
		{ id: "TRK-20260404-001", type: "X-Ray", diagnosis: "Tüberküloz", score: 84.4, level: "Orta", status: "Taslak", date: "04.04.2026" },
		{ id: "TRK-20260403-003", type: "MR", diagnosis: "Serebral Enfarktüs", score: 90.6, level: "Kritik", status: "Kaydedildi", date: "03.04.2026" }
	];

	function normalizeScanType(text) {
		const value = (text || "").toLowerCase();
		if (value.includes("x-ray") || value.includes("xray")) {
			return "xray";
		}
		if (value.includes("ct")) {
			return "ct";
		}
		if (value.includes("mr")) {
			return "mr";
		}
		return "";
	}

	function getPath() {
		const rawPath = window.location.pathname.toLowerCase();
		if (rawPath.length > 1 && rawPath.endsWith("/")) {
			return rawPath.slice(0, -1);
		}
		return rawPath;
	}

	function isPath(path) {
		return getPath() === path;
	}

	function isDesktop() {
		return window.matchMedia("(min-width: 1024px)").matches;
	}

	function mapNavLinks(aside) {
		const routes = {
			"Ana Panel": "/dashboard",
			"Yeni Tarama": "/analysis",
			"Raporlarım": "/reports",
			"Tarama Ara": "/scan-search",
			"Profilim": "/profile",
			"Çıkış Yap": "/login"
		};

		aside.querySelectorAll("a").forEach((link) => {
			const label = Array.from(link.querySelectorAll("span"))
				.map((s) => s.textContent.trim())
				.find((txt) => routes[txt]);

			if (label) {
				link.setAttribute("href", routes[label]);
			}

			const spans = link.querySelectorAll("span");
			if (spans.length > 1) {
				spans[1].classList.add("nav-label");
			}
		});
	}

	function getScoreClass(score) {
		if (score >= 90) {
			return "success";
		}
		if (score >= 80) {
			return "warning";
		}
		return "danger";
	}

	function getLevelClass(level) {
		const value = (level || "").toLowerCase();
		if (value.includes("kritik")) {
			return "danger";
		}
		if (value.includes("temiz")) {
			return "success";
		}
		return "warning";
	}

	function getStatusClass(status) {
		const value = (status || "").toLowerCase();
		if (value.includes("taslak")) {
			return "warning";
		}
		return "success";
	}

	function renderDashboardReports() {
		if (!isPath("/dashboard")) {
			return;
		}

		const allReportsLink = Array.from(document.querySelectorAll("section a")).find((link) => (link.textContent || "").includes("Tümünü Gör"));
		if (allReportsLink) {
			allReportsLink.setAttribute("href", "/reports");
		}

		const tbody = document.querySelector("#dashboard-reports-tbody") || document.querySelector("section table tbody");
		if (!tbody) {
			return;
		}

		const recent = DEMO_REPORTS.slice(0, 4);
		tbody.innerHTML = recent
			.map((item) => {
				const scoreClass = getScoreClass(item.score);
				const statusClass = getStatusClass(item.status);
				return (
					"<tr class=\"hover:bg-surface-container-high transition-colors\">" +
					"<td class=\"px-8 py-4 font-mono text-sm text-slate-300\">" + item.id + "</td>" +
					"<td class=\"px-8 py-4\"><span class=\"px-2 py-1 bg-[#1c6ef2]/10 text-[#1c6ef2] text-[0.6875rem] font-bold rounded\">" + item.type + "</span></td>" +
					"<td class=\"px-8 py-4 text-sm font-semibold text-white\">" + item.diagnosis + "</td>" +
					"<td class=\"px-8 py-4\"><div class=\"flex items-center gap-3\"><div class=\"w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden\"><div class=\"h-full bg-status-" + scoreClass + "\" style=\"width: " + item.score + "%;\"></div></div><span class=\"text-xs font-bold text-status-" + scoreClass + "\">%" + item.score.toFixed(1) + "</span></div></td>" +
					"<td class=\"px-8 py-4\"><span class=\"flex items-center gap-1.5 text-xs text-status-" + statusClass + " font-medium\"><span class=\"w-1.5 h-1.5 rounded-full bg-status-" + statusClass + "\"></span>" + item.status + "</span></td>" +
					"<td class=\"px-8 py-4 text-xs text-slate-400\">" + item.date + "</td>" +
					"</tr>"
				);
			})
			.join("");
	}

	function renderReportsTable() {
		if (!isPath("/reports")) {
			return;
		}

		const tbody = document.querySelector("#reports-table-tbody") || document.querySelector("section table tbody");
		if (!tbody) {
			return;
		}

		tbody.innerHTML = DEMO_REPORTS.map((item) => {
			const scoreClass = getScoreClass(item.score);
			const levelClass = getLevelClass(item.level);
			const statusClass = getStatusClass(item.status);
			return (
				"<tr class=\"hover:bg-surface-container-high transition-colors\">" +
				"<td class=\"px-8 py-4 font-mono text-sm text-slate-300\">" + item.id + "</td>" +
				"<td class=\"px-8 py-4\"><span class=\"px-2 py-1 bg-[#1c6ef2]/10 text-[#1c6ef2] text-[0.6875rem] font-bold rounded\">" + item.type + "</span></td>" +
				"<td class=\"px-8 py-4 text-sm font-semibold text-white\">" + item.diagnosis + "</td>" +
				"<td class=\"px-8 py-4\"><div class=\"flex items-center gap-3\"><div class=\"w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden\"><div class=\"h-full bg-status-" + scoreClass + "\" style=\"width: " + item.score + "%;\"></div></div><span class=\"text-xs font-bold text-status-" + scoreClass + "\">%" + item.score.toFixed(1) + "</span></div></td>" +
				"<td class=\"px-8 py-4\"><span class=\"px-2 py-0.5 rounded text-[0.6875rem] font-bold bg-status-" + levelClass + "/10 text-status-" + levelClass + " border border-status-" + levelClass + "/20\">" + item.level + "</span></td>" +
				"<td class=\"px-8 py-4\"><span class=\"flex items-center gap-1.5 text-xs text-status-" + statusClass + " font-medium\"><span class=\"w-1.5 h-1.5 rounded-full bg-status-" + statusClass + "\"></span>" + item.status + "</span></td>" +
				"<td class=\"px-8 py-4 text-xs text-slate-400\">" + item.date + "</td>" +
				"<td class=\"px-8 py-4 text-center\"><a class=\"text-[#1C6EF2] font-semibold text-sm hover:underline inline-flex items-center gap-1\" href=\"#\">Aç <i class=\"fi fi-rr-arrow-small-right\"></i></a></td>" +
				"</tr>"
			);
		}).join("");
	}

	function renderScanSearchTable() {
		if (!isPath("/scan-search")) {
			return;
		}

		const searchInput = document.querySelector("#scan-search-input") || document.querySelector("input[placeholder*='Hastalık adı']");
		if (searchInput) {
			searchInput.value = "";
		}

		const tbody = document.querySelector("#scan-search-table-tbody") || document.querySelector("section table tbody");
		if (!tbody) {
			return;
		}

		tbody.innerHTML = DEMO_REPORTS.map((item) => {
			const scoreClass = getScoreClass(item.score);
			const levelClass = getLevelClass(item.level);
			return (
				"<tr class=\"hover:bg-white/5 transition-colors group\">" +
				"<td class=\"px-8 py-4 font-mono text-sm text-slate-300\">" + item.id + "</td>" +
				"<td class=\"px-8 py-4\"><span class=\"px-2 py-0.5 bg-[#1c6ef2]/10 text-[#1c6ef2] text-[0.6875rem] font-bold rounded\">" + item.type + "</span></td>" +
				"<td class=\"px-8 py-4 text-sm text-white\"><span class=\"font-bold\">" + item.diagnosis + "</span></td>" +
				"<td class=\"px-8 py-4 text-sm font-bold text-status-" + scoreClass + "\">%" + item.score.toFixed(1) + "</td>" +
				"<td class=\"px-8 py-4\"><span class=\"px-2 py-0.5 bg-status-" + levelClass + "/10 text-status-" + levelClass + " text-[0.6875rem] font-bold rounded\">" + item.level + "</span></td>" +
				"<td class=\"px-8 py-4 text-xs text-slate-400\">" + item.date + "</td>" +
				"<td class=\"px-8 py-4 text-right\"><a class=\"text-[#1c6ef2] text-sm font-bold hover:underline inline-flex items-center gap-1\" href=\"#\">Aç <i class=\"fi fi-rr-arrow-small-right\"></i></a></td>" +
				"</tr>"
			);
		}).join("");

		const countLabel = document.querySelector("#scan-search-count") || Array.from(document.querySelectorAll("span")).find((s) => (s.textContent || "").includes("kayıt bulundu"));
		if (countLabel) {
			countLabel.textContent = DEMO_REPORTS.length + " kayıt bulundu";
		}
	}

	function initializeDemoReports() {
		renderDashboardReports();
		renderReportsTable();
		renderScanSearchTable();
	}

	function enableDashboardQuickCards() {
		if (!isPath("/dashboard")) {
			return;
		}

		const cards = Array.from(document.querySelectorAll("main div[class*='grid-cols-3'] > div")).filter((card) => {
			const title = card.querySelector("h4");
			return !!title && /yükle/i.test(title.textContent || "");
		});

		cards.forEach((card) => {
			const title = card.querySelector("h4");
			if (!title) {
				return;
			}

			const type = normalizeScanType(title.textContent);
			if (!type) {
				return;
			}

			card.classList.remove("bg-[#1c6ef2]/10", "border-2", "border-[#1c6ef2]");
			card.classList.add("bg-surface-container-low", "border", "border-white/5", "hover:bg-surface-container-high", "transition-all");

			const iconWrap = card.querySelector("div.w-16.h-16");
			if (iconWrap) {
				iconWrap.classList.remove("bg-[#1c6ef2]", "text-white");
				iconWrap.classList.add("bg-surface-container-highest", "text-[#1c6ef2]");
			}

			const arrowBtn = card.querySelector("button");
			if (arrowBtn) {
				arrowBtn.classList.remove("bg-[#1c6ef2]", "text-white");
				arrowBtn.classList.add("bg-surface-container-highest", "text-[#1c6ef2]", "group-hover:bg-[#1c6ef2]", "group-hover:text-white", "transition-colors");
			}

			card.addEventListener("click", function () {
				window.location.href = "/analysis?type=" + encodeURIComponent(type);
			});
		});
	}

	function getAnalysisTimelineNodes() {
		const timeline = document.querySelector("main .mb-10 .max-w-4xl.mx-auto");
		if (!timeline) {
			return { steps: [], connectors: [] };
		}

		const children = Array.from(timeline.children);
		const steps = children.filter((item) => item.classList.contains("flex") && item.classList.contains("flex-col"));
		const connectors = children.filter((item) => item.classList.contains("flex-1"));
		return { steps, connectors };
	}

	function setTimelineStepState(stepEl, stepNumber, state) {
		const circle = stepEl.querySelector("div.w-8.h-8");
		const labels = stepEl.querySelectorAll("span");
		if (!circle || labels.length < 3) {
			return;
		}

		circle.classList.remove("bg-[#1c6ef2]", "text-white", "border-2", "border-[#1c6ef2]", "bg-[#10141a]", "text-[#1c6ef2]", "border-slate-700", "text-slate-600");
		labels[1].classList.remove("text-[#1c6ef2]", "text-slate-600", "text-slate-400");
		labels[2].classList.remove("text-[#1c6ef2]", "text-slate-600", "text-white", "font-bold", "uppercase", "tracking-wide");

		if (state === "done") {
			circle.classList.add("bg-[#1c6ef2]", "text-white");
			circle.innerHTML = '<span class="material-symbols-outlined text-sm">check</span>';
			labels[1].classList.add("text-slate-400");
			labels[2].classList.add("text-white", "font-bold");
			return;
		}

		if (state === "active") {
			circle.classList.add("border-2", "border-[#1c6ef2]", "bg-[#10141a]", "text-[#1c6ef2]");
			circle.innerHTML = '<span class="text-sm font-bold">' + String(stepNumber) + "</span>";
			labels[1].classList.add("text-[#1c6ef2]");
			labels[2].classList.add("text-[#1c6ef2]", "font-bold", "uppercase", "tracking-wide");
			return;
		}

		circle.classList.add("border-2", "border-slate-700", "text-slate-600");
		circle.innerHTML = '<span class="text-sm font-bold">' + String(stepNumber) + "</span>";
		labels[1].classList.add("text-slate-600");
		labels[2].classList.add("text-slate-600");
	}

	function updateAnalysisTimeline(selectedType, hasUploaded) {
		const nodes = getAnalysisTimelineNodes();
		if (!nodes.steps.length) {
			return;
		}

		let completed = 0;
		let activeIndex = 0;

		if (selectedType) {
			completed = 1;
			activeIndex = 1;
		}

		if (selectedType && hasUploaded) {
			completed = 2;
			activeIndex = 2;
		}

		nodes.steps.forEach((step, idx) => {
			if (idx < completed) {
				setTimelineStepState(step, idx + 1, "done");
			} else if (idx === activeIndex) {
				setTimelineStepState(step, idx + 1, "active");
			} else {
				setTimelineStepState(step, idx + 1, "pending");
			}
		});

		nodes.connectors.forEach((line, idx) => {
			line.classList.remove("bg-[#1c6ef2]", "bg-slate-700");
			line.classList.add(idx < completed ? "bg-[#1c6ef2]" : "bg-slate-700");
		});
	}

	function setAnalysisCardState(card, selected) {
		if (!card) {
			return;
		}

		card.classList.remove("border-2", "border-[#1c6ef2]", "bg-[#1c6ef2]/5");
		card.classList.add("border", "border-white/5", "bg-surface-container-low", "hover:bg-surface-container-high");

		const iconWrap = card.querySelector("div.w-12.h-12");
		if (iconWrap) {
			iconWrap.classList.remove("bg-[#1c6ef2]/20", "text-[#1c6ef2]");
			iconWrap.classList.add("bg-white/5", "text-slate-400");
		}

		if (selected) {
			card.classList.remove("border", "border-white/5", "bg-surface-container-low", "hover:bg-surface-container-high");
			card.classList.add("border-2", "border-[#1c6ef2]", "bg-[#1c6ef2]/5");

			if (iconWrap) {
				iconWrap.classList.remove("bg-white/5", "text-slate-400");
				iconWrap.classList.add("bg-[#1c6ef2]/20", "text-[#1c6ef2]");
			}
		}
	}

	function enableAnalysisScanTypeSelection() {
		if (!isPath("/analysis")) {
			return;
		}

		const cards = Array.from(document.querySelectorAll("main .grid.grid-cols-3 > div")).filter((card) => {
			const title = card.querySelector("h4");
			const t = normalizeScanType((title || {}).textContent || "");
			return !!t;
		});
		if (!cards.length) {
			return;
		}

		const selectedTypeBadge = (function () {
			const labelSpan = Array.from(document.querySelectorAll("span")).find((s) => s.textContent.trim() === "Seçilen Tip:");
			if (!labelSpan) {
				return null;
			}
			const row = labelSpan.closest("div.flex.justify-between.items-center");
			if (!row) {
				return null;
			}
			return row.querySelector("span:last-child");
		})();

		const params = new URLSearchParams(window.location.search);
		let selectedType = normalizeScanType(params.get("type") || "");
		let hasUploaded = false;

		cards.forEach((card) => {
			const title = card.querySelector("h4");
			if (!title) {
				return;
			}

			const type = normalizeScanType(title.textContent);
			setAnalysisCardState(card, false);

			card.addEventListener("click", function () {
				selectedType = type;
				cards.forEach((c) => setAnalysisCardState(c, c === card));
				if (selectedTypeBadge) {
					selectedTypeBadge.textContent = type === "xray" ? "X-RAY" : type.toUpperCase();
				}
				window.history.replaceState({}, "", "/analysis?type=" + encodeURIComponent(type));
				updateAnalysisTimeline(selectedType, hasUploaded);
			});
		});

		const targetCard = cards.find((card) => normalizeScanType((card.querySelector("h4") || {}).textContent) === selectedType);
		if (targetCard) {
			setAnalysisCardState(targetCard, true);
			if (selectedTypeBadge) {
				selectedTypeBadge.textContent = selectedType === "xray" ? "X-RAY" : selectedType.toUpperCase();
			}
		} else if (selectedTypeBadge) {
			selectedTypeBadge.textContent = "-";
		}

		window.addEventListener("atgas-upload-success", function () {
			hasUploaded = true;
			updateAnalysisTimeline(selectedType, hasUploaded);
		});

		updateAnalysisTimeline(selectedType, hasUploaded);
	}

	function extractText(el) {
		return (el ? el.textContent : "").trim();
	}

	function parseScore(text) {
		const m = (text || "").match(/([0-9]+(?:\.[0-9]+)?)/);
		return m ? parseFloat(m[1]) : 0;
	}

	function parseDateTr(value) {
		const raw = (value || "").trim();
		const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
		if (iso) {
			return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
		}

		const m = raw.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
		if (!m) {
			return null;
		}
		return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
	}

	function enableReportsFiltering() {
		if (!isPath("/reports")) {
			return;
		}

		const searchInput = document.querySelector("input[placeholder*='Tarama ID']");
		const filterButtons = Array.from(document.querySelectorAll("div.flex.flex-wrap.gap-2 > button"));
		const rows = Array.from(document.querySelectorAll("#reports-table-tbody tr"));
		const prevButton = document.getElementById("reports-prev-page");
		const nextButton = document.getElementById("reports-next-page");
		const pageNumbersWrap = document.getElementById("reports-page-numbers");
		let activeFilter = "Tümü";
		let currentPage = 1;
		const pageSize = 4;

		if (!rows.length) {
			return;
		}

		const setPagerButtonState = function (button, disabled) {
			if (!button) {
				return;
			}
			button.disabled = !!disabled;
			button.classList.toggle("opacity-40", !!disabled);
			button.classList.toggle("cursor-not-allowed", !!disabled);
		};

		const renderPageButtons = function (totalPages) {
			if (!pageNumbersWrap) {
				return;
			}

			pageNumbersWrap.innerHTML = "";
			for (let p = 1; p <= totalPages; p += 1) {
				const btn = document.createElement("button");
				btn.type = "button";
				btn.textContent = String(p);
				btn.className = "w-8 h-8 rounded flex items-center justify-center transition-colors";
				if (p === currentPage) {
					btn.classList.add("bg-[#1c6ef2]", "text-white");
				} else {
					btn.classList.add("text-[#7D8590]", "hover:bg-[#262a31]");
				}
				btn.addEventListener("click", function () {
					currentPage = p;
					apply();
				});
				pageNumbersWrap.appendChild(btn);
			}
		};

		const apply = function () {
			const q = (searchInput ? searchInput.value : "").toLowerCase().trim();
			const filteredRows = rows.filter((row) => {
				const cells = row.querySelectorAll("td");
				const type = extractText(cells[1]).toLowerCase();
				const seviye = extractText(cells[4]).toLowerCase();
				const durum = extractText(cells[5]).toLowerCase();
				const haystack = row.textContent.toLowerCase();

				const filterOk =
					activeFilter === "Tümü" ||
					(activeFilter.toLowerCase() === "mr" && type.includes("mr")) ||
					(activeFilter.toLowerCase() === "ct" && type.includes("ct")) ||
					(activeFilter.toLowerCase() === "x-ray" && type.includes("x-ray")) ||
					(activeFilter.toLowerCase() === "kritik" && seviye.includes("kritik")) ||
					(activeFilter.toLowerCase() === "taslak" && durum.includes("taslak"));

				const searchOk = !q || haystack.includes(q);
				return filterOk && searchOk;
			});

			const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
			if (currentPage > totalPages) {
				currentPage = totalPages;
			}

			const start = (currentPage - 1) * pageSize;
			const pageRows = filteredRows.slice(start, start + pageSize);

			rows.forEach((row) => {
				row.style.display = pageRows.includes(row) ? "" : "none";
			});

			renderPageButtons(totalPages);
			setPagerButtonState(prevButton, currentPage <= 1);
			setPagerButtonState(nextButton, currentPage >= totalPages);
		};

		filterButtons.forEach((btn) => {
			btn.addEventListener("click", function () {
				activeFilter = btn.textContent.trim();
				currentPage = 1;
				filterButtons.forEach((b) => {
					b.classList.remove("bg-[#1c6ef2]", "text-white");
					if (b !== btn) {
						b.classList.add("bg-[#21262D]", "text-[#7D8590]");
					}
				});
				btn.classList.remove("bg-[#21262D]", "text-[#7D8590]");
				btn.classList.add("bg-[#1c6ef2]", "text-white");
				apply();
			});
		});

		if (searchInput) {
			searchInput.addEventListener("input", function () {
				currentPage = 1;
				apply();
			});
		}

		if (prevButton) {
			prevButton.addEventListener("click", function () {
				if (currentPage > 1) {
					currentPage -= 1;
					apply();
				}
			});
		}

		if (nextButton) {
			nextButton.addEventListener("click", function () {
				currentPage += 1;
				apply();
			});
		}

		apply();
	}

	function enableScanSearchFiltering() {
		if (!isPath("/scan-search")) {
			return;
		}

		const globalInput = document.querySelector("#scan-search-input") || document.querySelector("input[placeholder*='Hastalık adı']");
		const searchButton = document.querySelector("#scan-search-trigger") || Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Ara");
		const applyButton = Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Filtrele");
		const resetButton = Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Sıfırla");
		const rows = Array.from(document.querySelectorAll("#scan-search-table-tbody tr"));
		const countLabel = document.querySelector("#scan-search-count") || Array.from(document.querySelectorAll("span")).find((s) => (s.textContent || "").includes("kayıt bulundu"));
		const emptyState = document.getElementById("scan-search-empty-state") || document.querySelector("div.hidden.flex-col.items-center.justify-center.py-24.text-center");
		const tableWrap = document.querySelector("#scan-search-results .overflow-x-auto");
		const emptyTitle = document.getElementById("scan-search-empty-title");
		const emptyDesc = document.getElementById("scan-search-empty-desc");
		const historyWrap = document.getElementById("scan-search-history-chips");
		const historyKey = "atgas_scan_search_history";
		const filterToggle = document.getElementById("scan-search-filters-toggle");
		const filterIndicator = document.getElementById("scan-search-filters-indicator");

		if (!rows.length || !applyButton || !resetButton) {
			return;
		}

		const typeInputs = Array.from(document.querySelectorAll("input[name='scan_type']"));
		const levelInputs = Array.from(document.querySelectorAll("input[name='level']"));
		const dateStartInput = document.getElementById("scan-search-date-start") || document.querySelector("input[placeholder*='Başlangıç']");
		const dateEndInput = document.getElementById("scan-search-date-end") || document.querySelector("input[placeholder*='Bitiş']");
		const minInput = document.querySelector("input[placeholder='Min %']");
		const maxInput = document.querySelector("input[placeholder='Max %']");
		let hasTriggeredSearch = false;

		const hasActiveFilters = function () {
			const selectedType = getSelectedLabel("scan_type", "Tümü");
			const selectedLevel = getSelectedLabel("level", "Tümü");
			return (
				selectedType !== "Tümü" ||
				selectedLevel !== "Tümü" ||
				!!(dateStartInput && dateStartInput.value) ||
				!!(dateEndInput && dateEndInput.value) ||
				!!(minInput && minInput.value) ||
				!!(maxInput && maxInput.value)
			);
		};

		const updateFilterIndicator = function () {
			if (!filterIndicator) {
				return;
			}
			filterIndicator.classList.toggle("hidden", !hasActiveFilters());
			if (filterToggle) {
				filterToggle.classList.toggle("border-status-danger", hasActiveFilters());
			}
		};

		const readHistory = function () {
			try {
				const raw = window.localStorage.getItem(historyKey);
				const parsed = raw ? JSON.parse(raw) : [];
				if (!Array.isArray(parsed)) {
					return [];
				}
				return parsed.filter((v) => typeof v === "string" && v.trim()).slice(0, 8);
			} catch (_err) {
				return [];
			}
		};

		const writeHistory = function (values) {
			try {
				window.localStorage.setItem(historyKey, JSON.stringify(values.slice(0, 8)));
			} catch (_err) {
				// localStorage unavailable; continue without persistence.
			}
		};

		const pushHistory = function (term) {
			const value = (term || "").trim();
			if (value.length < 2) {
				return;
			}

			const items = readHistory();
			const lowered = value.toLocaleLowerCase("tr-TR");
			const deduped = [value].concat(items.filter((item) => item.toLocaleLowerCase("tr-TR") !== lowered));
			writeHistory(deduped);
			renderHistory();
		};

		const renderHistory = function () {
			if (!historyWrap) {
				return;
			}

			const items = readHistory();
			if (!items.length) {
				historyWrap.innerHTML = '<span class="px-3 py-1 rounded-full border border-white/10 text-xs text-slate-500">Henüz arama yapılmadı</span>';
				return;
			}

			historyWrap.innerHTML = items
				.map((item) => '<button type="button" class="px-3 py-1 rounded-full border border-white/10 text-xs text-slate-300 hover:border-[#1c6ef2] transition-colors" data-history-item="' + item.replace(/"/g, "&quot;") + '">' + item + "</button>")
				.join("");

			historyWrap.querySelectorAll("button[data-history-item]").forEach((btn) => {
				btn.addEventListener("click", function () {
					if (globalInput) {
						globalInput.value = btn.getAttribute("data-history-item") || "";
						applyFilters(true);
						globalInput.focus();
					}
				});
			});
		};

		const getSelectedLabel = function (name, fallback) {
			const input = document.querySelector("input[name='" + name + "']:checked");
			if (!input) {
				return fallback;
			}
			const label = input.closest("label");
			return (label ? label.textContent : fallback).replace("●", "").replace("○", "").trim();
		};

		const setCount = function (visibleCount, hasQuery) {
			if (countLabel) {
				countLabel.textContent = visibleCount + " kayıt bulundu";
			}
			if (tableWrap) {
				tableWrap.style.display = hasQuery ? "block" : "none";
			}
			if (emptyState) {
				emptyState.style.display = visibleCount ? "none" : "flex";
			}
			if (emptyTitle && emptyDesc) {
				if (!hasQuery) {
					emptyTitle.textContent = "Arama yapmak için yazmaya başlayın.";
					emptyDesc.textContent = "Sonuçlar, yazdığınız anda otomatik listelenecektir.";
				} else {
					emptyTitle.textContent = "Kayıt bulunamadı.";
					emptyDesc.textContent = "Farklı arama kriterleri deneyin.";
				}
			}
		};

		const applyFilters = function (shouldPersistHistory) {
			const selectedType = getSelectedLabel("scan_type", "Tümü").toLowerCase();
			const selectedLevel = getSelectedLabel("level", "Tümü").toLowerCase();
			const q = (globalInput ? globalInput.value : "").toLowerCase().trim();
			const hasQuery = q.length > 0;
			const min = minInput && minInput.value ? Number(minInput.value) : null;
			const max = maxInput && maxInput.value ? Number(maxInput.value) : null;
			const startDate = parseDateTr(dateStartInput ? dateStartInput.value : "");
			const endDate = parseDateTr(dateEndInput ? dateEndInput.value : "");
			let visible = 0;

			if (!hasTriggeredSearch) {
				rows.forEach((row) => {
					row.style.display = "none";
				});
				setCount(0, false);
				return;
			}

			if (!hasQuery) {
				rows.forEach((row) => {
					const cells = row.querySelectorAll("td");
					const typeText = extractText(cells[1]).toLowerCase();
					const seviyeText = extractText(cells[4]).toLowerCase();
					const score = parseScore(extractText(cells[3]));
					const date = parseDateTr(extractText(cells[5]));

					const rowType = normalizeScanType(typeText);
					const wantedType = normalizeScanType(selectedType);
					const typeOk = selectedType === "tümü" || (wantedType && rowType === wantedType);
					const levelOk = selectedLevel === "tümü" || seviyeText.includes(selectedLevel);
					const minOk = min === null || score >= min;
					const maxOk = max === null || score <= max;
					const startOk = !startDate || (date && date >= startDate);
					const endOk = !endDate || (date && date <= endDate);
					const show = typeOk && levelOk && minOk && maxOk && startOk && endOk;
					row.style.display = show ? "" : "none";
					if (show) {
						visible += 1;
					}
				});
				setCount(visible, true);
				return;
			}

			rows.forEach((row) => {
				const cells = row.querySelectorAll("td");
				const typeText = extractText(cells[1]).toLowerCase();
				const seviyeText = extractText(cells[4]).toLowerCase();
				const score = parseScore(extractText(cells[3]));
				const date = parseDateTr(extractText(cells[5]));
				const haystack = row.textContent.toLowerCase();

				const rowType = normalizeScanType(typeText);
				const wantedType = normalizeScanType(selectedType);
				const typeOk = selectedType === "tümü" || (wantedType && rowType === wantedType);
				const levelOk = selectedLevel === "tümü" || seviyeText.includes(selectedLevel);
				const queryOk = !q || haystack.includes(q);
				const minOk = min === null || score >= min;
				const maxOk = max === null || score <= max;
				const startOk = !startDate || (date && date >= startDate);
				const endOk = !endDate || (date && date <= endDate);

				const show = typeOk && levelOk && queryOk && minOk && maxOk && startOk && endOk;
				row.style.display = show ? "" : "none";
				if (show) {
					visible += 1;
				}
			});

			setCount(visible, true);
			if (shouldPersistHistory) {
				pushHistory(globalInput ? globalInput.value : "");
			}
			updateFilterIndicator();
		};

		applyButton.addEventListener("click", function () {
			hasTriggeredSearch = true;
			applyFilters(true);
		});
		resetButton.addEventListener("click", function () {
			typeInputs.forEach((input, idx) => {
				input.checked = idx === 0;
			});
			levelInputs.forEach((input, idx) => {
				input.checked = idx === 0;
			});
			if (globalInput) {
				globalInput.value = "";
			}
			if (dateStartInput) {
				dateStartInput.value = "";
			}
			if (dateEndInput) {
				dateEndInput.value = "";
			}
			if (minInput) {
				minInput.value = "";
			}
			if (maxInput) {
				maxInput.value = "";
			}
			hasTriggeredSearch = false;
			applyFilters(false);
			updateFilterIndicator();
		});

		if (searchButton) {
			searchButton.addEventListener("click", function () {
				hasTriggeredSearch = true;
				applyFilters(true);
			});
		}

		if (globalInput) {
			globalInput.addEventListener("keydown", function (event) {
				if (event.key === "Enter") {
					event.preventDefault();
				}
			});
		}

		typeInputs.forEach((input) => input.addEventListener("change", updateFilterIndicator));
		levelInputs.forEach((input) => input.addEventListener("change", updateFilterIndicator));
		if (dateStartInput) {
			dateStartInput.addEventListener("input", updateFilterIndicator);
		}
		if (dateEndInput) {
			dateEndInput.addEventListener("input", updateFilterIndicator);
		}
		if (minInput) {
			minInput.addEventListener("input", updateFilterIndicator);
		}
		if (maxInput) {
			maxInput.addEventListener("input", updateFilterIndicator);
		}

		renderHistory();
		updateFilterIndicator();
		applyFilters(false);
	}

	function enableScanSearchMobileFilterDrawer() {
		if (!isPath("/scan-search")) {
			return;
		}

		const toggle = document.getElementById("scan-search-filters-toggle");
		const panel = document.getElementById("scan-search-filters");
		const closeBtn = document.getElementById("scan-search-filters-close");
		if (!toggle || !panel) {
			return;
		}

		let overlay = document.getElementById("scan-search-filter-overlay");
		if (!overlay) {
			overlay = document.createElement("div");
			overlay.id = "scan-search-filter-overlay";
			document.body.appendChild(overlay);
		}

		const close = function () {
			document.body.classList.remove("filters-open");
		};

		toggle.addEventListener("click", function () {
			document.body.classList.toggle("filters-open");
		});

		overlay.addEventListener("click", close);
		if (closeBtn) {
			closeBtn.addEventListener("click", close);
		}

		document.addEventListener("keydown", function (event) {
			if (event.key === "Escape") {
				close();
			}
		});
	}

	function setAnalysisStepState(step, state) {
		if (!step) {
			return;
		}

		const circle = step.querySelector("span:first-child");
		const label = step.querySelector("span:last-child");
		if (!circle || !label) {
			return;
		}

		step.classList.remove("text-white", "text-slate-400", "text-[#1c6ef2]");
		circle.classList.remove("bg-[#1c6ef2]/20", "text-[#1c6ef2]", "bg-white/5", "text-slate-500", "bg-[#1c6ef2]", "text-white");
		label.classList.remove("font-bold", "font-medium");

		if (state === "done") {
			step.classList.add("text-white");
			circle.classList.add("bg-[#1c6ef2]", "text-white");
			label.classList.add("font-bold");
			return;
		}

		if (state === "active") {
			step.classList.add("text-[#1c6ef2]");
			circle.classList.add("bg-[#1c6ef2]/20", "text-[#1c6ef2]");
			label.classList.add("font-bold");
			return;
		}

		step.classList.add("text-slate-400");
		circle.classList.add("bg-white/5", "text-slate-500");
		label.classList.add("font-medium");
	}

	function setupAnalysisInputRules() {
		if (!isPath("/analysis")) {
			return;
		}

		const nameInput = document.getElementById("analysis-patient-name");
		const tcInput = document.getElementById("analysis-patient-tc");
		const protocolInput = document.getElementById("analysis-patient-protocol");
		const birthDateInput = document.getElementById("analysis-patient-birthdate");
		const startBtn = document.getElementById("analysis-start-btn");
		const processSteps = Array.from(document.querySelectorAll("#analysis-process-steps [data-analysis-step]"));

		if (!nameInput || !tcInput || !protocolInput || !birthDateInput || !processSteps.length) {
			return;
		}

		const digitsOnly = function (value) {
			return (value || "").replace(/\D+/g, "");
		};

		const lettersOnly = function (value) {
			return (value || "").replace(/[0-9]/g, "");
		};

		const getSelectedType = function () {
			const badge = Array.from(document.querySelectorAll("span")).find((s) => s.textContent.trim() === "Seçilen Tip:");
			if (!badge) {
				return "";
			}
			const row = badge.closest("div.flex.justify-between.items-center");
			if (!row) {
				return "";
			}
			const value = (row.querySelector("span:last-child") || {}).textContent || "";
			return value.trim() === "-" ? "" : value.trim();
		};

		const updateProcessSteps = function () {
			const selectedType = !!getSelectedType();
			const hasUploadNote = !!document.querySelector("[data-upload-result].upload-success-note");
			const nameValid = lettersOnly(nameInput.value).trim().length >= 3;
			const tcValid = digitsOnly(tcInput.value).length === 11;
			const protocolValid = digitsOnly(protocolInput.value).length > 0;
			const birthValid = !!birthDateInput.value;
			const patientValid = nameValid && tcValid && protocolValid && birthValid;

			setAnalysisStepState(processSteps[0], selectedType ? "done" : "active");
			setAnalysisStepState(processSteps[1], selectedType ? (hasUploadNote ? "done" : "active") : "pending");
			setAnalysisStepState(processSteps[2], hasUploadNote ? (patientValid ? "done" : "active") : "pending");
			setAnalysisStepState(processSteps[3], patientValid ? "active" : "pending");

			if (startBtn) {
				startBtn.disabled = !patientValid;
				startBtn.classList.toggle("opacity-50", !patientValid);
				startBtn.classList.toggle("cursor-not-allowed", !patientValid);
			}
		};

		nameInput.addEventListener("input", function () {
			const cleaned = lettersOnly(nameInput.value);
			if (cleaned !== nameInput.value) {
				nameInput.value = cleaned;
			}
			updateProcessSteps();
		});

		tcInput.addEventListener("input", function () {
			const cleaned = digitsOnly(tcInput.value).slice(0, 11);
			if (cleaned !== tcInput.value) {
				tcInput.value = cleaned;
			}
			updateProcessSteps();
		});

		protocolInput.addEventListener("input", function () {
			const cleaned = digitsOnly(protocolInput.value);
			if (cleaned !== protocolInput.value) {
				protocolInput.value = cleaned;
			}
			updateProcessSteps();
		});

		birthDateInput.addEventListener("input", updateProcessSteps);
		window.addEventListener("atgas-upload-success", updateProcessSteps);
		window.addEventListener("click", function (event) {
			const card = event.target && event.target.closest ? event.target.closest("main .grid.grid-cols-3 > div") : null;
			if (card) {
				window.setTimeout(updateProcessSteps, 0);
			}
		});

		updateProcessSteps();
	}

	function enableProfileTabs() {
		if (!isPath("/profile")) {
			return;
		}

		const tabButtons = Array.from(document.querySelectorAll("[data-tab-target]"));
		const tabPanels = Array.from(document.querySelectorAll("[data-tab-panel]"));
		if (!tabButtons.length || !tabPanels.length) {
			return;
		}

		const activate = function (target) {
			tabButtons.forEach((btn) => {
				btn.classList.remove("text-white", "font-semibold", "border-b-2", "border-[#1c6ef2]");
				btn.classList.add("text-slate-400", "font-medium");
			});

			tabPanels.forEach((panel) => {
				panel.classList.add("hidden");
			});

			const activeButton = tabButtons.find((btn) => btn.dataset.tabTarget === target);
			const activePanel = tabPanels.find((panel) => panel.dataset.tabPanel === target);

			if (activeButton) {
				activeButton.classList.remove("text-slate-400", "font-medium");
				activeButton.classList.add("text-white", "font-semibold", "border-b-2", "border-[#1c6ef2]");
			}

			if (activePanel) {
				activePanel.classList.remove("hidden");
			}
		};

		tabButtons.forEach((btn) => {
			btn.addEventListener("click", function () {
				activate(btn.dataset.tabTarget);
			});
		});

		activate("personal");
	}

	document.addEventListener("DOMContentLoaded", function () {
		const aside = document.querySelector("aside.fixed.left-0");
		const header = document.querySelector("header.fixed");
		const main = document.querySelector("main");

		if (!aside || !header || !main) {
			return;
		}

		document.body.classList.add("app-shell");
		document.body.classList.add("page-" + (getPath().slice(1).replace(/\//g, "-") || "root"));
		mapNavLinks(aside);

		const overlay = document.createElement("div");
		overlay.id = "sidebar-overlay";
		document.body.appendChild(overlay);

		const firstHeaderGroup = header.querySelector("div.flex.items-center.gap-2") || header.firstElementChild;
		const toggleButton = document.createElement("button");
		toggleButton.id = "sidebar-toggle";
		toggleButton.type = "button";
		toggleButton.setAttribute("aria-label", "Sidebar menuyu ac/kapat");
		toggleButton.innerHTML = '<span class="material-symbols-outlined">menu</span>';

		if (firstHeaderGroup) {
			firstHeaderGroup.prepend(toggleButton);
		}

		const closeMobileMenu = function () {
			document.body.classList.remove("sidebar-open");
			toggleButton.innerHTML = '<span class="material-symbols-outlined">menu</span>';
		};

		const toggleSidebar = function () {
			if (isDesktop()) {
				return;
			}

			document.body.classList.toggle("sidebar-open");
			const isOpen = document.body.classList.contains("sidebar-open");
			toggleButton.innerHTML = isOpen
				? '<span class="material-symbols-outlined">close</span>'
				: '<span class="material-symbols-outlined">menu</span>';
		};

		toggleButton.addEventListener("click", toggleSidebar);
		overlay.addEventListener("click", closeMobileMenu);

		window.addEventListener("resize", function () {
			if (isDesktop()) {
				document.body.classList.remove("sidebar-open");
				toggleButton.innerHTML = '<span class="material-symbols-outlined">menu</span>';
			} else if (!document.body.classList.contains("sidebar-open")) {
				toggleButton.innerHTML = '<span class="material-symbols-outlined">menu</span>';
			}
		});

		initializeDemoReports();
		enableDashboardQuickCards();
		enableAnalysisScanTypeSelection();
		setupAnalysisInputRules();
		enableReportsFiltering();
		enableScanSearchFiltering();
		enableScanSearchMobileFilterDrawer();
		enableProfileTabs();
	});
})();
