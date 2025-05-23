from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from will_flow.models.flow import Flow, FlowCreate, FlowUpdate
from will_flow.services.flow_service import FlowService

router = APIRouter()
flow_service = FlowService()


@router.post("/", response_model=Flow)
async def create_flow(flow: FlowCreate):
    """
    Create a new flow.
    """
    return await flow_service.create_flow(flow)


@router.get("/{flow_id}", response_model=Flow)
async def get_flow(flow_id: str):
    """
    Get flow by ID.
    """
    flow = await flow_service.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@router.put("/{flow_id}", response_model=Flow)
async def update_flow(flow_id: str, flow_update: FlowUpdate):
    """
    Update a flow.
    """
    flow = await flow_service.update_flow(flow_id, flow_update)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@router.delete("/{flow_id}", response_model=bool)
async def delete_flow(flow_id: str):
    """
    Delete a flow.
    """
    success = await flow_service.delete_flow(flow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flow not found")
    return success


@router.get("/", response_model=List[Flow])
async def list_flows(
    creator_email: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List flows, optionally filtered by creator email.
    """
    return await flow_service.list_flows(creator_email, limit, offset) 