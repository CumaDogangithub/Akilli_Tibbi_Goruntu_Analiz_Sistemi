(function () {
	const ALLOWED = [
		"image/png",
		"image/jpeg",
		"application/dicom",
		"application/dicom+json",
		"application/octet-stream"
	];

	function hasAllowedExtension(fileName) {
		const lower = fileName.toLowerCase();
		return [".dcm", ".dicom", ".png", ".jpg", ".jpeg", ".nii", ".nii.gz"].some((ext) => lower.endsWith(ext));
	}

	function showMessage(container, text, isError) {
		if (!container) {
			return;
		}
		container.textContent = text;
		container.className = isError ? "upload-error-note" : "upload-success-note";
	}

	async function uploadFile(file, resultBox, progressText) {
		if (!file) {
			return;
		}

		if (!ALLOWED.includes(file.type) && !hasAllowedExtension(file.name)) {
			showMessage(resultBox, "Desteklenmeyen dosya turu. DICOM, PNG, JPG, JPEG, NIfTI desteklenir.", true);
			return;
		}

		progressText.textContent = "Yukleniyor...";
		const formData = new FormData();
		formData.append("image", file);

		try {
			const response = await fetch("/upload-image", {
				method: "POST",
				body: formData
			});

			const data = await response.json();
			if (!response.ok || !data.ok) {
				throw new Error(data.error || "Dosya yuklenemedi.");
			}

			progressText.textContent = "Yukleme tamamlandi";
			showMessage(resultBox, "Dosya basariyla yuklendi: " + data.filename, false);
			window.dispatchEvent(new CustomEvent("atgas-upload-success", { detail: data }));
		} catch (error) {
			progressText.textContent = "Yukleme basarisiz";
			showMessage(resultBox, error.message || "Dosya yuklenirken bir hata olustu.", true);
		}
	}

	document.addEventListener("DOMContentLoaded", function () {
		const dropzone = document.querySelector("[data-upload-dropzone]");
		const pickerButton = document.querySelector("[data-upload-btn]");
		const resultBox = document.querySelector("[data-upload-result]");
		const progressText = document.querySelector("[data-upload-progress]");

		if (!dropzone || !pickerButton || !resultBox || !progressText) {
			return;
		}

		const input = document.createElement("input");
		input.type = "file";
		input.accept = ".dcm,.dicom,.png,.jpg,.jpeg,.nii,.nii.gz";
		input.hidden = true;
		dropzone.appendChild(input);

		pickerButton.addEventListener("click", function (event) {
			event.preventDefault();
			input.click();
		});

		input.addEventListener("change", function () {
			if (input.files && input.files.length) {
				uploadFile(input.files[0], resultBox, progressText);
			}
		});

		["dragenter", "dragover"].forEach((name) => {
			dropzone.addEventListener(name, function (event) {
				event.preventDefault();
				event.stopPropagation();
				dropzone.classList.add("border-[#1c6ef2]");
			});
		});

		["dragleave", "drop"].forEach((name) => {
			dropzone.addEventListener(name, function (event) {
				event.preventDefault();
				event.stopPropagation();
				dropzone.classList.remove("border-[#1c6ef2]");
			});
		});

		dropzone.addEventListener("drop", function (event) {
			const files = event.dataTransfer ? event.dataTransfer.files : null;
			if (files && files.length) {
				uploadFile(files[0], resultBox, progressText);
			}
		});
	});
})();
