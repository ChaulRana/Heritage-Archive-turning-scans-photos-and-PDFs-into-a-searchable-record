import sqlite3
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode())
    db.commit()

def set_tags(item_id, names):
    db = get_db()
    db.execute("DELETE FROM item_tags WHERE item_id=?", (item_id,))
    for n in {x.strip().lower() for x in names if x.strip()}:
        db.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (n,))
        tid = db.execute("SELECT id FROM tags WHERE name=?", (n,)).fetchone()[0]
        db.execute("INSERT OR IGNORE INTO item_tags VALUES(?,?)", (item_id, tid))
    db.commit()

def get_tags(item_id):
    rows = get_db().execute(
        "SELECT t.name FROM tags t JOIN item_tags it ON it.tag_id=t.id WHERE it.item_id=? ORDER BY t.name",
        (item_id,)).fetchall()
    return [r["name"] for r in rows]
