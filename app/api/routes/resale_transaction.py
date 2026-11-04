from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import (
    get_current_user,
    get_resale_transaction_service,
)
from app.schemas.resale_transaction import (
    CreateResaleTransactionRequest,
    PaginatedTransactionsResponse,
    ResaleTransactionResponse,
    TransactionFilterParams,
)
from app.services.resale_transaction_service import ResaleTransactionService

router = APIRouter(prefix="/api/resale-transactions", tags=["Resale Transactions"])


@router.post(
    "/",
    response_model=ResaleTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a resale transaction (Admin only)",
)
async def create_transaction(
    request: CreateResaleTransactionRequest,
    service: Annotated[
        ResaleTransactionService, Depends(get_resale_transaction_service)
    ],
    current_user=Security(get_current_user, scopes=["transaction:create"]),
):
    """
    Record completed resale transaction.
    Marks the listing as 'SOLD' and the vehicle as 'sold'. Restricted to Admin.
    """
    return await service.log_resale_transaction(
        request=request,
        user=current_user,
    )


@router.get(
    "/",
    response_model=PaginatedTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="View resale transaction ledger",
)
async def get_transactions(
    filters: Annotated[TransactionFilterParams, Query()],
    service: Annotated[
        ResaleTransactionService, Depends(get_resale_transaction_service)
    ],
    current_user=Security(get_current_user, scopes=["transaction:read"]),
):
    """
    View resale transactions.
    Admin sees the full system ledger; customers see their purchases and sales.
    """
    return await service.get_transactions(
        filters=filters,
        user=current_user,
    )

