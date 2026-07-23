# views.py
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User,Card, Transfer,Payment
from .serializers import UserSerializer, TransferSerializer, CardSerializer,PaymentSerializer
import hashlib
from decimal import Decimal
import datetime





def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@api_view(['POST'])
def register(request):
    username = request.data.get("username")
    passport_number = request.data.get("passport_number")
    password = request.data.get("password")

    if not username or not passport_number or not password:
        return Response({"error": "Все поля обязательны"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Такой username уже существует"}, status=400)

    if User.objects.filter(passport_number=passport_number).exists():
        return Response({"error": "Такой паспорт уже зарегистрирован"}, status=400)

    user = User.objects.create(
        username=username,
        passport_number=passport_number,
        password_hash=hash_password(password)
    )
    return Response(UserSerializer(user).data, status=201)



@api_view(['POST'])
def login(request):
    passport_number = request.data.get("passport_number")
    password = request.data.get("password")

    try:
        user = User.objects.get(passport_number=passport_number)
        if user.password_hash == hash_password(password):
            return Response({
                "id": user.id,
                "username": user.username,
                "total_balance": sum(card.balance for card in user.cards.all())
            })
        else:
            return Response({"error": "Неверный пароль"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def make_transfer(request):
    sender_id = request.data.get("sender")
    recipient_id = request.data.get("recipient")
    amount = float(request.data.get("amount"))

    try:
        sender = User.objects.get(id=sender_id)
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

    if sender.balance < amount:
        return Response({"error": "Недостаточно средств"}, status=status.HTTP_400_BAD_REQUEST)

   

    amount = Decimal(request.data.get("amount"))

    sender.balance -= amount
    recipient.balance += amount

    sender.save()
    recipient.save()

    transfer = Transfer.objects.create(sender=sender, recipient=recipient, amount=amount)
    serializer = TransferSerializer(transfer)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def transfer_list(request):
    transfers = Transfer.objects.all().order_by('-date_added')
    serializer = TransferSerializer(transfers, many=True)
    return Response(serializer.data)


## Парсинг баланса пользователей ! 

@api_view(['GET'])
def user_balance(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return Response({"id": user.id, "username": user.username, "balance": user.balance})
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

# cardtransfer 

 
@api_view(['POST'])
def card_transfer(request):
    sender_card_number = request.data.get("sender_card")
    recipient_card_number = request.data.get("recipient_card")
    amount_str = request.data.get("amount")

    try:
        amount = Decimal(amount_str)
    except Exception:
        return Response({"error": "Некорректная сумма"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sender_card = Card.objects.get(card_number=sender_card_number)
        recipient_card = Card.objects.get(card_number=recipient_card_number)
    except Card.DoesNotExist:
        return Response({"error": "Карта не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if sender_card.balance < amount:
        return Response({"error": "Недостаточно средств"}, status=status.HTTP_400_BAD_REQUEST)

    # списание и зачисление
    sender_card.balance -= amount
    recipient_card.balance += amount
    sender_card.save()
    recipient_card.save()

    return Response({
        "status": "Перевод успешен",
        "sender_balance": sender_card.balance,
        "recipient_balance": recipient_card.balance
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def add_card(request):
    user_id = request.data.get("user")
    card_number = request.data.get("card_number")
    expiry_str = request.data.get("expiry_date")  # формат MM/YY

    if not user_id or not card_number or not expiry_str:
        return Response({"error": "Все поля обязательны"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

    # преобразуем MM/YY → YYYY-MM-DD (берём последний день месяца)
    try:
        month, year = expiry_str.split("/")
        year = int("20" + year)  # например "26" → 2026
        month = int(month)
        last_day = (datetime.date(year, month, 1) + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        expiry_date = last_day
    except Exception:
        return Response({"error": "Неверный формат даты, используйте MM/YY"}, status=status.HTTP_400_BAD_REQUEST)

    if Card.objects.filter(card_number=card_number).exists():
        return Response({"error": "Карта уже существует"}, status=status.HTTP_400_BAD_REQUEST)

    card = Card.objects.create(user=user, card_number=card_number, expiry_date=expiry_date, balance=0)
    return Response({"status": "Карта добавлена", "card_id": card.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def user_cards(request, user_id):
    cards = Card.objects.filter(user_id=user_id)
    serializer = CardSerializer(cards, many=True)
    return Response(serializer.data)
@api_view(['POST'])
def card_transfer(request):
    sender_card_number = request.data.get("sender_card")
    recipient_card_number = request.data.get("recipient_card")
    amount_str = request.data.get("amount")

    from decimal import Decimal
    try:
        amount = Decimal(amount_str)
    except Exception:
        return Response({"error": "Некорректная сумма"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sender_card = Card.objects.get(card_number=sender_card_number)
        recipient_card = Card.objects.get(card_number=recipient_card_number)
    except Card.DoesNotExist:
        return Response({"error": "Карта не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if sender_card.balance < amount:
        return Response({"error": "Недостаточно средств"}, status=status.HTTP_400_BAD_REQUEST)

    sender_card.balance -= amount
    recipient_card.balance += amount
    sender_card.save()
    recipient_card.save()

    return Response({
        "status": "Перевод успешен",
        "sender_balance": sender_card.balance,
        "recipient_balance": recipient_card.balance
    }, status=status.HTTP_200_OK)
@api_view(['POST'])
def make_payment(request):
    user_id = request.data.get("user")
    service = request.data.get("service")
    amount_str = request.data.get("amount")
    card_number = request.data.get("card_number")

    from decimal import Decimal
    try:
        amount = Decimal(amount_str)
    except Exception:
        return Response({"error": "Некорректная сумма"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.objects.get(card_number=card_number, user_id=user_id)
    except Card.DoesNotExist:
        return Response({"error": "Карта не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if card.balance < amount:
        return Response({"error": "Недостаточно средств"}, status=status.HTTP_400_BAD_REQUEST)

    card.balance -= amount
    card.save()

    payment = Payment.objects.create(user_id=user_id, service=service, amount=amount)
    serializer = PaymentSerializer(payment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def payment_list(request, user_id):
    try:
        payments = Payment.objects.filter(user_id=user_id).order_by('-date_added')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
def profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)
