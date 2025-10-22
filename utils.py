from flask import abort

def post_to_dict(post) -> dict:
    """Transforms a post to a dict object"""
    return {"id": post.id, "author_id": post.author_id, "title": post.title, "body": post.body}

def require_fields(data: dict, *fields: str) -> None:
    missing = [f for f in fields if f not in data]
    if missing:
        abort(400, description=f"Missing fields: {', '.join(missing)}")