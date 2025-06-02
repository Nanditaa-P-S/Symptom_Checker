from django.db import models

class Symptom(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    symptoms = models.ManyToManyField(Symptom)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    diseases = models.ManyToManyField(Disease)

    def __str__(self):
        return self.name

class HealthTip(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    related_diseases = models.ManyToManyField(Disease)

    def __str__(self):
        return self.title
class PatientRecord(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    symptoms = models.ManyToManyField(Symptom)
    diseases = models.ManyToManyField(Disease)
    check_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.check_date.date()})"
class MedicationReminder(models.Model):
    user_name = models.CharField(max_length=100)
    medicine_name = models.CharField(max_length=100)
    dosage_time = models.TimeField()
    frequency_per_day = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user_name} - {self.medicine_name}"


