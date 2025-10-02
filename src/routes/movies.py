from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page"),
):
    result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = result.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = await db.execute(
        select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    )
    movies = movies.scalars().all()

    base_url = "/theater/movies/"
    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema.model_validate(
        {
            "movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items,
        }
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieDetailResponseSchema.model_validate(movie)
