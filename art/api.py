from ninja import Router

router = Router()


@router.get("/")
def list_events(request):
    return [{"id": 1, "title": "TEST TITLE"}]


@router.get("/{event_id}")
def event_details(request, event_id: int):
    return {"title": "TEST TITLE", "details": "TEST DETAILS"}
