"""
MCP-specific API routes for UITestFlow.

Provides REST API endpoints for test generation, guided execution,
and MCP server management.
"""

import asyncio
import logging
from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import APIKeyError, GenerationConfig, LLMError
from uitestflow.src.browser_manager import BrowserSessionManager
from uitestflow.src.enhanced_test_runner import EnhancedTestRunner
from uitestflow.src.models import BrowserConfig, TestDefinition
from uitestflow.src.test_parser import YAMLTestParser

from .auth import get_api_key_from_header
from .database import TestDefinitionModel, TestRunModel, get_db


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class GenerateTestRequest(BaseModel):
    """Request schema for test generation."""

    description: str = Field(..., min_length=1, description="Natural language test description")
    base_url: str | None = Field(None, description="Base URL for the test")
    model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model to use",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model temperature",
    )
    save: bool = Field(
        default=True,
        description="Whether to save test to database",
    )


class GenerateTestResponse(BaseModel):
    """Response schema for test generation."""

    test_id: UUID = Field(..., description="Generated test ID")
    test_definition: dict[str, Any] = Field(..., description="Test definition")
    generation_time_ms: int = Field(..., description="Time taken to generate")
    model_used: str = Field(..., description="Model used for generation")


class ExecuteTestRequest(BaseModel):
    """Request schema for test execution."""

    test_id: UUID | None = Field(None, description="ID of saved test to execute")
    test_definition: dict[str, Any] | None = Field(None, description="Inline test definition")
    with_claude: bool = Field(default=True, description="Enable Claude guidance")
    model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model for guidance",
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")


class ExecuteTestResponse(BaseModel):
    """Response schema for test execution."""

    run_id: UUID = Field(..., description="Test run ID for tracking")
    status: str = Field(..., description="Execution status")
    message: str = Field(..., description="Status message")


class MCPStatusResponse(BaseModel):
    """Response schema for MCP status."""

    mcp_enabled: bool = Field(..., description="Whether MCP is enabled")
    server_available: bool = Field(..., description="Whether MCP server is available")
    api_key_configured: bool = Field(..., description="Whether API key is configured")
    available_tools: list[str] = Field(..., description="List of available MCP tools")
    default_model: str = Field(..., description="Default Claude model")
    transport: str = Field(..., description="MCP transport protocol")


class FeedbackItem(BaseModel):
    """Feedback item for a test step."""

    step_index: int
    step_name: str
    guidance: str | None = None
    selector_adapted: bool = False
    original_selector: str | None = None
    adapted_selector: str | None = None
    recovery_attempted: bool = False
    recovery_action: str | None = None
    success: bool


class FeedbackResponse(BaseModel):
    """Response schema for Claude feedback."""

    run_id: UUID
    test_name: str
    total_steps: int
    feedback_items: list[FeedbackItem]
    overall_guidance: str | None = None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/generate", response_model=GenerateTestResponse)
async def generate_test(
    request: GenerateTestRequest,
    api_key: str = Depends(get_api_key_from_header),
    db: AsyncSession = Depends(get_db),
) -> GenerateTestResponse:
    """
    Generate a test definition from natural language description.

    Uses Claude AI to convert natural language into a structured test definition.

    Args:
        request: Test generation request
        api_key: Anthropic API key from header
        db: Database session

    Returns:
        Generated test definition with ID

    Raises:
        HTTPException: If generation fails
    """
    import time

    start_time = time.time()

    # Create generator
    config = GenerationConfig(
        model=request.model,
        temperature=request.temperature,
        max_tokens=4000,
    )

    try:
        generator = ClaudeTestGenerator(api_key=api_key, config=config)
    except APIKeyError as e:
        logger.error("API key error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Generate test
    try:
        test_def = await generator.generate_test(
            description=request.description,
            base_url=request.base_url,
        )
    except LLMError as e:
        logger.error("LLM error during generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Test generation failed: {e!s}",
        )
    except Exception as e:
        logger.error("Unexpected error during generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {e!s}",
        )

    generation_time_ms = int((time.time() - start_time) * 1000)

    # Save to database if requested
    test_id = uuid4()
    if request.save:
        try:
            test_model = TestDefinitionModel(
                id=test_id,
                org_id=uuid4(),  # TODO: Get from authenticated user
                name=test_def.name,
                description=test_def.description,
                version=test_def.version,
                url=test_def.url,
                steps=[asdict(step) for step in test_def.steps],
                evaluators=[asdict(ev) for ev in test_def.evaluators],
                browser_config=asdict(test_def.browser_config) if test_def.browser_config else {},
                auth_config=asdict(test_def.auth) if test_def.auth else {},
                timeout=test_def.timeout,
                retry_config=asdict(test_def.retry_config) if test_def.retry_config else {},
                tags=test_def.tags or [],
            )
            db.add(test_model)
            await db.commit()
            logger.info("Test definition saved with ID: %s", test_id)
        except Exception as e:
            logger.error("Error saving test to database: %s", e)
            await db.rollback()
            # Continue anyway, return the test definition

    return GenerateTestResponse(
        test_id=test_id,
        test_definition=asdict(test_def),
        generation_time_ms=generation_time_ms,
        model_used=request.model,
    )


@router.post("/execute", response_model=ExecuteTestResponse)
async def execute_test(
    request: ExecuteTestRequest,
    api_key: str = Depends(get_api_key_from_header),
    db: AsyncSession = Depends(get_db),
) -> ExecuteTestResponse:
    """
    Execute a test with optional Claude guidance.

    Runs a test (either from database or inline definition) with optional
    real-time Claude guidance for adaptive execution.

    Args:
        request: Test execution request
        api_key: Anthropic API key from header
        db: Database session

    Returns:
        Test run ID for tracking progress

    Raises:
        HTTPException: If execution setup fails
    """
    # Get test definition
    test_def: TestDefinition | None = None

    if request.test_id:
        # Load from database
        from sqlalchemy import select

        result = await db.execute(
            select(TestDefinitionModel).where(TestDefinitionModel.id == request.test_id)
        )
        test_model = result.scalar_one_or_none()

        if not test_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test definition not found: {request.test_id}",
            )

        # Convert to TestDefinition
        parser = YAMLTestParser()
        import yaml

        test_yaml = yaml.dump({
            "name": test_model.name,
            "description": test_model.description,
            "version": test_model.version,
            "url": test_model.url,
            "steps": test_model.steps,
            "evaluators": test_model.evaluators,
            "browser_config": test_model.browser_config,
            "timeout": test_model.timeout,
        })
        test_def = parser.parse_string(test_yaml)

    elif request.test_definition:
        # Parse inline definition
        parser = YAMLTestParser()
        import yaml

        test_yaml = yaml.dump(request.test_definition)
        test_def = parser.parse_string(test_yaml)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either test_id or test_definition must be provided",
        )

    # Create run ID
    run_id = uuid4()

    # Queue execution in background (async task)
    asyncio.create_task(
        _execute_test_background(
            run_id=run_id,
            test_def=test_def,
            with_claude=request.with_claude,
            claude_model=request.model,
            api_key=api_key if request.with_claude else None,
            headless=request.headless,
        )
    )

    return ExecuteTestResponse(
        run_id=run_id,
        status="queued",
        message="Test execution queued. Use WebSocket to monitor progress.",
    )


@router.get("/status", response_model=MCPStatusResponse)
async def get_mcp_status(
    api_key: str | None = Depends(get_api_key_from_header),
) -> MCPStatusResponse:
    """
    Get MCP server status and configuration.

    Returns information about MCP availability, configured tools, and settings.

    Args:
        api_key: Optional API key from header

    Returns:
        MCP status information
    """
    # Check if MCP package is available
    try:
        import mcp  # noqa: F401

        mcp_enabled = True
    except ImportError:
        mcp_enabled = False

    # List of available tools
    available_tools = [
        "navigate",
        "click",
        "fill",
        "wait_for",
        "screenshot",
        "get_page_state",
        "get_text",
        "evaluate_javascript",
        "get_console_logs",
        "select",
    ]

    return MCPStatusResponse(
        mcp_enabled=mcp_enabled,
        server_available=mcp_enabled,
        api_key_configured=api_key is not None,
        available_tools=available_tools,
        default_model="claude-3-5-haiku-20241022",
        transport="stdio",
    )


@router.get("/feedback/{run_id}", response_model=FeedbackResponse)
async def get_feedback(
    run_id: UUID,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """
    Get Claude feedback for a test run.

    Retrieves guidance, selector adaptations, and recovery attempts for each step.

    Args:
        run_id: Test run ID
        page: Page number for pagination
        page_size: Items per page
        db: Database session

    Returns:
        Claude feedback for the test run

    Raises:
        HTTPException: If run not found
    """
    from sqlalchemy import select

    # Get test run
    result = await db.execute(select(TestRunModel).where(TestRunModel.id == run_id))
    test_run = result.scalar_one_or_none()

    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run not found: {run_id}",
        )

    # Extract feedback from step results
    # This is a placeholder - actual implementation would parse metadata
    feedback_items = []
    step_results = test_run.step_results or []

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    for i, step_result in enumerate(step_results[start_idx:end_idx], start=start_idx):
        feedback_items.append(
            FeedbackItem(
                step_index=i,
                step_name=step_result.get("step_name", f"Step {i + 1}"),
                guidance=step_result.get("claude_guidance"),
                selector_adapted=step_result.get("selector_adapted", False),
                original_selector=step_result.get("original_selector"),
                adapted_selector=step_result.get("adapted_selector"),
                recovery_attempted=step_result.get("recovery_attempted", False),
                recovery_action=step_result.get("recovery_action"),
                success=step_result.get("success", False),
            )
        )

    return FeedbackResponse(
        run_id=run_id,
        test_name=test_run.test_name or "Unknown",
        total_steps=len(step_results),
        feedback_items=feedback_items,
        overall_guidance=test_run.metadata.get("overall_guidance") if test_run.metadata else None,
    )


# ============================================================================
# Background Tasks
# ============================================================================


async def _execute_test_background(
    run_id: UUID,
    test_def: TestDefinition,
    with_claude: bool,
    claude_model: str,
    api_key: str | None,
    headless: bool,
) -> None:
    """
    Execute test in background task.

    Args:
        run_id: Test run ID
        test_def: Test definition to execute
        with_claude: Whether to use Claude guidance
        claude_model: Claude model to use
        api_key: Anthropic API key
        headless: Run browser in headless mode
    """
    from .websocket import manager

    try:
        # Notify start
        await manager.send_message(
            run_id,
            {
                "type": "test_started",
                "run_id": str(run_id),
                "test_name": test_def.name,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Create browser session
        browser_config = BrowserConfig(headless=headless)
        session_manager = BrowserSessionManager(browser_config)

        # Create Claude client if needed
        claude_client = None
        if with_claude and api_key:
            config = GenerationConfig(model=claude_model)
            claude_client = ClaudeTestGenerator(api_key=api_key, config=config)

        # Create runner
        if claude_client:
            runner = EnhancedTestRunner(
                session_manager=session_manager,
                claude_client=claude_client,
            )
        else:
            from uitestflow.src.test_runner import TestRunner

            runner = TestRunner(session_manager=session_manager)

        # Execute test
        result = await runner.run_test(test_def)

        # Notify completion
        await manager.send_message(
            run_id,
            {
                "type": "test_completed",
                "run_id": str(run_id),
                "status": result.status,
                "passed": result.passed,
                "duration_ms": result.duration_ms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Cleanup
        await session_manager.cleanup()

    except Exception as e:
        logger.error("Error executing test %s: %s", run_id, e)
        await manager.send_message(
            run_id,
            {
                "type": "test_error",
                "run_id": str(run_id),
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
