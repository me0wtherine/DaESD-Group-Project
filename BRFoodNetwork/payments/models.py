from django.db import models

# Create your models here.
class WeeklyPayment():
    WeeklyPaymentID
    TotalPayment
    TotalComission
    AccountNumber
    AccountName
    SortCode

class Payments(models.Model):
    PaymentID
    OrderID
    NetworkCommission
    ProducerPayment
    ProducerID
    WeeklyPaymentID
