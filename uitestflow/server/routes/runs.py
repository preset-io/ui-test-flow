"""
Test run management and execution routes.

Handles test execution, monitoring, and result retrieval.
"""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import TestStatus
from ...src.test_runner import TestRunner
from ..database import TestDefinitionModel, TestRunModel, get_db
from ..schemas import (
    MessageResponse,
    TestRunAbortRequest,
    TestRunCreate,
    TestRunListResponse,
    TestRunResponse,
)
from ..websocket import manager as ws_manager


router = APIRouter(prefix="/api/runs", tags=["test-runs"])

# Global test runner instance
test_runner = TestRunner()


async def execute_test_background(
    run_id: UUID,
    test_id: UUID,
    profile: str | None,
    context: dict,
    db_url: str,
):
    """
    Execute test in background and update database with results.

    Args:
        run_id: Test run ID
        test_id: Test definition ID to load from database
        profile: Profile name
        context: Execution context
        db_url: Database URL for creating new session
    """
    from sqlalchemy import select, update

    from ...core.models import ActionType as CoreActionType
    from ...core.models import AuthConfig as CoreAuthConfig
    from ...core.models import BrowserConfig as CoreBrowserConfig
    from ...core.models import EvaluatorConfig as CoreEvaluatorConfig
    from ...core.models import Profile as CoreProfile
    from ...core.models import ProfileExecutionMode
    from ...core.models import TestDefinition as CoreTestDefinition
    from ...core.models import TestStep as CoreTestStep
    from ...src.profile_executor import ProfileExecutor
    from ..database import Profile as ProfileModel
    from ..database import async_session_maker

    # Track whether we started the environment (so we can stop it later)
    started_environment = False
    profile_executor = None

    try:
        # Load test definition from database
        async with async_session_maker() as db:
            result = await db.execute(
                select(TestDefinitionModel).where(TestDefinitionModel.id == test_id)
            )
            test_model = result.scalar_one_or_none()

            if not test_model:
                raise Exception(f"Test definition {test_id} not found")

            # Convert database model to Pydantic model (core.models)
            core_steps = [
                CoreTestStep(
                    name=step["name"],
                    action=CoreActionType(step["action"]),
                    selector=step.get("selector"),
                    value=step.get("value"),
                    url=step.get("url"),
                    timeout=step.get("timeout"),
                    screenshot=step.get("screenshot", False),
                    condition=step.get("condition"),
                )
                for step in test_model.steps
            ]

            core_evaluators = [
                CoreEvaluatorConfig(
                    name=ev["name"],
                    evaluator_type=ev["type"],
                    params={
                        k: v
                        for k, v in {
                            "selector": ev.get("selector"),
                            "expected_value": ev.get("expected_value"),
                            "max_errors": ev.get("max_errors"),
                            "max_warnings": ev.get("max_warnings"),
                            "max_load_time": ev.get("max_load_time"),
                            "max_time": ev.get("max_time"),
                            "pattern": ev.get("pattern"),
                            "threshold": ev.get("threshold"),
                        }.items()
                        if v is not None
                    },
                )
                for ev in test_model.evaluators
            ]

            core_browser_config = None
            if test_model.browser_config:
                core_browser_config = CoreBrowserConfig(**test_model.browser_config)

            core_auth_config = None
            if test_model.auth_config:
                core_auth_config = CoreAuthConfig(**test_model.auth_config)

            test_definition = CoreTestDefinition(
                id=test_model.id,
                name=test_model.name,
                description=test_model.description,
                version=test_model.version,
                url=test_model.url,
                steps=core_steps,
                evaluators=core_evaluators,
                browser_config=core_browser_config,
                auth_config=core_auth_config,
                timeout=test_model.timeout,
                tags=test_model.tags or [],
            )

            # Check if profile needs to be started
            if profile:
                # Load profile from database
                profile_result = await db.execute(
                    select(ProfileModel).where(ProfileModel.id == profile)
                )
                profile_model = profile_result.scalar_one_or_none()

                if profile_model:
                    # Check if environment is not running
                    if profile_model.environment_status != "running":
                        await ws_manager.broadcast_status(
                            run_id, "running", f"Starting environment: {profile_model.name}"
                        )

                        # Convert database profile to core Profile model
                        from ...core.models import BrowserConfig as ProfileBrowserConfig
                        from ...core.models import InitStep

                        core_profile = CoreProfile(
                            id=profile_model.id,
                            name=profile_model.name,
                            description=profile_model.description,
                            base_url=profile_model.base_url,
                            init_steps=[InitStep(**step) for step in profile_model.init_steps]
                            if profile_model.init_steps
                            else [],
                            browser_config=ProfileBrowserConfig(**profile_model.browser_config)
                            if profile_model.browser_config
                            else None,
                            execution_mode=ProfileExecutionMode(profile_model.execution_mode)
                            if profile_model.execution_mode
                            else ProfileExecutionMode.AUTOMATED,
                        )

                        # Start the profile
                        profile_executor = ProfileExecutor()
                        result = await profile_executor.execute_profile(
                            core_profile,
                            execution_mode=ProfileExecutionMode.AUTOMATED,
                            headless=True,
                            with_claude=False,
                        )

                        if result.success:
                            # Update profile status to running
                            await db.execute(
                                update(ProfileModel)
                                .where(ProfileModel.id == profile)
                                .values(environment_status="running")
                            )
                            await db.commit()
                            started_environment = True
                        else:
                            # Environment failed to start
                            error_msg = f"Failed to start environment: {', '.join(result.errors)}"
                            raise Exception(error_msg)

        # Broadcast start status
        await ws_manager.broadcast_status(run_id, "running", "Test execution started")

        # Execute test - pass run_id so screenshots are saved to correct directory
        test_run = await test_runner.run_test(test_definition, profile, context, run_id=run_id)

        # Update database with results
        async with async_session_maker() as db:
            result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
            run_model = result.scalar_one_or_none()

            if run_model:
                run_model.status = test_run.status.value
                run_model.started_at = test_run.started_at
                run_model.completed_at = test_run.completed_at
                run_model.duration_ms = test_run.duration_ms

                # Convert result to dict
                if test_run.result:
                    run_model.result = {
                        "passed": test_run.result.passed,
                        "score": test_run.result.score,
                        "steps_executed": test_run.result.steps_executed,
                        "steps_passed": test_run.result.steps_passed,
                        "steps_failed": test_run.result.steps_failed,
                        "total_duration_ms": test_run.result.total_duration_ms,
                        "error_message": test_run.result.error_message,
                    }

                await db.commit()

        # Broadcast completion
        await ws_manager.broadcast_complete(
            run_id,
            {
                "status": test_run.status.value,
                "passed": test_run.result.passed if test_run.result else False,
                "duration_ms": test_run.duration_ms,
            },
        )

        # Stop environment if we started it
        if started_environment and profile and profile_executor:
            await ws_manager.broadcast_status(run_id, "running", "Stopping environment")
            try:
                await profile_executor.close_session(profile)
                # Update profile status to stopped
                async with async_session_maker() as db:
                    await db.execute(
                        update(ProfileModel)
                        .where(ProfileModel.id == profile)
                        .values(environment_status=None)
                    )
                    await db.commit()
            except Exception as cleanup_error:
                # Log cleanup error but don't fail the test
                print(f"Error stopping environment: {cleanup_error}")

    except Exception as e:
        # Update database with error
        async with async_session_maker() as db:
            result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
            run_model = result.scalar_one_or_none()

            if run_model:
                run_model.status = TestStatus.FAILED.value
                run_model.completed_at = datetime.utcnow()
                run_model.result = {
                    "passed": False,
                    "score": 0.0,
                    "steps_executed": 0,
                    "steps_passed": 0,
                    "steps_failed": 0,
                    "total_duration_ms": 0,
                    "error_message": str(e),
                }
                await db.commit()

        # Broadcast error
        await ws_manager.broadcast_error(run_id, str(e))

        # Stop environment if we started it (cleanup on error)
        if started_environment and profile and profile_executor:
            try:
                await profile_executor.close_session(profile)
                # Update profile status to stopped
                async with async_session_maker() as db:
                    await db.execute(
                        update(ProfileModel)
                        .where(ProfileModel.id == profile)
                        .values(environment_status=None)
                    )
                    await db.commit()
            except Exception as cleanup_error:
                # Log cleanup error but don't fail the test
                print(f"Error stopping environment after test failure: {cleanup_error}")


@router.get("", response_model=TestRunListResponse)
async def list_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    test_id: UUID | None = Query(None, description="Filter by test ID"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List test runs with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        test_id: Filter by test ID
        status: Filter by status
        db: Database session

    Returns:
        List of test runs with pagination info
    """
    # Build query (no auth for now)
    query = select(TestRunModel)

    # Apply filters
    if test_id:
        query = query.where(TestRunModel.test_id == test_id)

    if status:
        query = query.where(TestRunModel.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(TestRunModel.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    runs = result.scalars().all()

    return TestRunListResponse(
        runs=[TestRunResponse.model_validate(run) for run in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TestRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    run_request: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create and execute a test run.

    Args:
        run_request: Test run creation request
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Test run information (execution happens in background)

    Raises:
        HTTPException: If test not found
    """
    # Get test definition (no auth for now)
    result = await db.execute(
        select(TestDefinitionModel).where(TestDefinitionModel.id == run_request.test_id)
    )
    test_def = result.scalar_one_or_none()

    if not test_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {run_request.test_id} not found",
        )

    # Create test run record
    run_id = uuid4()
    run_model = TestRunModel(
        id=run_id,
        test_id=test_def.id,
        test_name=test_def.name,
        org_id=test_def.org_id,  # Use test's org_id
        profile=run_request.profile,
        triggered_by=run_request.triggered_by,
        context=run_request.context,
        status=TestStatus.PENDING.value,
    )

    db.add(run_model)
    await db.commit()
    await db.refresh(run_model)

    # Convert to src test definition (used by TestRunner)
    from ...src.models import ActionType, AuthConfig, BrowserConfig, EvaluatorConfig, TestStep
    from ...src.models import TestDefinition as SrcTestDefinition

    # Parse steps
    steps = []
    for step_data in test_def.steps:
        steps.append(
            TestStep(
                name=step_data["name"],
                action=ActionType(step_data["action"]),
                selector=step_data.get("selector"),
                value=step_data.get("value"),
                url=step_data.get("url"),
                timeout=step_data.get("timeout"),
                screenshot=step_data.get("screenshot", False),
                condition=step_data.get("condition"),
            )
        )

    # Parse evaluators
    evaluators = []
    for eval_data in test_def.evaluators:
        evaluators.append(
            EvaluatorConfig(
                name=eval_data["name"],
                type=eval_data["type"],
                selector=eval_data.get("selector"),
                expected_value=eval_data.get("expected_value"),
                max_errors=eval_data.get("max_errors"),
                max_warnings=eval_data.get("max_warnings"),
                max_load_time=eval_data.get("max_load_time"),
                max_time=eval_data.get("max_time"),
                pattern=eval_data.get("pattern"),
                threshold=eval_data.get("threshold"),
            )
        )

    # Parse browser config - src models use 'type' field
    browser_config = None
    if test_def.browser_config:
        browser_dict = dict(test_def.browser_config)
        browser_config = BrowserConfig(
            type=browser_dict.get("type", "chromium"),
            headless=browser_dict.get("headless", True),
            viewport=browser_dict.get("viewport", {"width": 1920, "height": 1080}),
            device=browser_dict.get("device"),
            locale=browser_dict.get("locale", "en-US"),
            timezone=browser_dict.get("timezone"),
            permissions=browser_dict.get("permissions", []),
            slow_mo=browser_dict.get("slow_mo", 0),
            user_agent=browser_dict.get("user_agent"),
            proxy=browser_dict.get("proxy"),
            ignore_https_errors=browser_dict.get("ignore_https_errors", False),
            accept_downloads=browser_dict.get("accept_downloads", False),
            record_video=browser_dict.get("record_video", False),
        )

    # Parse auth config - src models use 'type' field and 'auth' attribute name
    auth_config = None
    if test_def.auth_config:
        auth_dict = dict(test_def.auth_config)
        # Extract credentials if present
        creds = auth_dict.get("credentials", {})
        auth_config = AuthConfig(
            type=auth_dict.get("type", "none"),
            username=auth_dict.get("username") or creds.get("username"),
            password=auth_dict.get("password") or creds.get("password"),
            token=auth_dict.get("token"),
            provider=auth_dict.get("provider"),
            client_id=auth_dict.get("client_id"),
            client_secret=auth_dict.get("client_secret"),
            headers=auth_dict.get("headers"),
            cookies=auth_dict.get("cookies"),
        )

    src_test_def = SrcTestDefinition(
        id=test_def.id,
        name=test_def.name,
        description=test_def.description,
        version=test_def.version,
        url=test_def.url,
        steps=steps,
        evaluators=evaluators,
        browser_config=browser_config,
        auth=auth_config,
        timeout=test_def.timeout,
        tags=test_def.tags,
    )

    # Execute test in background
    from ..database import DATABASE_URL

    # Just pass the test_id - we'll reload from DB in background task
    background_tasks.add_task(
        execute_test_background,
        run_id,
        test_def.id,  # Pass test_id instead of whole object
        run_request.profile,
        run_request.context,
        DATABASE_URL,
    )

    return TestRunResponse.model_validate(run_model)


@router.get("/{run_id}", response_model=TestRunResponse)
async def get_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a test run by ID.

    Args:
        run_id: Test run ID
        db: Database session

    Returns:
        Test run information

    Raises:
        HTTPException: If run not found
    """
    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {run_id} not found",
        )

    return TestRunResponse.model_validate(run)


@router.post("/{run_id}/abort", response_model=MessageResponse)
async def abort_run(
    run_id: UUID,
    request: TestRunAbortRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Abort a running test.

    Args:
        run_id: Test run ID
        request: Abort request with reason
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If run not found or not running
    """
    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {run_id} not found",
        )

    if run.status not in [TestStatus.PENDING.value, TestStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot abort test run with status: {run.status}",
        )

    reason = request.reason if request else "User requested abort"

    # Update status
    run.status = TestStatus.ABORTED.value
    run.completed_at = datetime.utcnow()
    if run.started_at:
        run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)

    await db.commit()

    # Broadcast abort
    await ws_manager.broadcast_status(run_id, "aborted", reason)

    return MessageResponse(
        message="Test run aborted",
        detail=reason,
    )


@router.delete("/{run_id}", response_model=MessageResponse)
async def delete_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a test run.

    Args:
        run_id: Test run ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If run not found
    """
    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {run_id} not found",
        )

    await db.delete(run)
    await db.commit()

    return MessageResponse(
        message="Test run deleted successfully",
        detail=f"Test run {run_id} has been deleted",
    )


@router.get("/{run_id}/screenshots")
async def get_run_screenshots(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get screenshots for a test run.

    Args:
        run_id: Test run ID
        db: Database session

    Returns:
        List of screenshot URLs/paths
    """
    from pathlib import Path

    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {run_id} not found",
        )

    # Check for screenshots in test_results directory (use absolute path)
    # The test_results dir could be in multiple locations depending on working directory
    base_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root

    # Check both possible locations
    possible_dirs = [
        base_dir / "test_results" / str(run_id) / "screenshots",
        base_dir / "uitestflow" / "ui" / "test_results" / str(run_id) / "screenshots",
    ]

    screenshots_dir = None
    for d in possible_dirs:
        if d.exists():
            screenshots_dir = d
            break
    screenshots = []

    if screenshots_dir and screenshots_dir.exists():
        for screenshot in sorted(screenshots_dir.glob("*.png")):
            screenshots.append({
                "name": screenshot.name,
                "path": str(screenshot),
                "url": f"/api/runs/{run_id}/screenshots/{screenshot.name}",
            })

    return {"run_id": str(run_id), "screenshots": screenshots}


@router.get("/{run_id}/screenshots/{filename}")
async def get_screenshot_file(
    run_id: UUID,
    filename: str,
):
    """
    Serve a screenshot file.

    Args:
        run_id: Test run ID
        filename: Screenshot filename

    Returns:
        Screenshot image file
    """
    from pathlib import Path

    from fastapi.responses import FileResponse

    # Use absolute path to find screenshot - check multiple locations
    base_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root

    possible_paths = [
        base_dir / "test_results" / str(run_id) / "screenshots" / filename,
        base_dir / "uitestflow" / "ui" / "test_results" / str(run_id) / "screenshots" / filename,
    ]

    screenshot_path = None
    for p in possible_paths:
        if p.exists():
            screenshot_path = p
            break

    if not screenshot_path or not screenshot_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot {filename} not found",
        )

    return FileResponse(
        path=str(screenshot_path),
        media_type="image/png",
        filename=filename,
    )


@router.get("/{run_id}/logs")
async def get_run_logs(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get logs for a test run.

    Args:
        run_id: Test run ID
        db: Database session

    Returns:
        Test run logs
    """
    from pathlib import Path

    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {run_id} not found",
        )

    # Check for logs in test_results directory
    logs_dir = Path(f"test_results/{run_id}")
    logs = []

    # Try to read log file if exists
    log_file = logs_dir / "run.log"
    if log_file.exists():
        logs = log_file.read_text().splitlines()

    # Also return run result info as logs
    result_logs = []
    if run.result:
        result_logs.append(f"Status: {run.status}")
        result_logs.append(f"Passed: {run.result.get('passed', False)}")
        result_logs.append(f"Score: {run.result.get('score', 0)}")
        result_logs.append(f"Steps executed: {run.result.get('steps_executed', 0)}")
        result_logs.append(f"Steps passed: {run.result.get('steps_passed', 0)}")
        result_logs.append(f"Steps failed: {run.result.get('steps_failed', 0)}")
        if run.result.get("error_message"):
            result_logs.append(f"Error: {run.result.get('error_message')}")
        result_logs.append(f"Duration: {run.duration_ms}ms")

    return {
        "run_id": str(run_id),
        "logs": logs if logs else result_logs,
        "result": run.result,
    }
