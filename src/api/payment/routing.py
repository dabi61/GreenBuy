from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Annotated
from datetime import datetime
import uuid

from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.order.model import Order, OrderStatus
from .model import Payment, PaymentMethod, PaymentStatus, RefundRequest
from .scheme import (
    PaymentMethodCreate, PaymentMethodRead, PaymentMethodUpdate,
    PaymentCreate, PaymentRead, PaymentUpdate,
    RefundRequestCreate, RefundRequestRead, RefundRequestUpdate,
    ProcessPaymentRequest, PaymentResponse
)

router = APIRouter()

# ==================== PAYMENT METHODS ====================

@router.post("/methods", response_model=PaymentMethodRead)
def create_payment_method(
    payment_method: PaymentMethodCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Tạo phương thức thanh toán mới"""
    
    # Nếu đây là default method, tắt default của các method khác
    if payment_method.is_default:
        existing_methods = session.exec(
            select(PaymentMethod).where(
                PaymentMethod.user_id == current_user.id,
                PaymentMethod.is_default == True
            )
        ).all()
        for method in existing_methods:
            method.is_default = False
            session.add(method)
    
    # Mask card number (chỉ lưu 4 số cuối)
    card_number_masked = None
    if payment_method.card_number:
        card_number_masked = "**** **** **** " + payment_method.card_number[-4:]
    
    new_method = PaymentMethod(
        user_id=current_user.id,
        type=payment_method.type,
        card_number=card_number_masked,
        card_holder_name=payment_method.card_holder_name,
        expiry_month=payment_method.expiry_month,
        expiry_year=payment_method.expiry_year,
        paypal_email=payment_method.paypal_email,
        bank_name=payment_method.bank_name,
        account_number=payment_method.account_number,
        account_holder=payment_method.account_holder,
        is_default=payment_method.is_default
    )
    
    session.add(new_method)
    session.commit()
    session.refresh(new_method)
    return new_method

@router.get("/methods", response_model=List[PaymentMethodRead])
def get_payment_methods(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Lấy danh sách phương thức thanh toán của user"""
    methods = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_active == True
        )
    ).all()
    return methods

@router.put("/methods/{method_id}", response_model=PaymentMethodRead)
def update_payment_method(
    method_id: int,
    update_data: PaymentMethodUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Cập nhật phương thức thanh toán"""
    method = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == method_id,
            PaymentMethod.user_id == current_user.id
        )
    ).first()
    
    if not method:
        raise HTTPException(404, detail="Payment method not found")
    
    # Nếu set default, tắt default của các method khác
    if update_data.is_default:
        existing_methods = session.exec(
            select(PaymentMethod).where(
                PaymentMethod.user_id == current_user.id,
                PaymentMethod.is_default == True,
                PaymentMethod.id != method_id
            )
        ).all()
        for m in existing_methods:
            m.is_default = False
            session.add(m)
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(method, field, value)
    
    method.updated_at = datetime.utcnow()
    session.add(method)
    session.commit()
    session.refresh(method)
    return method

@router.delete("/methods/{method_id}")
def delete_payment_method(
    method_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Xóa phương thức thanh toán (soft delete)"""
    method = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == method_id,
            PaymentMethod.user_id == current_user.id
        )
    ).first()
    
    if not method:
        raise HTTPException(404, detail="Payment method not found")
    
    method.is_active = False
    session.add(method)
    session.commit()
    return {"message": "Payment method deleted"}

# ==================== PAYMENTS ====================

@router.post("/process/{order_id}", response_model=PaymentResponse)
def process_payment(
    order_id: int,
    payment_request: ProcessPaymentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Xử lý thanh toán cho đơn hàng"""
    
    # Kiểm tra order - use "orders" table since that's where new orders are created
    from sqlalchemy import text
    order_result = session.execute(
        text('SELECT id, user_id, total_amount FROM orders WHERE id = :order_id AND user_id = :user_id'),
        {"order_id": order_id, "user_id": current_user.id}
    ).first()
    
    if not order_result:
        raise HTTPException(404, detail="Order not found")
    
    # For this simplified flow, assume all orders can be paid (since "order" table doesn't have status)
    
    # Kiểm tra xem đã có payment thành công chưa - use raw SQL to avoid enum comparison issue
    from sqlalchemy import text
    existing_payment_result = session.execute(
        text("SELECT id FROM payment WHERE order_id = :order_id AND status = CAST(:status AS paymentstatus)"),
        {"order_id": order_id, "status": "completed"}
    ).first()
    
    existing_payment = existing_payment_result is not None
    
    if existing_payment:
        raise HTTPException(400, detail="Order already paid")
    
    payment_method = None
    
    # Xử lý payment method
    if payment_request.payment_method_id:
        payment_method = session.exec(
            select(PaymentMethod).where(
                PaymentMethod.id == payment_request.payment_method_id,
                PaymentMethod.user_id == current_user.id,
                PaymentMethod.is_active == True
            )
        ).first()
        
        if not payment_method:
            raise HTTPException(404, detail="Payment method not found")
    
    elif payment_request.new_payment_method:
        # Tạo payment method mới nếu user chọn save
        if payment_request.save_payment_method:
            card_number_masked = None
            if payment_request.new_payment_method.card_number:
                card_number_masked = "**** **** **** " + payment_request.new_payment_method.card_number[-4:]
            
            payment_method = PaymentMethod(
                user_id=current_user.id,
                type=payment_request.new_payment_method.type,
                card_number=card_number_masked,
                card_holder_name=payment_request.new_payment_method.card_holder_name,
                expiry_month=payment_request.new_payment_method.expiry_month,
                expiry_year=payment_request.new_payment_method.expiry_year,
                paypal_email=payment_request.new_payment_method.paypal_email,
                bank_name=payment_request.new_payment_method.bank_name,
                account_number=payment_request.new_payment_method.account_number,
                account_holder=payment_request.new_payment_method.account_holder,
                is_default=payment_request.new_payment_method.is_default
            )
            session.add(payment_method)
            session.commit()
            session.refresh(payment_method)
    
    # Tạo payment record using raw SQL to avoid enum issues
    transaction_id = str(uuid.uuid4())
    
    payment_insert_sql = text("""
        INSERT INTO payment (
            order_id, payment_method_id, amount, currency, status, 
            transaction_id, notes, created_at
        ) VALUES (
            :order_id, :payment_method_id, :amount, :currency, 
            CAST(:status AS paymentstatus), :transaction_id, :notes, :created_at
        ) RETURNING id
    """)
    
    payment_result = session.execute(payment_insert_sql, {
        'order_id': order_id,
        'payment_method_id': payment_method.id if payment_method else None,
        'amount': order_result[2],  # Use total_price from order query result
        'currency': 'VND',
        'status': 'processing',
        'transaction_id': transaction_id,
        'notes': f'Payment for Order #{order_id}',
        'created_at': datetime.utcnow()
    })
    
    payment_id = payment_result.fetchone()[0]
    session.commit()
    
    # Mô phỏng xử lý thanh toán
    # Trong thực tế, đây sẽ là integration với payment gateway
    success = simulate_payment_processing(payment_method, order_result[2])
    
    if success:
        # Update payment to completed using raw SQL
        payment_update_sql = text("""
            UPDATE payment 
            SET status = CAST(:status AS paymentstatus), 
                completed_at = :completed_at, 
                processed_at = :processed_at
            WHERE id = :payment_id
        """)
        
        session.execute(payment_update_sql, {
            'status': 'completed',
            'completed_at': datetime.utcnow(),
            'processed_at': datetime.utcnow(),
            'payment_id': payment_id
        })
        
        session.commit()
        
        return PaymentResponse(
            success=True,
            payment_id=payment_id,
            transaction_id=transaction_id,
            status="completed",
            amount=order_result[2],
            message="Payment completed successfully"
        )
    else:
        # Update payment to failed using raw SQL
        payment_update_sql = text("""
            UPDATE payment 
            SET status = CAST(:status AS paymentstatus), 
                failure_reason = :failure_reason,
                processed_at = :processed_at
            WHERE id = :payment_id
        """)
        
        session.execute(payment_update_sql, {
            'status': 'failed',
            'failure_reason': 'Payment gateway rejected the transaction',
            'processed_at': datetime.utcnow(),
            'payment_id': payment_id
        })
        
        session.commit()
        
        return PaymentResponse(
            success=False,
            payment_id=payment_id,
            transaction_id=transaction_id,
            status="failed",
            amount=order_result[2],
            message="Payment failed"
        )

@router.get("/", response_model=List[PaymentRead])
def get_user_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Lấy danh sách payments của user"""
    payments = session.exec(
        select(Payment)
        .join(Order)
        .where(Order.user_id == current_user.id)
    ).all()
    return payments

@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Lấy thông tin chi tiết payment"""
    payment = session.exec(
        select(Payment)
        .join(Order)
        .where(
            Payment.id == payment_id,
            Order.user_id == current_user.id
        )
    ).first()
    
    if not payment:
        raise HTTPException(404, detail="Payment not found")
    
    return payment

# ==================== REFUNDS ====================

@router.post("/refund", response_model=RefundRequestRead)
def request_refund(
    refund_request: RefundRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Yêu cầu hoàn tiền"""
    
    # Kiểm tra payment - use raw SQL to avoid enum comparison
    payment_result = session.execute(
        text("""SELECT p.id, p.order_id, p.amount FROM payment p 
             JOIN orders o ON p.order_id = o.id 
             WHERE p.id = :payment_id AND o.user_id = :user_id 
             AND p.status = CAST(:status AS paymentstatus)"""),
        {"payment_id": refund_request.payment_id, "user_id": current_user.id, "status": "completed"}
    ).first()
    
    if not payment_result:
        raise HTTPException(404, detail="Payment not found or not eligible for refund")
    
    # Get full payment object for amount checking
    payment = session.get(Payment, payment_result[0])
    
    if not payment:
        raise HTTPException(404, detail="Payment not found or not eligible for refund")
    
    if refund_request.amount > payment.amount:
        raise HTTPException(400, detail="Refund amount cannot exceed payment amount")
    
    # Kiểm tra xem đã có refund request chưa
    existing_refund = session.exec(
        select(RefundRequest).where(
            RefundRequest.payment_id == refund_request.payment_id,
            RefundRequest.status.in_(["pending", "approved"])
        )
    ).first()
    
    if existing_refund:
        raise HTTPException(400, detail="Refund request already exists")
    
    new_refund = RefundRequest(
        payment_id=refund_request.payment_id,
        user_id=current_user.id,
        amount=refund_request.amount,
        reason=refund_request.reason
    )
    
    session.add(new_refund)
    session.commit()
    session.refresh(new_refund)
    return new_refund

@router.post("/test", response_model=dict)
def test_payment_creation(
    session: Session = Depends(get_session)
):
    """Simple test endpoint for payment functionality"""
    try:
        # Use raw SQL to avoid enum casting issues
        from sqlalchemy import text
        transaction_id = str(uuid.uuid4())
        
        insert_sql = text("""
            INSERT INTO payment (
                order_id, amount, currency, status, transaction_id, 
                notes, created_at
            ) VALUES (
                :order_id, :amount, :currency, CAST(:status AS paymentstatus), 
                :transaction_id, :notes, :created_at
            ) RETURNING id
        """)
        
        result = session.execute(insert_sql, {
            'order_id': 1,  # Use order from "order" table
            'amount': 95000.0,
            'currency': 'VND',
            'status': 'pending',
            'transaction_id': transaction_id,
            'notes': 'Test payment',
            'created_at': datetime.utcnow()
        })
        
        payment_id = result.fetchone()[0]
        session.commit()
        
        return {
            "success": True,
            "payment_id": payment_id,
            "transaction_id": transaction_id,
            "status": "pending",
            "amount": 95000.0,
            "message": "Test payment created successfully!"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Test payment creation failed"
        }

def simulate_payment_processing(payment_method: PaymentMethod, amount: float) -> bool:
    """
    Mô phỏng xử lý thanh toán
    Trong thực tế, đây sẽ integrate với các payment gateway như:
    - Stripe, PayPal cho thẻ tín dụng
    - MoMo, ZaloPay API cho e-wallet
    - Bank API cho chuyển khoản
    """
    import random
    
    # COD luôn thành công
    if payment_method and payment_method.type == "cod":
        return True
    
    # Mô phỏng 90% success rate cho các payment method khác
    return random.random() > 0.1 