"""
Test definition CRUD routes.

Handles creation, reading, updating, and deletion of test definitions.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import TestDefinitionModel, get_db


# Default org_id for unauthenticated requests
DEFAULT_ORG_ID = UUID("0c8809d8-1604-486b-80cd-a77b4a7a6630")
from ..schemas import (
    MessageResponse,
    TestDefinitionCreate,
    TestDefinitionListResponse,
    TestDefinitionResponse,
    TestDefinitionUpdate,
)


router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.get("", response_model=TestDefinitionListResponse)
async def list_tests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tags: str | None = Query(None, description="Filter by tags (comma-separated)"),
    search: str | None = Query(None, description="Search in name and description"),
    db: AsyncSession = Depends(get_db),
):
    """
    List test definitions with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        tags: Filter by tags (comma-separated)
        search: Search query for name/description
        db: Database session

    Returns:
        List of test definitions with pagination info
    """
    # Build query (no auth for now)
    query = select(TestDefinitionModel)

    # Apply filters
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query = query.where(TestDefinitionModel.tags.op("&&")(tag_list))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (TestDefinitionModel.name.ilike(search_pattern))
            | (TestDefinitionModel.description.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(TestDefinitionModel.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    tests = result.scalars().all()

    return TestDefinitionListResponse(
        tests=[TestDefinitionResponse.model_validate(test) for test in tests],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TestDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    test: TestDefinitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new test definition.

    Args:
        test: Test definition data
        db: Database session

    Returns:
        Created test definition
    """
    test_id = uuid4()

    # Convert steps to dict format
    steps_dict = [step.model_dump() for step in test.steps]

    # Convert evaluators to dict format
    evaluators_dict = [evaluator.model_dump(by_alias=True) for evaluator in test.evaluators]

    test_model = TestDefinitionModel(
        id=test_id,
        org_id=DEFAULT_ORG_ID,
        name=test.name,
        description=test.description,
        version=test.version,
        url=test.url,
        steps=steps_dict,
        evaluators=evaluators_dict,
        browser_config=test.browser_config or {},
        auth_config=test.auth_config or {},
        timeout=test.timeout,
        retry_config=test.retry_config or {},
        tags=test.tags,
        created_by=None,
    )

    db.add(test_model)
    await db.commit()
    await db.refresh(test_model)

    return TestDefinitionResponse.model_validate(test_model)


@router.get("/{test_id}", response_model=TestDefinitionResponse)
async def get_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a test definition by ID.

    Args:
        test_id: Test definition ID
        db: Database session

    Returns:
        Test definition

    Raises:
        HTTPException: If test not found
    """
    result = await db.execute(select(TestDefinitionModel).where(TestDefinitionModel.id == test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found",
        )

    return TestDefinitionResponse.model_validate(test)


@router.put("/{test_id}", response_model=TestDefinitionResponse)
async def update_test(
    test_id: UUID,
    test_update: TestDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a test definition.

    Args:
        test_id: Test definition ID
        test_update: Updated test data
        db: Database session

    Returns:
        Updated test definition

    Raises:
        HTTPException: If test not found
    """
    result = await db.execute(select(TestDefinitionModel).where(TestDefinitionModel.id == test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found",
        )

    # Update fields
    update_data = test_update.model_dump(exclude_unset=True)

    # Handle special fields
    if update_data.get("steps"):
        update_data["steps"] = [step.model_dump() for step in test_update.steps]

    if update_data.get("evaluators"):
        update_data["evaluators"] = [
            evaluator.model_dump(by_alias=True) for evaluator in test_update.evaluators
        ]

    for field, value in update_data.items():
        setattr(test, field, value)

    await db.commit()
    await db.refresh(test)

    return TestDefinitionResponse.model_validate(test)


@router.delete("/{test_id}", response_model=MessageResponse)
async def delete_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a test definition.

    Args:
        test_id: Test definition ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If test not found
    """
    result = await db.execute(select(TestDefinitionModel).where(TestDefinitionModel.id == test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found",
        )

    await db.delete(test)
    await db.commit()

    return MessageResponse(
        message="Test deleted successfully",
        detail=f"Test {test_id} has been deleted",
    )
