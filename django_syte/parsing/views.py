# views.py

import hashlib
import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import User, Card, Transfer, Payment
from .serializers import (
    UserSerializer,
    TransferSerializer,
    CardSerializer,
    PaymentSerializer,
)


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================================================
# REGISTER
# =========================================================

@api_view(['POST'])
def register(request):
    username = request.data.get("username")
    passport_number = request.data.get("passport_number")
    password = request.data.get("password")

    if not username or not passport_number or not password:
        return Response(
            {"error": "Все поля обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Такой username уже существует"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(passport_number=passport_number).exists():
        return Response(
            {"error": "Такой паспорт уже зарегистрирован"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create(
        username=username,
        passport_number=passport_number,
        password_hash=hash_password(password)
    )

    return Response(
        UserSerializer(user).data,
        status=status.HTTP_201_CREATED
    )


# =========================================================
# LOGIN
# =========================================================

@api_view(['POST'])
def login(request):
    passport_number = request.data.get("passport_number")
    password = request.data.get("password")

    if not passport_number or not password:
        return Response(
            {"error": "Паспорт и пароль обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(
            passport_number=passport_number
        )

    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    if user.password_hash != hash_password(password):
        return Response(
            {"error": "Неверный пароль"},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "id": user.id,
        "username": user.username,
        "total_balance": user.total_balance
    })


# =========================================================
# USERS LIST
# =========================================================

@api_view(['GET'])
def user_list(request):
    users = User.objects.all()

    serializer = UserSerializer(
        users,
        many=True
    )

    return Response(serializer.data)


# =========================================================
# USER BALANCE
# =========================================================

@api_view(['GET'])
def user_balance(request, user_id):

    try:
        user = User.objects.get(
            id=user_id
        )

    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    total_balance = sum(
        (card.balance for card in user.cards.all()),
        Decimal("0")
    )

    return Response({
        "id": user.id,
        "username": user.username,
        "balance": total_balance
    })


# =========================================================
# USER CARDS
# =========================================================

@api_view(['GET'])
def user_cards(request, user_id):

    try:
        User.objects.get(id=user_id)

    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    cards = Card.objects.filter(
        user_id=user_id
    ).order_by("id")

    serializer = CardSerializer(
        cards,
        many=True
    )

    return Response(serializer.data)


# =========================================================
# ADD CARD
# =========================================================

@api_view(['POST'])
def add_card(request):

    user_id = request.data.get("user")
    card_number = request.data.get("card_number")
    expiry_str = request.data.get("expiry_date")

    if not user_id or not card_number or not expiry_str:
        return Response(
            {"error": "Все поля обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверка номера карты
    card_number = str(card_number).strip()

    if not card_number.isdigit():
        return Response(
            {"error": "Номер карты должен содержать только цифры"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(card_number) != 16:
        return Response(
            {"error": "Номер карты должен содержать 16 цифр"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Пользователь
    try:
        user = User.objects.get(
            id=user_id
        )

    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Дата MM/YY
    try:
        month, year = expiry_str.split("/")

        month = int(month)
        year = int("20" + year)

        if month < 1 or month > 12:
            raise ValueError

        first_day = datetime.date(
            year,
            month,
            1
        )

        next_month = (
            first_day + datetime.timedelta(days=32)
        ).replace(day=1)

        last_day = next_month - datetime.timedelta(days=1)

        expiry_date = last_day

    except Exception:
        return Response(
            {
                "error":
                "Неверный формат даты. Используйте MM/YY"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Проверяем существование карты
    if Card.objects.filter(
        card_number=card_number
    ).exists():

        return Response(
            {"error": "Карта уже существует"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Создание карты
    card = Card.objects.create(
        user=user,
        card_number=card_number,
        expiry_date=expiry_date,
        balance=Decimal("0")
    )

    return Response(
        {
            "status": "Карта добавлена",
            "card_id": card.id
        },
        status=status.HTTP_201_CREATED
    )


# =========================================================
# CARD TRANSFER
# =========================================================

@api_view(['POST'])
def card_transfer(request):

    user_id = request.data.get("user_id")
    sender_card_number = request.data.get("sender_card")
    recipient_card_number = request.data.get("recipient_card")
    amount_str = request.data.get("amount")

    # -----------------------------------------------------
    # Проверяем поля
    # -----------------------------------------------------

    if (
        not user_id
        or not sender_card_number
        or not recipient_card_number
        or not amount_str
    ):
        return Response(
            {"error": "Все поля обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )

    sender_card_number = str(
        sender_card_number
    ).strip()

    recipient_card_number = str(
        recipient_card_number
    ).strip()

    # -----------------------------------------------------
    # Проверяем сумму
    # -----------------------------------------------------

    try:
        amount = Decimal(
            str(amount_str)
        )

    except (InvalidOperation, ValueError, TypeError):
        return Response(
            {"error": "Некорректная сумма"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if amount <= 0:
        return Response(
            {"error": "Сумма должна быть больше 0"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Нельзя переводить на ту же карту
    # -----------------------------------------------------

    if sender_card_number == recipient_card_number:
        return Response(
            {
                "error":
                "Нельзя перевести деньги на ту же карту"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Получаем карты
    # -----------------------------------------------------

    try:

        # ВАЖНО:
        # карта отправителя должна принадлежать
        # текущему пользователю

        sender_card = Card.objects.get(
            card_number=sender_card_number,
            user_id=user_id
        )

        # Получатель может быть картой другого пользователя

        recipient_card = Card.objects.get(
            card_number=recipient_card_number
        )

    except Card.DoesNotExist:

        return Response(
            {
                "error":
                "Карта отправителя или получателя не найдена"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------------------------
    # Проверяем баланс
    # -----------------------------------------------------

    if sender_card.balance < amount:

        return Response(
            {"error": "Недостаточно средств"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Выполняем перевод
    # -----------------------------------------------------

    with transaction.atomic():

        sender_card.balance -= amount
        recipient_card.balance += amount

        sender_card.save(
            update_fields=["balance"]
        )

        recipient_card.save(
            update_fields=["balance"]
        )

        transfer = Transfer.objects.create(
            sender=sender_card.user,
            recipient=recipient_card.user,
            amount=amount
        )

    # -----------------------------------------------------
    # Ответ
    # -----------------------------------------------------

    return Response(
        {
            "status": "Перевод успешен",
            "transfer_id": transfer.id,
            "amount": amount,
            "sender_balance": sender_card.balance,
            "recipient_balance": recipient_card.balance
        },
        status=status.HTTP_200_OK
    )


# =========================================================
# TRANSFER HISTORY
# =========================================================

@api_view(['GET'])
def transfer_list(request):

    transfers = Transfer.objects.all().order_by(
        "-date_added"
    )

    serializer = TransferSerializer(
        transfers,
        many=True
    )

    return Response(serializer.data)


# =========================================================
# USER TRANSFER HISTORY
# =========================================================

@api_view(['GET'])
def user_transfer_list(request, user_id):

    transfers = Transfer.objects.filter(
        sender_id=user_id
    ) | Transfer.objects.filter(
        recipient_id=user_id
    )

    transfers = transfers.order_by(
        "-date_added"
    )

    serializer = TransferSerializer(
        transfers,
        many=True
    )

    return Response(serializer.data)


# =========================================================
# PAYMENT
# =========================================================

@api_view(['POST'])
def make_payment(request):

    user_id = request.data.get("user")
    service = request.data.get("service")
    amount_str = request.data.get("amount")
    card_number = request.data.get("card_number")

    if (
        not user_id
        or not service
        or not amount_str
        or not card_number
    ):
        return Response(
            {"error": "Все поля обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Сумма
    # -----------------------------------------------------

    try:
        amount = Decimal(
            str(amount_str)
        )

    except (InvalidOperation, ValueError, TypeError):
        return Response(
            {"error": "Некорректная сумма"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if amount <= 0:
        return Response(
            {"error": "Сумма должна быть больше 0"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Карта должна принадлежать пользователю
    # -----------------------------------------------------

    try:

        card = Card.objects.get(
            card_number=card_number,
            user_id=user_id
        )

    except Card.DoesNotExist:

        return Response(
            {"error": "Карта не найдена"},
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------------------------
    # Баланс
    # -----------------------------------------------------

    if card.balance < amount:

        return Response(
            {"error": "Недостаточно средств"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # Оплата
    # -----------------------------------------------------

    with transaction.atomic():

        card.balance -= amount

        card.save(
            update_fields=["balance"]
        )

        payment = Payment.objects.create(
            user_id=user_id,
            service=service,
            amount=amount
        )

    serializer = PaymentSerializer(
        payment
    )

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


# =========================================================
# PAYMENT HISTORY
# =========================================================

@api_view(['GET'])
def payment_list(request, user_id):

    payments = Payment.objects.filter(
        user_id=user_id
    ).order_by(
        "-date_added"
    )

    serializer = PaymentSerializer(
        payments,
        many=True
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


# =========================================================
# PROFILE
# =========================================================

@api_view(['GET'])
def profile(request, user_id):

    try:
        user = User.objects.get(
            id=user_id
        )

    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserSerializer(
        user
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )