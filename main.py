# app.py
from typing import Generator

from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from sqlalchemy import create_engine, Integer, Text, select, desc
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, Session

# --- SQLite Database setup ---------------------------

DATABASE_URL = "sqlite:///blog.db"  # file-based DB in project folder

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


Base.metadata.create_all(engine)

# --- Flask app ---------------------------------------------------------------
app = Flask(__name__)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Error handling (JSON) ---------------------------------------------------

@app.errorhandler(HTTPException)
def on_http_error(e: HTTPException):
    return jsonify({"error": e.name, "message": e.description}), e.code


@app.errorhandler(ValueError)
def on_value_error(e: ValueError):
    return jsonify({"error": "Bad Request", "message": str(e)}), 400


# --- Helpers -----------------------------------------------------------------
def post_to_dict(p: Post) -> dict:
    return {"id": p.id, "author_id": p.author_id, "title": p.title, "body": p.body}


def require_fields(data: dict, *fields: str):
    missing = [f for f in fields if f not in data]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")


# --- User Stories -----------------------------------------------------------

# 1) Create
@app.post("/posts")
def create_post():
    data = request.get_json(force=True) or {}
    require_fields(data, "author_id", "title", "body")

    with SessionLocal() as db:
        post = Post(
            author_id=int(data["author_id"]),
            title=str(data["title"]).strip(),
            body=str(data["body"]).strip(),
        )
        if not post.title:
            raise ValueError("Title cannot be empty.")
        db.add(post)
        db.commit()
        db.refresh(post)
        return jsonify(post_to_dict(post)), 201


# 2) Edit
@app.put("/posts/<int:post_id>")
def edit_post(post_id: int):
    data = request.get_json(force=True) or {}
    require_fields(data, "author_id", "title", "body")

    with SessionLocal() as db:
        post = db.get(Post, post_id)
        if not post:
            abort(404, description="Post not found.")
        if post.author_id != int(data["author_id"]):
            abort(403, description="You can only edit your own posts.")

        post.title = str(data["title"]).strip()
        post.body = str(data["body"]).strip()
        if not post.title:
            raise ValueError("Title cannot be empty.")
        db.commit()
        db.refresh(post)
        return jsonify(post_to_dict(post))


# 3) Browse my posts
@app.get("/posts/mine/<int:author_id>")
def list_my_posts(author_id: int):
    with SessionLocal() as db:
        stmt = select(Post).where(Post.author_id == author_id).order_by(desc(Post.id))
        posts = db.execute(stmt).scalars().all()
        return jsonify([post_to_dict(p) for p in posts])


# 4) Delete
@app.delete("/posts/<int:post_id>")
def delete_post(post_id: int):
    data = request.get_json(silent=True) or {}
    author_id = int(data.get("author_id")) if "author_id" in data else None
    if author_id is None:
        raise ValueError("author_id is required to delete a post.")

    with SessionLocal() as db:
        post = db.get(Post, post_id)
        if not post:
            abort(404, description="Post not found.")
        if post.author_id != author_id:
            abort(403, description="You can only delete your own posts.")

        db.delete(post)
        db.commit()
        return "", 204


# 5) See all posts 
@app.get("/posts")
def list_all_posts():
    with SessionLocal() as db:
        stmt = select(Post).order_by(desc(Post.id))
        posts = db.execute(stmt).scalars().all()
        return jsonify([post_to_dict(p) for p in posts])


if __name__ == "__main__":
    app.run()
