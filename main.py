#imports
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from sqlalchemy import create_engine, Integer, Text, select, desc
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

# --- SQLite Database setup ---------------------------

DATABASE_URL = "sqlite:///blog.db"  
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

# --- App ------------------------------------------------------
app = Flask(__name__)


# --- HTTP Error  ---------------------------------------------------

@app.errorhandler(HTTPException)
def on_http_error(http_error):
    return jsonify({"error": http_error.name, "message": http_error.description}), http_error.code

# --- Utils ------------------------------------------------------------

def post_to_dict(post):
    return {"id": post.id, "author_id": post.author_id, "title": post.title, "body": post.body}


def require_fields(data: dict, *fields: str):
    missing = [f for f in fields if f not in data]
    if missing:
        abort(400, description=f"Missing fields: {', '.join(missing)}")


# --- User Stories -----------------------------------------------------------

# Create a post
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
            abort(400, description="Title cannot be empty.")
        db.add(post)
        db.commit()
        db.refresh(post)
        return jsonify(post_to_dict(post)), 201


# Edit my post
@app.put("/posts/<int:post_id>")
def edit_post(post_id):
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
            abort(400, description="Title cannot be empty.")
        db.commit()
        return jsonify(post_to_dict(post))


# Browse my posts
@app.get("/posts/mine/<int:author_id>")
def list_my_posts(author_id):
    with SessionLocal() as db:
        stmt = select(Post).where(Post.author_id == author_id).order_by(desc(Post.id))
        posts = db.execute(stmt).scalars().all()
        return jsonify([post_to_dict(p) for p in posts])


# Delete one post
@app.delete("/posts/<int:post_id>")
def delete_post(post_id):
    data = request.get_json(silent=True) or {}
    if "author_id" not in data:
        abort(400, description="author_id is required to delete a post.")
    try: 
        author_id = int(data["author_id"])
    except (TypeError, ValueError):
        abort(400, description="author_id must be an integer.")
        
    with SessionLocal() as db:
        post = db.get(Post, post_id)
        if not post:
            abort(404, description="Post not found.")
        if post.author_id != author_id:
            abort(403, description="You can only delete your own posts.")

        db.delete(post)
        db.commit()
        return "", 204


# See all posts 
@app.get("/posts")
def list_all_posts():
    with SessionLocal() as db:
        stmt = select(Post).order_by(desc(Post.id))
        posts = db.execute(stmt).scalars().all()
        return jsonify([post_to_dict(p) for p in posts])


if __name__ == "__main__":
    app.run()
