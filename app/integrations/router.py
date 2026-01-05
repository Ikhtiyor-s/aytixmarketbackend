from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import httpx
import hashlib
import hmac
import time
from app.core.database import get_db
from app.dependencies import get_current_admin
from app.models import User, Integration, IntegrationStatus, ConnectedIntegration, IntegrationProject
from app.schemas import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse,
    ConnectedIntegrationCreate, ConnectedIntegrationUpdate, ConnectedIntegrationResponse,
    IntegrationProjectCreate, IntegrationProjectUpdate, IntegrationProjectResponse,
    IntegrationTestRequest, IntegrationTestResponse
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/public", response_model=List[IntegrationResponse])
async def get_public_integrations(
    db: Session = Depends(get_db)
):
    """Get all active integrations for public display."""
    integrations = db.query(Integration).filter(Integration.status != IntegrationStatus.INACTIVE).all()
    return integrations


@router.get("/", response_model=List[IntegrationResponse])
async def get_all_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all integrations (admin only)."""
    integrations = db.query(Integration).order_by(Integration.category, Integration.created_at.desc()).all()
    return integrations


@router.get("/categories")
async def get_integration_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all unique integration categories."""
    categories = db.query(Integration.category).distinct().all()
    return [c[0] for c in categories if c[0]]


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get a single integration by ID."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new integration."""
    integration = Integration(**integration_data.model_dump())
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an integration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    update_data = integration_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)

    db.commit()
    db.refresh(integration)
    return integration


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an integration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    db.delete(integration)
    db.commit()
    return None


# ============== Integration Projects (Aytix Integration Service Clients) ==============
# Bu marketplace loyihalari bilan bog'liq EMAS - alohida integratsiya xizmati mijozlari!

@router.get("/projects", response_model=List[IntegrationProjectResponse])
async def get_integration_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all integration projects (Aytix integration service clients)."""
    projects = db.query(IntegrationProject).order_by(IntegrationProject.created_at.desc()).all()
    return projects


@router.get("/projects/{project_id}", response_model=IntegrationProjectResponse)
async def get_integration_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get a single integration project by ID."""
    project = db.query(IntegrationProject).filter(IntegrationProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Integration project not found")
    return project


@router.post("/projects", response_model=IntegrationProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_integration_project(
    data: IntegrationProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new integration project (client)."""
    project = IntegrationProject(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/projects/{project_id}", response_model=IntegrationProjectResponse)
async def update_integration_project(
    project_id: int,
    data: IntegrationProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an integration project."""
    project = db.query(IntegrationProject).filter(IntegrationProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Integration project not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an integration project."""
    project = db.query(IntegrationProject).filter(IntegrationProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Integration project not found")

    # Check if project has connected integrations
    connected_count = db.query(ConnectedIntegration).filter(
        ConnectedIntegration.integration_project_id == project_id
    ).count()

    if connected_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Bu loyihada {connected_count} ta ulangan integratsiya mavjud. Avval ularni o'chiring."
        )

    db.delete(project)
    db.commit()
    return None


# ============== Connected Integrations (User Configurations) ==============

@router.get("/connected", response_model=List[ConnectedIntegrationResponse])
async def get_connected_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all connected/configured integrations."""
    integrations = db.query(ConnectedIntegration).order_by(ConnectedIntegration.created_at.desc()).all()
    return integrations


@router.post("/connected", response_model=ConnectedIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_connected_integration(
    data: ConnectedIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create/Connect a new integration with configuration."""
    # Check if already exists
    existing = db.query(ConnectedIntegration).filter(
        ConnectedIntegration.integration_id == data.integration_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Integration '{data.integration_id}' is already connected. Use PUT to update."
        )

    integration = ConnectedIntegration(**data.model_dump())
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.put("/connected/{id}", response_model=ConnectedIntegrationResponse)
async def update_connected_integration(
    id: int,
    data: ConnectedIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a connected integration configuration."""
    integration = db.query(ConnectedIntegration).filter(ConnectedIntegration.id == id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Connected integration not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)

    db.commit()
    db.refresh(integration)
    return integration


@router.delete("/connected/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connected_integration(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete/Disconnect an integration."""
    integration = db.query(ConnectedIntegration).filter(ConnectedIntegration.id == id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Connected integration not found")

    db.delete(integration)
    db.commit()
    return None


@router.post("/test", response_model=IntegrationTestResponse)
async def test_integration_connection(
    data: IntegrationTestRequest,
    current_user: User = Depends(get_current_admin)
):
    """Test integration connection with provided credentials."""

    integration_id = data.integration_id
    config = data.config

    try:
        if integration_id == "amocrm":
            return await test_amocrm(config)
        elif integration_id == "zadarma":
            return await test_zadarma(config)
        elif integration_id == "telegram":
            return await test_telegram(config)
        elif integration_id == "payme":
            return IntegrationTestResponse(
                success=True,
                message="Payme konfiguratsiyasi saqlandi. Haqiqiy tekshirish to'lov paytida amalga oshiriladi."
            )
        elif integration_id == "click":
            return IntegrationTestResponse(
                success=True,
                message="Click konfiguratsiyasi saqlandi. Haqiqiy tekshirish to'lov paytida amalga oshiriladi."
            )
        elif integration_id == "google_analytics":
            return IntegrationTestResponse(
                success=True,
                message="Google Analytics Measurement ID saqlandi."
            )
        elif integration_id == "sms_eskiz":
            return await test_eskiz(config)
        else:
            return IntegrationTestResponse(
                success=True,
                message="Konfiguratsiya saqlandi."
            )
    except Exception as e:
        return IntegrationTestResponse(
            success=False,
            message=f"Xatolik: {str(e)}"
        )


# ============== Integration Test Functions ==============

async def test_amocrm(config: dict) -> IntegrationTestResponse:
    """Test AmoCRM connection."""
    subdomain = config.get("subdomain", "").strip()
    client_id = config.get("client_id", "").strip()
    client_secret = config.get("client_secret", "").strip()
    redirect_uri = config.get("redirect_uri", "").strip()
    authorization_code = config.get("authorization_code", "").strip()

    if not all([subdomain, client_id, client_secret, redirect_uri, authorization_code]):
        return IntegrationTestResponse(success=False, message="Barcha majburiy maydonlar to'ldirilishi kerak")

    try:
        async with httpx.AsyncClient() as client:
            # Try to get access token using authorization code
            response = await client.post(
                f"https://{subdomain}.amocrm.ru/oauth2/access_token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return IntegrationTestResponse(
                    success=True,
                    message="AmoCRM bilan ulanish muvaffaqiyatli! Access token olindi."
                )
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("hint", error_data.get("message", "Noma'lum xatolik"))
                return IntegrationTestResponse(
                    success=False,
                    message=f"AmoCRM xatolik: {error_msg}"
                )
    except httpx.TimeoutException:
        return IntegrationTestResponse(success=False, message="AmoCRM serveriga ulanish vaqti tugadi")
    except Exception as e:
        return IntegrationTestResponse(success=False, message=f"Ulanish xatoligi: {str(e)}")


async def test_zadarma(config: dict) -> IntegrationTestResponse:
    """Test Zadarma API connection."""
    api_key = config.get("api_key", "").strip()
    api_secret = config.get("api_secret", "").strip()

    if not api_key or not api_secret:
        return IntegrationTestResponse(success=False, message="API Key va API Secret kiritilishi kerak")

    try:
        # Zadarma API authentication
        method = "/v1/info/balance/"
        params_str = ""

        # Generate signature
        data_to_sign = method + params_str + hashlib.md5(params_str.encode()).hexdigest()
        signature = hmac.new(
            api_secret.encode(),
            data_to_sign.encode(),
            hashlib.sha1
        ).hexdigest()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.zadarma.com{method}",
                headers={
                    "Authorization": f"{api_key}:{signature}"
                },
                timeout=10.0
            )

            data = response.json()
            if data.get("status") == "success":
                balance = data.get("balance", "N/A")
                currency = data.get("currency", "")
                return IntegrationTestResponse(
                    success=True,
                    message=f"Zadarma bilan ulanish muvaffaqiyatli! Balans: {balance} {currency}"
                )
            else:
                return IntegrationTestResponse(
                    success=False,
                    message=f"Zadarma xatolik: {data.get('message', 'Autentifikatsiya xatosi')}"
                )
    except httpx.TimeoutException:
        return IntegrationTestResponse(success=False, message="Zadarma serveriga ulanish vaqti tugadi")
    except Exception as e:
        return IntegrationTestResponse(success=False, message=f"Ulanish xatoligi: {str(e)}")


async def test_telegram(config: dict) -> IntegrationTestResponse:
    """Test Telegram Bot connection."""
    bot_token = config.get("bot_token", "").strip()

    if not bot_token:
        return IntegrationTestResponse(success=False, message="Bot Token kiritilishi kerak")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=10.0
            )

            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                bot_name = bot_info.get("first_name", "Unknown")
                bot_username = bot_info.get("username", "unknown")
                return IntegrationTestResponse(
                    success=True,
                    message=f"Telegram bot bilan ulanish muvaffaqiyatli! Bot: @{bot_username} ({bot_name})"
                )
            else:
                default_msg = "Token noto'g'ri"
                return IntegrationTestResponse(
                    success=False,
                    message=f"Telegram xatolik: {data.get('description', default_msg)}"
                )
    except httpx.TimeoutException:
        return IntegrationTestResponse(success=False, message="Telegram serveriga ulanish vaqti tugadi")
    except Exception as e:
        return IntegrationTestResponse(success=False, message=f"Ulanish xatoligi: {str(e)}")


async def test_eskiz(config: dict) -> IntegrationTestResponse:
    """Test Eskiz SMS connection."""
    email = config.get("email", "").strip()
    password = config.get("password", "").strip()

    if not email or not password:
        return IntegrationTestResponse(success=False, message="Email va Parol kiritilishi kerak")

    try:
        async with httpx.AsyncClient() as client:
            # Get auth token
            response = await client.post(
                "https://notify.eskiz.uz/api/auth/login",
                data={"email": email, "password": password},
                timeout=10.0
            )

            data = response.json()
            if data.get("data", {}).get("token"):
                return IntegrationTestResponse(
                    success=True,
                    message="Eskiz SMS bilan ulanish muvaffaqiyatli!"
                )
            else:
                return IntegrationTestResponse(
                    success=False,
                    message=f"Eskiz xatolik: {data.get('message', 'Autentifikatsiya xatosi')}"
                )
    except httpx.TimeoutException:
        return IntegrationTestResponse(success=False, message="Eskiz serveriga ulanish vaqti tugadi")
    except Exception as e:
        return IntegrationTestResponse(success=False, message=f"Ulanish xatoligi: {str(e)}")
