"""
Profile management routes.

Handles environment configuration profiles.
"""

import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uitestflow.src.profile_executor import ProfileExecutor

from ..ai_profile_generator import AIProfileGenerator
from ..ai_test_generator import AITestGenerator, CoverageLevel, SiteCrawler
from ..database import Profile, get_db
from ..schemas import (
    AIProfileGenerateRequest,
    AIProfileGenerateResponse,
    AITestGenerateRequest,
    AITestGenerateResponse,
    ProfileCreate,
    ProfileListResponse,
    ProfileResponse,
    ProfileStartRequest,
    ProfileStartResponse,
    ProfileTestResponse,
    ProfileUpdate,
)


router = APIRouter(prefix="/api/profiles", tags=["profiles"])

# Global executor instance for session management
_executor = ProfileExecutor()


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    profile_type: str | None = None,
    execution_mode: str | None = None,
    tags: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all profiles with optional filtering.

    Args:
        profile_type: Filter by profile type (environment, workflow, custom)
        execution_mode: Filter by execution mode (automated, manual, hybrid)
        tags: Comma-separated list of tags to filter by
        db: Database session

    Returns:
        List of profiles
    """
    # Build query with filters
    query = select(Profile)

    if profile_type:
        query = query.where(Profile.profile_type == profile_type)

    if execution_mode:
        query = query.where(Profile.execution_mode == execution_mode)

    # Execute query
    result = await db.execute(query)
    profiles = result.scalars().all()

    # Filter by tags if provided (post-query since JSON filtering is complex)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        profiles = [p for p in profiles if any(tag in p.tags for tag in tag_list)]

    return ProfileListResponse(
        profiles=[ProfileResponse.model_validate(profile) for profile in profiles],
        total=len(profiles),
    )


# ====================================================================================
# Browser Session Management Endpoints
# ====================================================================================
# NOTE: These must come BEFORE /{profile_id} routes to avoid path conflicts


@router.get("/sessions")
async def list_browser_sessions():
    """List all active browser sessions."""
    sessions = _executor.browser_manager.get_session_info()
    return {"sessions": sessions, "count": len(sessions)}


@router.delete("/sessions/{session_id}")
async def close_browser_session(session_id: str):
    """Close a specific browser session."""
    await _executor.browser_manager.cleanup_session(session_id)
    return {"success": True, "message": f"Session {session_id} closed"}


@router.delete("/sessions")
async def close_all_browser_sessions():
    """Close all browser sessions."""
    await _executor.browser_manager.cleanup_all_sessions()
    return {"success": True, "message": "All sessions closed"}


@router.post("/sessions/cleanup")
async def cleanup_dead_sessions():
    """Cleanup dead/orphaned browser sessions."""
    count = await _executor.browser_manager.cleanup_dead_sessions()
    return {"success": True, "cleaned_up": count, "message": f"Cleaned up {count} dead sessions"}


# ====================================================================================
# Profile CRUD Endpoints
# ====================================================================================


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a profile by ID.

    Args:
        profile_id: Profile ID
        db: Database session

    Returns:
        Profile information

    Raises:
        HTTPException: If profile not found
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    return ProfileResponse.model_validate(profile)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new profile.

    Args:
        profile_data: Profile data
        db: Database session

    Returns:
        Created profile

    Raises:
        HTTPException: If profile already exists
    """
    import uuid

    # Generate profile ID if not provided
    profile_id = profile_data.id or (
        str(uuid.uuid4())[:8] + "-" + profile_data.name.lower().replace(" ", "-")
    )

    # Check if profile already exists
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profile {profile_id} already exists",
        )

    # Generate org_id if not provided
    org_id = profile_data.org_id or uuid.uuid4()

    # Create profile with all new fields
    profile = Profile(
        id=profile_id,
        name=profile_data.name,
        org_id=org_id,
        description=profile_data.description,
        profile_type=profile_data.profile_type,
        execution_mode=profile_data.execution_mode,
        base_url=profile_data.base_url,
        init_steps=profile_data.init_steps,
        auth_config=profile_data.auth_config,
        browser_config=profile_data.browser_config,
        llm_config=profile_data.llm_config,
        notification_config=profile_data.notification_config,
        tags=profile_data.tags,
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return ProfileResponse.model_validate(profile)


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a profile.

    Args:
        profile_id: Profile ID
        profile_data: Updated profile data
        db: Database session

    Returns:
        Updated profile

    Raises:
        HTTPException: If profile not found
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # Update fields if provided
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse.model_validate(profile)


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a profile.

    Args:
        profile_id: Profile ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If profile not found
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    await db.delete(profile)
    await db.commit()

    return {"message": f"Profile {profile_id} deleted successfully"}


@router.post("/{profile_id}/start", response_model=ProfileStartResponse)
async def start_profile(
    profile_id: str,
    start_request: ProfileStartRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a profile by executing its initialization steps.

    This endpoint:
    1. Loads the profile configuration
    2. Initializes browser with browser_config
    3. Executes init_steps in sequence
    4. Returns a browser session ready for testing

    Args:
        profile_id: Profile ID
        start_request: Optional overrides for execution mode and headless setting
        db: Database session

    Returns:
        ProfileStartResponse with session info

    Raises:
        HTTPException: If profile not found
    """
    from uitestflow.core.models import Profile as CoreProfile

    # Get profile from database
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    db_profile = result.scalar_one_or_none()

    if not db_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # Convert DB profile to core Profile model
    core_profile = CoreProfile(
        id=db_profile.id,
        name=db_profile.name,
        description=db_profile.description,
        profile_type=db_profile.profile_type,
        execution_mode=db_profile.execution_mode,
        base_url=db_profile.base_url,
        init_steps=db_profile.init_steps or [],
        auth_config=db_profile.auth_config or {},
        browser_config=db_profile.browser_config or {},
        llm_config=db_profile.llm_config or {},
        notification_config=db_profile.notification_config or {},
        tags=db_profile.tags or [],
    )

    # Execute profile initialization (use global executor to track sessions)
    exec_result = await _executor.execute_profile(
        profile=core_profile,
        execution_mode=start_request.execution_mode if start_request else None,
        headless=start_request.headless if start_request else None,
        with_claude=start_request.with_claude if start_request else True,
    )

    return ProfileStartResponse(
        success=exec_result.success,
        session_id=core_profile.id if exec_result.session else None,
        steps_executed=exec_result.steps_executed,
        errors=exec_result.errors,
        message=exec_result.message,
    )


@router.post("/{profile_id}/test", response_model=ProfileTestResponse)
async def test_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Test connectivity for a profile.

    Makes an HTTP request to the profile's base_url to verify:
    - Network connectivity
    - URL accessibility
    - Response time

    Args:
        profile_id: Profile ID
        db: Database session

    Returns:
        ProfileTestResponse with test results

    Raises:
        HTTPException: If profile not found
    """
    # Get profile from database
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # Test connectivity
    start_time = time.time()

    try:
        # Build auth headers based on auth type
        headers = {}
        auth_config = profile.auth_config or {}
        auth_type = auth_config.get("type", "none")

        if auth_type == "bearer":
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            api_key = auth_config.get("api_key")
            api_key_header = auth_config.get("api_key_header", "X-API-Key")
            api_key_prefix = auth_config.get("api_key_prefix")
            if api_key:
                if api_key_prefix:
                    headers[api_key_header] = f"{api_key_prefix} {api_key}"
                else:
                    headers[api_key_header] = api_key
        elif auth_type == "basic":
            import base64

            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        # Add any custom headers
        custom_headers = auth_config.get("custom_headers", {})
        headers.update(custom_headers)

        # Create HTTP client with timeout
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Make request to base URL with auth headers
            response = await client.get(profile.base_url, headers=headers)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Check if response is successful (2xx or 3xx status codes)
            if response.status_code < 400:
                return ProfileTestResponse(
                    success=True,
                    latency_ms=latency_ms,
                    error=None,
                )
            return ProfileTestResponse(
                success=False,
                latency_ms=latency_ms,
                error=f"HTTP {response.status_code}: {response.reason_phrase}",
            )

    except httpx.TimeoutException:
        latency_ms = int((time.time() - start_time) * 1000)
        return ProfileTestResponse(
            success=False,
            latency_ms=latency_ms,
            error="Connection timeout (10 seconds)",
        )
    except httpx.ConnectError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ProfileTestResponse(
            success=False,
            latency_ms=latency_ms,
            error=f"Connection failed: {e!s}",
        )
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ProfileTestResponse(
            success=False,
            latency_ms=latency_ms,
            error=f"Test failed: {e!s}",
        )


@router.post("/generate", response_model=AIProfileGenerateResponse)
async def generate_profiles_with_ai(
    request: AIProfileGenerateRequest,
):
    """
    Generate profile configurations using AI from natural language description.

    This endpoint uses AI (Claude, GPT, etc.) to automatically create profile configurations
    from natural language descriptions. You can describe multiple profiles in one request.

    Example request:
    {
        "description": "Create two profiles for Superset running on localhost:9001.
                       One pre-auth profile that just navigates to the login page,
                       and one authenticated profile that logs in with admin/admin credentials.",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "api_key_env": "ANTHROPIC_API_KEY"
    }

    Args:
        request: AI generation request with description and provider settings

    Returns:
        AIProfileGenerateResponse with generated profile configurations
    """
    generator = AIProfileGenerator(
        provider=request.provider, model=request.model, api_key_env=request.api_key_env
    )

    result = await generator.generate_profiles(request.description)

    return AIProfileGenerateResponse(
        success=result["success"],
        profiles=result["profiles"],
        message=result["message"],
        reasoning=result.get("reasoning"),
    )


@router.post("/generate-tests", response_model=AITestGenerateResponse)
async def generate_tests_from_profile(request: AITestGenerateRequest):
    """
    Generate comprehensive tests from an initialized environment profile.

    Uses AI to analyze the environment and create tests based on:
    - Site crawl data from active browser session
    - Coverage level (smoke, canary, medium, deep)
    - Industry best practices for each coverage level

    Requires the profile to be started first to have an active browser session.
    """
    # Validate coverage level
    try:
        coverage_level = CoverageLevel(request.coverage_level.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coverage level: {request.coverage_level}. Must be one of: smoke, canary, medium, deep",
        )

    # Get the browser session for this profile
    session = None
    for active_session in _executor.browser_manager.get_session_info():
        if request.profile_id in active_session.get("session_id", ""):
            # Find the actual session object
            for sess_id, sess in _executor.browser_manager._active_sessions.items():
                if request.profile_id in sess_id:
                    session = sess
                    break
            break

    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active browser session found for profile {request.profile_id}. "
            "Please start the profile first using the Start button with manual or hybrid mode.",
        )

    # Check if session is still alive
    if not await session.is_alive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Browser session for profile {request.profile_id} is no longer active. "
            "Please restart the profile.",
        )

    try:
        # Crawl the site using the active session
        crawler = SiteCrawler(session.page, max_depth=request.crawl_depth)
        site_data = await crawler.crawl()

        # Get profile info for context
        profile_info = {
            "name": request.profile_id,
            "base_url": session.page.url,
            "profile_type": "environment",
        }

        # Generate tests using AI
        generator = AITestGenerator(
            provider=request.provider, model=request.model, api_key_env=request.api_key_env
        )

        result = await generator.generate_tests(site_data, coverage_level, profile_info)

        return AITestGenerateResponse(
            success=result["success"],
            tests=result.get("tests", []),
            count=result.get("count", 0),
            coverage_level=result.get("coverage_level", coverage_level.value),
            site_data=site_data,
            message=result["message"],
            reasoning=result.get("reasoning"),
        )

    except Exception as e:
        logger.error("Error generating tests from profile: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {e!s}",
        )
