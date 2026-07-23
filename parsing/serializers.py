# serializers.py
from rest_framework import serializers
from .models import User,Transfer,Payment
from .models import Card

class CardSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    expiry_date = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['id', 'user_id', 'username', 'card_number', 'expiry_date', 'balance']

    def get_expiry_date(self, obj):
        return obj.expiry_date.strftime("%m/%y")






class UserSerializer(serializers.ModelSerializer):
    total_balance = serializers.SerializerMethodField()

    def get_total_balance(self, obj):
        return obj.total_balance

    class Meta:
        model = User
        fields = ["id", "username", "passport_number", "total_balance"]




class TransferSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    recipient = serializers.StringRelatedField()

    class Meta:
        model = Transfer
        fields = ['id', 'sender', 'recipient', 'amount', 'date_added']
class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Payment
        fields = ['id', 'user', 'service', 'amount', 'date_added']