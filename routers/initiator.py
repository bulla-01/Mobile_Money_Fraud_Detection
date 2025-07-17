from fastapi import APIRouter

router = APIRouter()

@router.get("/initiator/test")
def test_initiator():
    return {"message": "Initiator endpoint working!"}
