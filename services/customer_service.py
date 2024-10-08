from exceptions import raise_error
from models.order import Order
from models.flower import Flower
from models.orderdetail import OrderDetail
from models.customerspending import CustomerSpending
from schemas.order import OrderCreate, OrderResponse, OrderDetailResponse
from sqlalchemy.orm import Session
from schemas.base_response import BaseResponse
from typing import List
from datetime import date, datetime


def order_response(order: Order, db: Session) -> OrderResponse:
    order_details = db.query(OrderDetail).filter(OrderDetail.order_id == order.id).all()
    order_details_response = [
        OrderDetailResponse(
            id=detail.id,
            flower_id=detail.flower_id,
            quantity=detail.quantity,
            total_price=detail.total_price
        )
        for detail in order_details
    ]
    return OrderResponse(
            id=order.id,
            total_cost=order.total_cost,
            day=order.day,
            month=order.month,
            year=order.year,
            order_details=order_details_response
        )


def get_all(user_id: int, db: Session) -> List[OrderResponse]:
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return [order_response(order, db) for order in orders]


def get_by_id(user_id: int, order_id: int, db: Session) -> OrderResponse | BaseResponse:
    if order_id < 1:
        return raise_error(10)
    order_model = db.query(Order).filter(
        Order.user_id == user_id,
        Order.id == order_id
    ).first()
    if order_model is None:
        return raise_error(300003)
    return order_response(order_model, db)


def create(user_id: int, order: OrderCreate, db: Session) -> OrderResponse | BaseResponse:
    details = order.order_details
    total_cost = 0
    for detail in details:
        if detail.flower_id < 1 or detail.quantity < 1:
            return raise_error(300002)
        flower = db.query(Flower).filter(Flower.id == detail.flower_id).first()
        if flower is None or detail.quantity > flower.quantity:
            return raise_error(300002)
        total_cost += (detail.quantity * flower.price)
        flower.quantity -= detail.quantity
        db.add(flower)
        db.commit()
    current_date = datetime.now()
    order_model = Order(
        day=current_date.day,
        month=current_date.month,
        year=current_date.year,
        total_cost=total_cost,
        user_id=user_id
    )
    db.add(order_model)
    db.commit()
    order_details = []
    for detail in details:
        flower = db.query(Flower).filter(Flower.id == detail.flower_id).first()
        detail_model = OrderDetail(
            quantity=detail.quantity,
            total_price=detail.quantity*flower.price,
            flower_id=flower.id,
            order_id=order_model.id
        )
        order_details.append(detail_model)
        db.add(detail_model)
        db.commit()
    spending = db.query(CustomerSpending).filter(CustomerSpending.id == user_id).first()
    if spending is None:
        spending = CustomerSpending(
            id=user_id,
            total_spending=total_cost
        )
    else:
        spending.total_spending += total_cost
    db.add(spending)
    db.commit()
    order_details_response = [
        OrderDetailResponse(
            id=detail.id,
            flower_id=detail.flower_id,
            quantity=detail.quantity,
            total_price=detail.total_price
        )
        for detail in order_details
    ]
    return OrderResponse(
        id=order_model.id,
        total_cost=order_model.total_cost,
        day=order_model.day,
        month=order_model.month,
        year=order_model.year,
        order_details=order_details_response
    )


def daily_orders(user_id: int, day: int, month: int, year: int, db: Session) -> List[OrderResponse] | BaseResponse:
    try:
        date(year, month, day)
    except Exception:
        return raise_error(500001)
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.day == day,
        Order.month == month,
        Order.year == year
    ).all()
    return [order_response(order, db) for order in orders]


def monthly_orders(user_id: int, month: int, year: int, db: Session) -> List[OrderResponse] | BaseResponse:
    try:
        date(year, month, 1)
    except Exception:
        return raise_error(500001)
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.month == month,
        Order.year == year
    ).all()
    return [order_response(order, db) for order in orders]


def quarterly_orders(user_id: int, quarter: int, year: int, db: Session) -> List[OrderResponse] | BaseResponse:
    if year < 1:
        return raise_error(10)
    if not 1 <= quarter <= 4:
        return raise_error(11)
    start_month, end_month = quarter * 3 - 2, quarter * 3
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.month >= start_month,
        Order.month <= end_month,
        Order.year == year
    ).all()
    return [order_response(order, db) for order in orders]


def yearly_orders(user_id: int, year: int, db: Session) -> List[OrderResponse] | BaseResponse:
    if year < 1:
        return raise_error(10)
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.year == year
    ).all()
    return [order_response(order, db) for order in orders]