from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.resale_transaction import ResaleTransaction
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.interfaces.resale_transaction_interface import (
    ResaleTransactionInterface,
)
from app.repositories.interfaces.user_interface import UserInterface
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.resale_transaction import (
    CreateResaleTransactionRequest,
    ResaleTransactionPatchRequest,
    TransactionFilterParams,
)
from app.services.email_service import EmailService


class ResaleTransactionService:
    def __init__(
        self,
        session: AsyncSession,
        resale_transaction_repository: ResaleTransactionInterface,
        vehicle_listing_repository: VehicleListingInterface,
        vehicle_repository: VehicleInterface,
        user_repository: UserInterface,
        email_service: EmailService,
    ):
        self.session = session
        self.resale_transaction_repository = resale_transaction_repository
        self.vehicle_listing_repository = vehicle_listing_repository
        self.vehicle_repository = vehicle_repository
        self.user_repository = user_repository
        self.email_service = email_service

    def _resale_transaction_email_payload(
        self,
        buyer: User,
        seller: User,
        vehicle: Vehicle,
        transaction: ResaleTransaction,
        consultant: User | None = None,
    ) -> dict:
        delivery_str = (
            transaction.delivery_date.strftime("%Y-%m-%d %H:%M")
            if isinstance(transaction.delivery_date, datetime)
            else (
                str(transaction.delivery_date) if transaction.delivery_date else "To be scheduled"
            )
        )
        notes_str = transaction.delivery_notes or "Standard handover"

        messages = [
            {
                "From": {
                    "Email": "visowmani.123@gmail.com",
                    "Name": "Car Resale Consultancy API",
                },
                "To": [
                    {
                        "Email": buyer.email,
                        "Name": buyer.name,
                    }
                ],
                "Subject": f"Vehicle Purchase Confirmation - {vehicle.brand} {vehicle.model} ({vehicle.registration_number})",
                "HTMLPart": f"""
                    <h2>Congratulations {buyer.name}!</h2>
                    <p>Your vehicle purchase has been successfully processed and confirmed.</p>
                    <p><strong>Transaction Summary:</strong></p>
                    <ul>
                        <li><strong>Transaction ID:</strong> #{transaction.id}</li>
                        <li><strong>Vehicle:</strong> {vehicle.brand} {vehicle.model} ({vehicle.manufacturing_year})</li>
                        <li><strong>Registration Number:</strong> {vehicle.registration_number}</li>
                        <li><strong>Final Sale Price:</strong> Rs. {transaction.final_price:,.2f}</li>
                        <li><strong>Scheduled Delivery:</strong> {delivery_str}</li>
                        <li><strong>Delivery Notes:</strong> {notes_str}</li>
                    </ul>
                    <p>Thank you for choosing our platform for your car purchase!</p>
                    <br/>
                    <p>Best regards,<br/>Auto Consultancy Team</p>
                """,
            },
            {
                "From": {
                    "Email": "visowmani.123@gmail.com",
                    "Name": "Car Resale Consultancy API",
                },
                "To": [
                    {
                        "Email": seller.email,
                        "Name": seller.name,
                    }
                ],
                "Subject": f"Vehicle Sale Confirmed - {vehicle.brand} {vehicle.model} ({vehicle.registration_number})",
                "HTMLPart": f"""
                    <h2>Good News {seller.name}!</h2>
                    <p>Your vehicle has been successfully sold through our consultancy platform.</p>
                    <p><strong>Sale Summary:</strong></p>
                    <ul>
                        <li><strong>Transaction ID:</strong> #{transaction.id}</li>
                        <li><strong>Vehicle:</strong> {vehicle.brand} {vehicle.model} ({vehicle.manufacturing_year})</li>
                        <li><strong>Registration Number:</strong> {vehicle.registration_number}</li>
                        <li><strong>Final Sale Price:</strong> Rs. {transaction.final_price:,.2f}</li>
                    </ul>
                    <p>Our finance and handover team will contact you regarding payout processing and RC transfer formalities.</p>
                    <br/>
                    <p>Best regards,<br/>Auto Consultancy Team</p>
                """,
            },
        ]

        if consultant:
            messages.append(
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": consultant.email,
                            "Name": consultant.name,
                        }
                    ],
                    "Subject": f"Deal Closed - Vehicle {vehicle.registration_number} (Transaction #{transaction.id})",
                    "HTMLPart": f"""
                        <h2>Resale Deal Finalized</h2>
                        <p>Hello {consultant.name},</p>
                        <p>The transaction for vehicle <strong>{vehicle.brand} {vehicle.model}</strong> ({vehicle.registration_number}) has been completed successfully.</p>
                        <ul>
                            <li><strong>Transaction ID:</strong> #{transaction.id}</li>
                            <li><strong>Final Price:</strong> Rs. {transaction.final_price:,.2f}</li>
                            <li><strong>Buyer:</strong> {buyer.name} ({buyer.email})</li>
                            <li><strong>Seller:</strong> {seller.name} ({seller.email})</li>
                        </ul>
                        <br/>
                        <p>Best regards,<br/>Auto Consultancy Management</p>
                    """,
                }
            )

        return {"Messages": messages}

    def _resale_cancellation_email_payload(
        self,
        buyer: User,
        seller: User,
        vehicle: Vehicle,
        transaction: ResaleTransaction,
    ) -> dict:
        return {
            "Messages": [
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": buyer.email,
                            "Name": buyer.name,
                        }
                    ],
                    "Subject": f"Resale Transaction Cancelled - {vehicle.registration_number}",
                    "HTMLPart": f"""
                        <h2>Transaction Cancelled</h2>
                        <p>Hello {buyer.name},</p>
                        <p>Resale transaction #{transaction.id} for vehicle <strong>{vehicle.brand} {vehicle.model}</strong> (Reg No: <strong>{vehicle.registration_number}</strong>) has been cancelled.</p>
                        <p>If you have already processed payment, refund procedures have been initiated.</p>
                        <br/>
                        <p>Best regards,<br/>Auto Consultancy Team</p>
                    """,
                },
                {
                    "From": {
                        "Email": "visowmani.123@gmail.com",
                        "Name": "Car Resale Consultancy API",
                    },
                    "To": [
                        {
                            "Email": seller.email,
                            "Name": seller.name,
                        }
                    ],
                    "Subject": f"Resale Transaction Cancelled - {vehicle.registration_number}",
                    "HTMLPart": f"""
                        <h2>Transaction Cancelled</h2>
                        <p>Hello {seller.name},</p>
                        <p>Resale transaction #{transaction.id} for vehicle <strong>{vehicle.brand} {vehicle.model}</strong> (Reg No: <strong>{vehicle.registration_number}</strong>) has been cancelled.</p>
                        <p>Your vehicle has been restored to active status on our listing platform.</p>
                        <br/>
                        <p>Best regards,<br/>Auto Consultancy Team</p>
                    """,
                },
            ]
        }

    async def log_resale_transaction(
        self, request: CreateResaleTransactionRequest, user: User
    ) -> ResaleTransaction:
        """
        Records a completed resale deal and executes atomic multi-table state transitions:
        - Validates listing is ACTIVE, vehicle is active, buyer is active and distinct from seller.
        - Persists ResaleTransaction audit record.
        - Atomically transitions vehicle_listing to 'SOLD' and vehicle to 'sold'.
        - Dispatches confirmation emails to buyer, seller, and consultant outside DB transaction.
        """
        if user.role != "ADMIN":
            raise ForbiddenException("Only administrators can record resale transactions.")

        email_payload = None

        async with self.session.begin():
            listing = await self.vehicle_listing_repository.get_listing_by_id(request.listing_id)
            if not listing:
                raise NotFoundException("Vehicle listing not found.")

            if listing.status != "ACTIVE":
                raise BadRequestException(
                    f"Cannot record sale for listing in '{listing.status}' status. Only ACTIVE listings can be sold."
                )

            vehicle = await self.vehicle_repository.get_vehicle_by_id(listing.vehicle_id)
            if not vehicle or vehicle.status == "deactivated":
                raise BadRequestException(
                    "Associated vehicle is not valid or has been deactivated."
                )

            buyer = await self.user_repository.get_user_by_id(request.buyer_id)
            if not buyer or not buyer.is_active:
                raise NotFoundException("Buyer not found or is inactive.")

            if request.buyer_id == vehicle.seller_id:
                raise BadRequestException(
                    "The vehicle seller cannot be the buyer in a resale transaction."
                )

            consultant = None
            if request.consultant_id is not None:
                consultant = await self.user_repository.get_user_by_id(request.consultant_id)
                if not consultant:
                    raise NotFoundException("Consultant not found.")

            seller = await self.user_repository.get_user_by_id(vehicle.seller_id)

            # Record transaction
            transaction = await self.resale_transaction_repository.create_transaction(
                listing_id=listing.id,
                buyer_id=request.buyer_id,
                seller_id=vehicle.seller_id,
                final_price=request.final_price,
                consultant_id=request.consultant_id,
                delivery_date=request.delivery_date,
                delivery_notes=request.delivery_notes,
            )

            # Mark listing as SOLD
            await self.vehicle_listing_repository.update_listing(
                listing_id=listing.id,
                status="SOLD",
            )

            # Mark vehicle as sold
            await self.vehicle_repository.update_vehicle_status(
                vehicle_id=vehicle.id,
                status="sold",
            )

            if buyer and seller and vehicle:
                email_payload = self._resale_transaction_email_payload(
                    buyer=buyer,
                    seller=seller,
                    vehicle=vehicle,
                    transaction=transaction,
                    consultant=consultant,
                )
        if email_payload:
            try:
                await self.email_service.send_mail(email_payload)
            except Exception:
                pass

        return transaction

    async def get_transactions(self, filters: TransactionFilterParams, user: User) -> dict:
        async with self.session.begin():
            return await self.resale_transaction_repository.get_transactions(
                filters=filters,
                user_id=user.id,
                role=user.role,
            )

    async def patch_transaction(
        self,
        transaction_id: int,
        patch_data: ResaleTransactionPatchRequest,
        user: User,
    ) -> ResaleTransaction:
        """
        Updates transaction metadata or executes deal cancellation rollback:
        - If status changes to 'CANCELLED', rolls back vehicle state to 'approved' and listing to 'ACTIVE'.
        - Sends cancellation notifications to buyer and seller outside DB transaction.
        """
        if user.role != "ADMIN":
            raise ForbiddenException("Only administrators can update resale transactions.")

        update_dict = patch_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise BadRequestException("No fields provided for update.")

        email_payload = None

        async with self.session.begin():
            tx = await self.resale_transaction_repository.get_transaction_by_id(transaction_id)
            if not tx:
                raise NotFoundException("Resale transaction not found.")

            if tx.status == "CANCELLED" and update_dict.get("status") != "CANCELLED":
                raise BadRequestException("Cannot modify a cancelled resale transaction.")

            # If cancelling transaction, restore listing to ACTIVE and vehicle to approved
            if update_dict.get("status") == "CANCELLED" and tx.status != "CANCELLED":
                await self.vehicle_listing_repository.update_listing(
                    listing_id=tx.listing_id,
                    status="ACTIVE",
                )
                vehicle = None
                if tx.listing and tx.listing.vehicle_id:
                    vehicle = await self.vehicle_repository.get_vehicle_by_id(tx.listing.vehicle_id)
                    if vehicle:
                        await self.vehicle_repository.update_vehicle_status(
                            vehicle_id=vehicle.id,
                            status="approved",
                        )

                buyer = tx.buyer or await self.user_repository.get_user_by_id(tx.buyer_id)
                seller = tx.seller or await self.user_repository.get_user_by_id(tx.seller_id)
                if buyer and seller and vehicle:
                    email_payload = self._resale_cancellation_email_payload(
                        buyer=buyer,
                        seller=seller,
                        vehicle=vehicle,
                        transaction=tx,
                    )

            updated_tx = await self.resale_transaction_repository.update_transaction(
                transaction_id=transaction_id,
                update_data=update_dict,
            )

        if email_payload:
            try:
                await self.email_service.send_mail(email_payload)
            except Exception:
                pass

        return updated_tx
