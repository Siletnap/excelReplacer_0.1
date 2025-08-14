from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class State(models.TextChoices):  # Enumeration of allowed values
    IN = 'in', 'In'
    OUT = 'out', 'Out'
    REPAIR = 'repair', 'Repair'


class BoatType(models.TextChoices):  # Enumeration of allowed values
    motorYacht = 'M/Y', 'M/Y'
    sailingYacht = 'S/Y', 'S/Y'
    catamaran = 'CAT.', 'CAT.'
    jetski = 'JETSKI', 'JETSKI'
    tender = 'TENDER', 'TENDER'

class Boat(models.Model):

    boatType = models.CharField(
        max_length=30,
        choices=BoatType.choices,
        default=BoatType.motorYacht,
    )
    name = models.CharField(max_length=100)
    berth = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(  # <-- changed from IntegerField
        max_length=20,
        choices=State.choices,
        default=State.IN,
    )
    cid = models.CharField(max_length=50, default="", blank=True)
    ecod = models.CharField(max_length=50, default="", blank=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        if self.berth:
            self.berth = self.berth.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.boatType} {self.name}"

class TrafficEntry(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    boatType = models.CharField(
        max_length=30,
        choices=BoatType.choices,
        default=BoatType.motorYacht,
    )
    name = models.CharField(max_length=100)
    trDate = models.DateField(null=True, blank=True)
    # trDate = models.CharField(max_length=20, null=True, blank=True) # date
    trTime = models.TimeField(null=True, blank=True)
    direction = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.IN,
    )
    passengers = models.IntegerField(validators=[MinValueValidator(1)],
                                     default="",
                                     null=True,
                                     blank=True)
    purpose = models.CharField(max_length=100, default="", null=True, blank=True)
    edr = models.DateField(default="", null=True, blank=True)
    # edr = models.CharField(max_length=20, default="", null=True, blank=True)
    etr = models.TimeField(default="", null=True, blank=True)
    trComments = models.CharField(max_length=200, default="", null=True, blank=True)
    berth = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.boatType} {self.name} going {self.direction}, at {self.trTime}, on {self.trDate}."