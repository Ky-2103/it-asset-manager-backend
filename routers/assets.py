from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import admin_required, get_current_user
from database import get_db
from models import Asset, User
from schemas import AssetCreate, AssetOut, AssetUpdate

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=list[AssetOut])
def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Asset).all()


@router.get("/my", response_model=list[AssetOut])
def get_my_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Asset).filter(Asset.assigned_user_id == current_user.id).all()


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):

    if db.query(Asset).filter(Asset.asset_tag == payload.asset_tag).first():
        raise HTTPException(status_code=400, detail="asset_tag already exists")

    if payload.status == "Assigned" and not payload.assigned_user_id:
        raise HTTPException(status_code=400, detail="assigned_user_id is required when status is Assigned")

    if payload.assigned_user_id:
        assigned_user = db.query(User).filter(User.id == payload.assigned_user_id).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    payload.created_at = datetime.now()
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if payload.asset_tag and payload.asset_tag != asset.asset_tag:
        existing = db.query(Asset).filter(Asset.asset_tag == payload.asset_tag).first()
        if existing:
            raise HTTPException(status_code=400, detail="asset_tag already exists")
        asset.asset_tag = payload.asset_tag

    if payload.name:
        asset.name = payload.name
    if payload.category:
        asset.category = payload.category

    requested_status = payload.status if payload.status is not None else asset.status
    requested_user_id = payload.assigned_user_id if payload.assigned_user_id is not None else asset.assigned_user_id

    if requested_status == "Assigned" and not requested_user_id:
        raise HTTPException(status_code=400, detail="assigned_user_id is required when status is Assigned")

    if payload.assigned_user_id is not None:
        if payload.assigned_user_id:
            user = db.query(User).filter(User.id == payload.assigned_user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Assigned user not found")

            asset.assigned_user_id = payload.assigned_user_id
        else:
            asset.assigned_user_id = None

    if payload.status:
        asset.status = payload.status

    if asset.status != "Assigned":
        asset.assigned_user_id = None

    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return None
