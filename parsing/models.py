# models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    passport_number = models.CharField(max_length=20, unique=True)
    password_hash = models.CharField(max_length=256, default="")

    @property
    def total_balance(self):
        return sum(card.balance for card in self.cards.all())


class Card(models.Model):
    user = models.ForeignKey(
        User,
        related_name="cards",   # <--- вот это важно
        on_delete=models.CASCADE
    )
    card_number = models.CharField(max_length=16, unique=True)
    expiry_date = models.DateField()
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)



class Transfer(models.Model):
    sender = models.ForeignKey(User, related_name="sent_transfers", on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_transfers", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.amount}"
    


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} оплатил {self.service} на {self.amount}"