from fastapi import APIRouter

router = APIRouter()

@router.post("/citydate", response_model=bool)
def post_city_date():
    return True

@router.get("/citydate", response_model=bool)
def get_city_date():
    return True
