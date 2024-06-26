import http
import models as db
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from database import session
from schemas import CreateUser, User, GetFavorite, CreateCategory, CreatePost, Category, CreateLike, GetPost, \
    CreateComments, Comments


app = FastAPI()


def get_db():
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/users", response_model=dict, tags=["User"])
def add_user(user: CreateUser, session: Session = Depends(get_db)) -> dict:
    try:
        if user.password == "":
            return {"message": "Password is empty"}
        new_user = db.User(**user.model_dump())
        session.add(new_user)
        cur_id = session.query(db.User).where(db.User.username == user.username).first().id
        session.add(db.Favorite(owner_id=cur_id))
        return {"message": "User added successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users", response_model=list[User], tags=["User"])
def get_users(session: Session = Depends(get_db)):
    try:
        users = session.execute(select(db.User)).scalars().all()
        user_response = [User.validate(user) for user in users]
        return user_response
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=User, tags=["User"])
def get_user_by_id(user_id: str, session: Session = Depends(get_db)):
    try:
        user = session.query(db.User).filter(db.User.id == user_id).first()
        if user.id:
            return User.model_validate(user)
        else:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail={"message": "User not found"})
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}", response_model=dict, tags=["User"])
def delete_user(user_id: str, session: Session = Depends(get_db)):
    try:
        favorite_count = session.execute(delete(db.Favorite).where(db.Favorite.owner_id == user_id)).rowcount
        deleted_count = session.execute(delete(db.User).where(db.User.id == user_id)).rowcount
        if deleted_count == 0 or favorite_count == 0:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/favorite/{user_id}", tags=["Favorite"])
def get_user_favorite(user_id: str, session: Session = Depends(get_db)):
    try:
        favorite = session.query(db.Favorite).filter(db.Favorite.owner_id == user_id).first()
        if not favorite.id:
            return {"message": "favorite not found!"}
        return GetFavorite.model_validate(favorite)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/category", tags=["Category"], response_model=dict)
def add_category(category: CreateCategory, session: Session = Depends(get_db)):
    if not category.name:
        return {"message": "name is empty!"}

    session.add(db.Category(**category.model_dump()))

    return {"message": "category is created!"}


@app.get("/category", tags=["Category"], response_model=list[Category])
def get_categories(session: Session = Depends(get_db)):
    try:
        cat = session.execute(select(db.Category)).scalars().all()
        return [Category.model_validate(c) for c in cat]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/category/{id}", tags=["Category"], response_model=dict)
def update_category(category_id: str, name: str, session: Session = Depends(get_db)):
    try:
        category = session.query(db.Category).filter(db.Category.id == category_id).first()
        category.name = name
        session.commit()
        return {"message": "name category updated!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/category/{id}", tags=["Category"], response_model=dict)
def delete_category(id: str, session: Session = Depends(get_db)):
    try:
        deleted_row = session.execute(delete(db.Category).where(db.Category.id == id)).rowcount
        if deleted_row == 0:
            return {"message": "Id is not valid"}
        return {"message": "Category deleted!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/post", tags=["Post"], response_model=list[GetPost])
def get_posts():
    try:
        post = session.query(db.Post).all()
        response = [GetPost.model_validate(p) for p in post]
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/post", tags=["Post"], response_model=dict)
def add_post(post: CreatePost, session: Session = Depends(get_db)):
    if post.title == "" or post.content == "":
        return {"message": "post title or content is empty!"}
    session.add(db.Post(**post.model_dump()))
    return {"message": "post is created!"}


@app.delete("/post/{id}", tags=["Post"], response_model=dict)
def delete_post(id: str, session: Session = Depends(get_db)):
    try:
        row_count = session.execute(delete(db.Post).where(db.Post.id == id)).rowcount
        if row_count == 0:
            return {"message": "ID is not valid!"}
        return {"message": "post successfully deleted!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/like", tags=["Like"], response_model=dict)
def like_post(like: CreateLike, session: Session = Depends(get_db)):
    try:
        session.add(db.Like(**like.model_dump()))
        return {"message": f"like putted under the post {like.post_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/like", tags=["Like"], response_model=dict)
def delete_like(id: str, session: Session = Depends(get_db)):
    try:
        row_count = session.execute(delete(db.Like).where(db.Like.id == id)).rowcount
        if row_count == 0:
            return {"message": "id is not valid!"}
        return {"message": "like successfully deleted!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Comments handlers

@app.get("/comments", status_code=200, tags=["Comments"])
def read_comments(session: Session = Depends(get_db)):
    response = session.query(db.Comment).all()
    return response


@app.post("/comments", status_code=http.HTTPStatus.CREATED, tags=["Comments"], response_model=CreateComments)
def create_comment(comment: CreateComments, session: Session = Depends(get_db)):
    try:
        new_comment = db.Comment(**comment.dict())
        session.add(new_comment)
        return new_comment
    except Exception as e:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/comments/{comment_id}", status_code=http.HTTPStatus.OK, tags=["Comments"], response_model=Comments)
def read_comment(comment_id: str, session: Session = Depends(get_db)):
    try:
        response = session.query(db.Comment).filter(db.Comment.id == comment_id).first()
        return Comments.model_validate(response)
    except Exception as e:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/comments/{comment_id}", status_code=http.HTTPStatus.OK, tags=["Comments"])
def delete_comment(comment_id: str, session: Session = Depends(get_db)):
    try:
        row = session.execute(delete(db.Comment).filter(db.Comment.id == comment_id)).rowcount
        if row == 0:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail=f"comment by id {comment_id} not found")
        return "Comment deleted!"
    except Exception as e:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@app.patch("/comments/{comment_id}", status_code=http.HTTPStatus.OK, tags=["Comments"])
def update_comment(comment_id: str, body: str, session: Session = Depends(get_db)):
    try:
        response = session.query(db.Comment).where(db.Comment.id == comment_id).first()
        response.body = body
        session.commit()
        return "Comment updated!"
    except Exception as e:
        raise HTTPException(status_code=http.HTTPStatus.OK, detail=str(e))


@app.get("/comments/{post_id}")
def get_post_comments(post_id: str, session: Session = Depends(get_db)):
    try:
        comments = session.query(db.Comment).where(db.Comment.post_id == post_id).all()
        print(comments)
    except Exception as e:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
