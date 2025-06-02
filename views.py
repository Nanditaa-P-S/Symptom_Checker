from django.shortcuts import render, redirect
from .models import Symptom, Disease, Doctor, HealthTip, PatientRecord, MedicationReminder
from django.utils import timezone
from django.core.mail import send_mail
from django.http import HttpResponse
from .mongo_utils import get_mongo_client
from .local_storage import get_local_storage

def user_info(request):
    """Step 1: Collect user information"""
    if request.method == 'POST':
        # Get user information from form
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')

        # Store user info in session
        request.session['user_name'] = name
        request.session['user_age'] = age
        request.session['user_gender'] = gender
        request.session['user_email'] = email
        request.session['user_phone'] = phone

        # Redirect to symptom form
        return redirect('symptom_form')

    return render(request, 'checker/user_info.html')

def symptom_form(request):
    symptoms = Symptom.objects.all()

    if request.method == 'POST':
        selected_ids = request.POST.getlist('symptoms')
        duration = request.POST.get('duration')
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')

        selected_symptoms = Symptom.objects.filter(id__in=selected_ids)

        # Disease and doctor prediction
        diseases = Disease.objects.filter(symptoms__in=selected_symptoms).distinct()
        doctors = Doctor.objects.filter(diseases__in=diseases).distinct()
        tips = HealthTip.objects.filter(related_diseases__in=diseases).distinct()

        # Save patient record in Django ORM
        record = PatientRecord.objects.create(
            name=name,
            age=age,
            gender=gender
        )
        record.symptoms.set(selected_symptoms)
        record.diseases.set(diseases)
        record.save()

        # Save to MongoDB
        mongo_client = get_mongo_client()

        # Convert Django model instances to dictionaries
        symptoms_data = [{'id': s.id, 'name': s.name} for s in selected_symptoms]
        diseases_data = [{'id': d.id, 'name': d.name, 'description': d.description} for d in diseases]

        # Create MongoDB document
        patient_data = {
            'django_id': record.id,
            'name': name,
            'age': int(age),
            'gender': gender,
            'symptoms': symptoms_data,
            'diseases': diseases_data,
            'check_date': timezone.now(),
            'duration': duration
        }

        # Insert into MongoDB
        mongo_client.insert_one('patient_records', patient_data)

        context = {
            'diseases': diseases,
            'doctors': doctors,
            'tips': tips,
        }
        return render(request, 'checker/results.html', context)

    return render(request, 'checker/symptom_form.html', {'symptoms': symptoms})

def search_tips(request):
    query = request.GET.get('q')
    tips = []

    if query:
        diseases = Disease.objects.filter(name__icontains=query)
        tips = HealthTip.objects.filter(related_diseases__in=diseases).distinct()

        # Log search in MongoDB
        mongo_client = get_mongo_client()
        search_data = {
            'query': query,
            'timestamp': timezone.now(),
            'results_count': len(tips),
            'user_ip': request.META.get('REMOTE_ADDR', 'unknown'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
        }
        mongo_client.insert_one('search_logs', search_data)

    return render(request, 'checker/search_tips.html', {'tips': tips, 'query': query})

def medication_reminder(request):
    user_reminders = None

    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        user_email = request.POST.get('user_email')
        medicine_name = request.POST.get('medicine_name')
        dosage_time = request.POST.get('dosage_time')
        frequency = request.POST.get('frequency')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Save to Django ORM
        reminder = MedicationReminder.objects.create(
            user_name=user_name,
            medicine_name=medicine_name,
            dosage_time=dosage_time,
            frequency_per_day=frequency,
            start_date=start_date,
            end_date=end_date
        )

        # Save to MongoDB with email
        mongo_client = get_mongo_client()

        # Create MongoDB document
        reminder_data = {
            'django_id': reminder.id,
            'user_name': user_name,
            'user_email': user_email,
            'medicine_name': medicine_name,
            'dosage_time': dosage_time,
            'frequency_per_day': int(frequency),
            'start_date': start_date,
            'end_date': end_date,
            'created_at': timezone.now()
        }

        # Insert into MongoDB
        mongo_client.insert_one('medication_reminders', reminder_data)

        # Automatically send confirmation email
        try:
            confirmation_message = f"""
Dear {user_name},

Your medication reminder has been set successfully!

Medicine: {medicine_name}
Dosage Time: {dosage_time}
Frequency: {frequency} times per day
Duration: {start_date} to {end_date}

We'll send you reminders at the scheduled times.

Best regards,
Symptom Checker Team
            """

            send_mail(
                subject=f'Medication Reminder Set: {medicine_name}',
                message=confirmation_message,
                from_email='noreply@symptomchecker.com',
                recipient_list=[user_email],
                fail_silently=False,
            )

            # Log confirmation email
            email_data = {
                'recipient': user_email,
                'subject': f'Medication Reminder Set: {medicine_name}',
                'timestamp': timezone.now(),
                'status': 'sent',
                'type': 'confirmation',
                'medicine_name': medicine_name,
                'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
            }
            mongo_client.insert_one('email_logs', email_data)

        except Exception as e:
            # Log error but don't stop the process
            email_data = {
                'recipient': user_email,
                'subject': f'Medication Reminder Set: {medicine_name}',
                'timestamp': timezone.now(),
                'status': 'failed',
                'error': str(e),
                'type': 'confirmation',
                'medicine_name': medicine_name,
                'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
            }
            mongo_client.insert_one('email_logs', email_data)

        # fetch reminders for that user
        user_reminders = MedicationReminder.objects.filter(user_name=user_name)

        return render(request, 'checker/medication_form.html', {
            'user_name': user_name,
            'user_email': user_email,
            'reminders': user_reminders,
        })

    return render(request, 'checker/medication_form.html')

def send_test_email(request):
    recipient_email = 'nanditaa@example.com'  # Change this to your actual email

    try:
        send_mail(
            subject='Test Reminder from Symptom Checker',
            message='Hello Nanditaa! This is a test email from your Django app.',
            from_email='noreply@symptomchecker.com',  # Use a generic from email
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        # Log email sending in MongoDB
        mongo_client = get_mongo_client()
        email_data = {
            'recipient': recipient_email,
            'subject': 'Test Reminder from Symptom Checker',
            'timestamp': timezone.now(),
            'status': 'sent',
            'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
        }
        mongo_client.insert_one('email_logs', email_data)

        return HttpResponse("✅ Test email sent!")
    except Exception as e:
        # Log error in MongoDB
        mongo_client = get_mongo_client()
        email_data = {
            'recipient': recipient_email,
            'subject': 'Test Reminder from Symptom Checker',
            'timestamp': timezone.now(),
            'status': 'failed',
            'error': str(e),
            'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
        }
        mongo_client.insert_one('email_logs', email_data)

        return HttpResponse(f"❌ Failed to send email: {str(e)}")

def send_medication_reminder(request):
    """Send medication reminders to users"""
    if request.method == 'POST':
        user_email = request.POST.get('user_email')
        medicine_name = request.POST.get('medicine_name')
        dosage_time = request.POST.get('dosage_time')

        if not user_email or not medicine_name:
            return HttpResponse("❌ Please provide email and medicine name")

        try:
            # Create reminder message
            message = f"""
Dear Patient,

This is a friendly reminder to take your medication:

Medicine: {medicine_name}
Time: {dosage_time}
Date: {timezone.now().strftime('%B %d, %Y')}

Please take your medication as prescribed by your doctor.

Best regards,
Symptom Checker Team
            """

            send_mail(
                subject=f'Medication Reminder: {medicine_name}',
                message=message,
                from_email='noreply@symptomchecker.com',
                recipient_list=[user_email],
                fail_silently=False,
            )

            # Log email sending in MongoDB
            mongo_client = get_mongo_client()
            email_data = {
                'recipient': user_email,
                'subject': f'Medication Reminder: {medicine_name}',
                'timestamp': timezone.now(),
                'status': 'sent',
                'type': 'reminder',
                'medicine_name': medicine_name,
                'dosage_time': dosage_time,
                'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
            }
            mongo_client.insert_one('email_logs', email_data)

            return HttpResponse(f"✅ Medication reminder sent to {user_email}!")

        except Exception as e:
            # Log error in MongoDB
            mongo_client = get_mongo_client()
            email_data = {
                'recipient': user_email,
                'subject': f'Medication Reminder: {medicine_name}',
                'timestamp': timezone.now(),
                'status': 'failed',
                'error': str(e),
                'type': 'reminder',
                'medicine_name': medicine_name,
                'dosage_time': dosage_time,
                'user_ip': request.META.get('REMOTE_ADDR', 'unknown')
            }
            mongo_client.insert_one('email_logs', email_data)

            return HttpResponse(f"❌ Failed to send reminder: {str(e)}")

    # If GET request, check for URL parameters (from reminder buttons)
    medicine_name = request.GET.get('medicine')
    dosage_time = request.GET.get('time')
    user_email = request.GET.get('email')

    if medicine_name and dosage_time and user_email:
        # Pre-fill the form with data from URL
        context = {
            'medicine_name': medicine_name,
            'dosage_time': dosage_time,
            'user_email': user_email
        }
        return render(request, 'checker/send_reminder.html', context)

    # If GET request without parameters, show empty form
    return render(request, 'checker/send_reminder.html')

def mongo_data_view(request):
    """View to display data from MongoDB collections and local storage"""
    mongo_client = get_mongo_client()
    local_storage = get_local_storage()

    # Check if MongoDB connection is successful
    mongodb_available = mongo_client.connect()

    # Get data from local storage
    local_patient_records = local_storage.find('patient_records')
    local_medication_reminders = local_storage.find('medication_reminders')
    local_search_logs = local_storage.find('search_logs')
    local_email_logs = local_storage.find('email_logs')

    if mongodb_available:
        # Get data from MongoDB
        mongo_patient_records = mongo_client.find('patient_records')
        mongo_medication_reminders = mongo_client.find('medication_reminders')
        mongo_search_logs = mongo_client.find('search_logs')
        mongo_email_logs = mongo_client.find('email_logs')

        context = {
            'mongodb_available': True,
            'patient_records': mongo_patient_records,
            'medication_reminders': mongo_medication_reminders,
            'search_logs': mongo_search_logs,
            'email_logs': mongo_email_logs,
            'local_patient_records': local_patient_records,
            'local_medication_reminders': local_medication_reminders,
            'local_search_logs': local_search_logs,
            'local_email_logs': local_email_logs,
            'using_local_storage': False
        }
    else:
        context = {
            'mongodb_available': False,
            'patient_records': local_patient_records,
            'medication_reminders': local_medication_reminders,
            'search_logs': local_search_logs,
            'email_logs': local_email_logs,
            'error_message': 'MongoDB is not available. Using local storage instead.',
            'using_local_storage': True
        }

    return render(request, 'checker/mongo_data.html', context)
