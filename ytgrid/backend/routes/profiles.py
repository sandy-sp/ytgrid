from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ytgrid.database.repository import ProfileRepository
from ytgrid.backend.auth import verify_api_key

router = APIRouter(tags=["Profiles"])

class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProfileEntryCreate(BaseModel):
    video_url: str
    speed: float = 1.0
    loop_count: int = 1

def get_repo():
    return ProfileRepository()

@router.post("/", dependencies=[Depends(verify_api_key)])
async def create_profile(request: ProfileCreate, repo: ProfileRepository = Depends(get_repo)):
    try:
        profile_id = await repo.create_profile(request.name, request.description)
        return {"status": "success", "profile_id": profile_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", dependencies=[Depends(verify_api_key)])
async def list_profiles(repo: ProfileRepository = Depends(get_repo)):
    return await repo.list_profiles()

@router.get("/{identifier}", dependencies=[Depends(verify_api_key)])
async def get_profile(identifier: str, repo: ProfileRepository = Depends(get_repo)):
    # Try looking up by integer ID first, else fallback to name
    val = identifier
    if identifier.isdigit():
        val = int(identifier)
    profile = await repo.get_profile(val)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/{profile_id}/entries", dependencies=[Depends(verify_api_key)])
async def add_entry(profile_id: int, entry: ProfileEntryCreate, repo: ProfileRepository = Depends(get_repo)):
    profile = await repo.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    entry_id = await repo.add_entry(
        profile_id=profile_id,
        video_url=entry.video_url,
        speed=entry.speed,
        loop_count=entry.loop_count
    )
    return {"status": "success", "entry_id": entry_id}

@router.post("/{identifier}/run", dependencies=[Depends(verify_api_key)])
async def run_profile(identifier: str, repo: ProfileRepository = Depends(get_repo)):
    import uuid
    from ytgrid.backend.task_manager import task_manager

    val = int(identifier) if identifier.isdigit() else identifier
    profile = await repo.get_profile(val)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if not profile.get('entries'):
        raise HTTPException(status_code=400, detail="Profile has no entries to run")

    running_sessions = []
    # Each entry gets its own generated session id, started via the task manager.
    for entry in profile['entries']:
        session_id = uuid.uuid4().hex[:8]
        started = task_manager.start_session(
            session_id=session_id,
            url=entry['video_url'],
            speed=entry['speed'],
            loop_count=entry['loop_count'],
        )
        if started:
            await repo.record_execution_start(session_id, profile['id'])
            running_sessions.append(session_id)

    if not running_sessions:
        raise HTTPException(
            status_code=503,
            detail="No sessions could be started (system throttled or duplicates).",
        )

    return {"status": "success", "sessions": running_sessions}

@router.delete("/{profile_id}", dependencies=[Depends(verify_api_key)])
async def delete_profile(profile_id: int, repo: ProfileRepository = Depends(get_repo)):
    deleted = await repo.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}

@router.get("/{profile_id}/history", dependencies=[Depends(verify_api_key)])
async def get_history(profile_id: int, repo: ProfileRepository = Depends(get_repo)):
    return await repo.get_history(profile_id)
