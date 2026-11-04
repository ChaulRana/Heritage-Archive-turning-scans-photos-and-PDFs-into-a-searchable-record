import os, uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from services import db as database
from services.ocr import extract_text
from services.tagger import analyse, CATEGORIES, ERAS

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
    DB_PATH=os.environ.get("DB_PATH", "archive.db"),
    UPLOAD_DIR="uploads",
    MAX_CONTENT_LENGTH=25 * 1024 * 1024,
)
ALLOWED = {"png", "jpg", "jpeg", "tif", "tiff", "pdf"}
os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
app.teardown_appcontext(database.close_db)
with app.app_context():
    database.init_db()

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "")
    era = request.args.get("era", "")
    sql = ("SELECT DISTINCT i.* FROM items i LEFT JOIN item_tags it ON it.item_id=i.id "
           "LEFT JOIN tags t ON t.id=it.tag_id WHERE 1=1")
    params = []
    if q:
        sql += " AND (i.title LIKE ? OR i.extracted_text LIKE ? OR i.location LIKE ? OR t.name LIKE ?)"
        params += [f"%{q}%"] * 4
    if cat:
        sql += " AND i.category=?"; params.append(cat)
    if era:
        sql += " AND i.era=?"; params.append(era)
    items = database.get_db().execute(sql + " ORDER BY i.created_at DESC", params).fetchall()
    return render_template("index.html", items=items, q=q, cat=cat, era=era,
                           categories=list(CATEGORIES), eras=list(ERAS))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = [f for f in request.files.getlist("files") if f.filename]
        saved = 0
        for f in files:
            ext = f.filename.rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED:
                flash(f"{f.filename}: unsupported file type. Use PNG, JPG, TIFF or PDF.")
                continue
            name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename)}"
            path = os.path.join(app.config["UPLOAD_DIR"], name)
            f.save(path)
            try:
                text = extract_text(path)
            except Exception as e:
                flash(f"{f.filename}: could not read text ({e}).")
                text = ""
            info = analyse(text)
            db = database.get_db()
            cur = db.execute(
                "INSERT INTO items(title, filename, file_type, extracted_text, category, era, location, language) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (request.form.get("title") or f.filename.rsplit(".", 1)[0], name, ext, text,
                 info["category"], info["era"], info["location"], info["language"]))
            database.set_tags(cur.lastrowid, info["tags"])
            saved += 1
        if saved:
            flash(f"{saved} item(s) added to the archive.")
            return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/item/<int:item_id>")
def item(item_id):
    row = database.get_db().execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        abort(404)
    return render_template("item.html", item=row, tags=database.get_tags(item_id),
                           categories=list(CATEGORIES), eras=list(ERAS))

@app.route("/item/<int:item_id>/edit", methods=["POST"])
def edit(item_id):
    f = request.form
    db = database.get_db()
    db.execute("UPDATE items SET title=?, category=?, era=?, location=? WHERE id=?",
               (f["title"], f["category"], f["era"], f["location"], item_id))
    db.commit()
    database.set_tags(item_id, f.get("tags", "").split(","))
    flash("Changes saved.")
    return redirect(url_for("item", item_id=item_id))

@app.route("/files/<path:name>")
def files(name):
    return send_from_directory(app.config["UPLOAD_DIR"], name)

if __name__ == "__main__":
    app.run(debug=True)
