from django.contrib import admin
from .models import Symptom, Disease, Doctor, HealthTip
from .models import PatientRecord 
from .models import MedicationReminder 
admin.site.register(PatientRecord)
admin.site.register(Symptom)
admin.site.register(Disease)
admin.site.register(Doctor)
admin.site.register(HealthTip)

admin.site.register(MedicationReminder) 