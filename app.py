from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "img" / "uploads"

ALLOWED_EXTENSIONS = {
	"dcm",
	"dicom",
	"png",
	"jpg",
	"jpeg",
	"nii",
	"nii.gz",
}


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _is_allowed(filename: str) -> bool:
	lower_name = filename.lower()
	if lower_name.endswith(".nii.gz"):
		return True
	if "." not in filename:
		return False
	return lower_name.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


@app.route("/")
def root():
	return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email = (request.form.get("email") or "").strip()
		password = (request.form.get("password") or "").strip()

		if email == "demo" and password == "demo":
			return redirect(url_for("dashboard"))

		return render_template("login.html", login_error=True, entered_email=email)

	return render_template("login.html", login_error=False, entered_email="")


@app.route("/dashboard")
def dashboard():
	return render_template("dashboard.html")


@app.route("/analysis")
def analysis():
	return render_template("analysis.html")


@app.route("/analysis/progress")
def analysis_progress():
	return render_template("analysis_progress.html")


@app.route("/analysis/result")
def analysis_result():
	return render_template("analysis_result.html")


@app.route("/reports")
def reports():
	return render_template("reports.html")


@app.route("/profile")
def profile():
	return render_template("profile.html")


@app.route("/scan-search")
def scan_search():
	return render_template("scan_search.html")


@app.post("/upload-image")
def upload_image():
	if "image" not in request.files:
		return jsonify({"ok": False, "error": "Dosya bulunamadi."}), 400

	image = request.files["image"]
	if not image or not image.filename:
		return jsonify({"ok": False, "error": "Gecerli bir dosya secin."}), 400

	if not _is_allowed(image.filename):
		return jsonify({"ok": False, "error": "Desteklenmeyen dosya formati."}), 400

	original_name = secure_filename(image.filename)
	filename = f"{uuid4().hex}_{original_name}"
	save_path = UPLOAD_DIR / filename
	image.save(save_path)

	return jsonify(
		{
			"ok": True,
			"filename": filename,
			"relative_path": f"img/uploads/{filename}",
			"url": url_for("static", filename=f"img/uploads/{filename}"),
		}
	)


if __name__ == "__main__":
	app.run(debug=True)
