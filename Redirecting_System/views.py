from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
import requests
import string
import random
import json
from fpdf import FPDF
import os
import io
import qrcode
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .encrypt_decrypt import encrypt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageDraw, ImageFont
import os
def get_firebase_app(name):
    try:
        return firebase_admin.get_app(name)
    except ValueError:
        cred = credentials.Certificate('Redirecting_System/serviceAccountCredential.json')
        return firebase_admin.initialize_app(cred, name=name)

db = firestore.client(app=get_firebase_app('alcher-redirecting-system'))




def get_data(request):
    data1 = {
        'DAY 1': db.collection('Data').document('Day-1').get().to_dict(),
        'DAY 2': db.collection('Data').document('Day-2').get().to_dict(),
        'DAY 3': db.collection('Data').document('Day-3').get().to_dict(),
    }
    data2 = {
        'EARLY BIRD SEASON PASS': db.collection('Data').document('EARLY BIRD SEASON PASS').get().to_dict(),
        'NORMAL SEASON PASS': db.collection('Data').document('NORMAL SEASON PASS').get().to_dict(),
    }
    request.session['dayWisePasses'] = data1
    request.session['seasonPasses'] = data2
    return JsonResponse(data2)

def home(request):
    dayWisePasses = request.session.get('dayWisePasses', {})
    print(dayWisePasses)
    seasonPasses = request.session.get('seasonPasses', {})
    return render(request, "Redirecting_System/home.html",{'dayWisePasses': dayWisePasses,'seasonPasses':seasonPasses})
    

def otp(request):
    return render(request, "Redirecting_System/otp.html")

def Success(request):
    return render(request, "Redirecting_System/success.html")

@csrf_exempt
def sendOtp(request):
    try:
        email = json.loads(request.body)['email']
        request.session['LeaderEmail'] = email
        otp = random.randint(100000, 999999)
        print("OTP : ", otp)
        subject = 'Your email verification'
        message = 'Your otp for verifiction of your email is ' + str(otp)
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [email])
        doc_ref = db.collection('all_otps').document()

        doc_ref.set({
            'id': doc_ref.id,
            'email': email,
            'otp': otp,
        })
        request.session['OTPId'] = doc_ref.id
        
    except Exception as e:
        print(e)
    return JsonResponse({"otp": otp})


def verify_otp(request):
    # Get the list of OTP values from the POST data
    otp_values = request.POST.getlist('otp')
    # Combine the OTP values into a single string
    otp = ''.join(otp_values)

    otpID = request.session.get('OTPId')
    snapshots = db.collection('all_otps').where('id', '==', otpID).stream() #
    users = []
    otp1 = 0
    for user in snapshots:
        formattedData = user.to_dict()
        print(formattedData)
        otp1 = formattedData['otp']
        users.append(user.reference)

    OTP = int(otp)
    email = request.session.get('LeaderEmail')
    print(OTP, otp1)
    if OTP == otp1:
        verifiedUsers = db.collection('verified_user').where('email', '==', email).stream()
        userPasses = []
        for user in verifiedUsers:
            data = user.to_dict()
            userPasses.append(user.id)

        return redirect('passes')
    
    context = {
        'message': "Incorrect OTP",
        'email': email
    }
    return render(request, 'Redirecting_System/otp.html', context)

def download_file(url):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)+"../Redirecting_System"))
    local_filename = os.path.join(base_dir, 'book1.xls')
    r = requests.get(url)
    f = open(local_filename, 'wb')
    f.write(r.content)
    f.close()
    return base_dir

def automation(request):
    dir = download_file('https://dev.bharatversity.com/events/website/api/event-amount-overview-excel-sheet-api/550b0b35-5bd1-47c0-88b2-8a952dd08e08')
    index=db.collection('index').document('rcT6Wb8kyh07erua4VaM').get().to_dict()['index']
    data=pd.read_excel(dir+'/book1.xls')
    pendinguser=db.collection('pending_user').stream()
    pend=[]
    for puser in pendinguser:
        user=puser.to_dict()
        ind = user['index']
        if data['PAYMENT_STATUS'][ind]== 'SUCCESS':
            verified = db.collection('verified_user').document()
            email=data['EMAIL'][ind]
            verify={
                "name": data['FIRST_NAME'][ind] + " " + data['LAST_NAME'][ind],
                "gender": data['GENDER'][ind],
                "contact no.":data['PHONE_NUMBER'][ind],
                "email":data['EMAIL'][ind],
                "Booking id":data['BOOKING_ID'][ind],
                "payment_status":data['PAYMENT_STATUS'][ind],
                "Amount":data['AMOUNT_PAID'][ind],
            }
            verified.set(verify)
            subject = 'just for testing'
            message='you have been verified'
            from_email = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_email, [email])
        pend.append(user)
        
    for i in range(index,len(data)):
        if data['PAYMENT_STATUS'][i]== 'SUCCESS':
            verified = db.collection('verified_user').document()
            email=data['EMAIL'][i]
            verify={
                "name": data['FIRST_NAME'][i] + " " + data['LAST_NAME'][i],
                "gender": data['GENDER'][i],
                "contact no.": int(data['PHONE_NUMBER'][i]),
                "email": data['EMAIL'][i],
                "Booking id": data['BOOKING_ID'][i],
                "payment_status": data['PAYMENT_STATUS'][i],
                "Amount": int(data['AMOUNT_PAID'][i]),
            }
            verified.set(verify)
            subject = 'just for testing'
            message='you have been verified'
            from_email = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_email, [email])
            index+=1
        if data['PAYMENT_STATUS'][i]== 'PENDING':
            pendings = db.collection('pending_user').document()
            pending={
                "name": data['FIRST_NAME'][i] + " " + data['LAST_NAME'][i],
                "gender": data['GENDER'][i],
                "contact no.": int(data['PHONE_NUMBER'][i]),
                "email": data['EMAIL'][i],
                "Booking id": data['BOOKING_ID'][i],
                "payment_status": data['PAYMENT_STATUS'][i],
                "Amount": int(data['AMOUNT_PAID'][i]),
                "index": i,
            }
            pendings.set(pending)
    db.collection('index').document('rcT6Wb8kyh07erua4VaM').update({'index':index})

@api_view(['GET'])
def user_data(request):
    try:
        email = request.query_params.get('email', None)
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        users=[]
        user_ref = db.collection('verified_user').where('email','==',email).stream()
        print(email)
        exist = False
        for user in user_ref:
            user_dic = user.to_dict()
            if user_dic['email'] == email:
                exist = True
            print(user_dic['email'])
            users.append(user_dic)
        if not users:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user = users
        # has_passes=user['err_des']['pass']
        # print(has_passes+100)
        if exist:
            encrypted_data = encrypt("alcheringa24",user)
        return Response(encrypted_data)
        # else:
        #     return Response({'error': 'User has no passes'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Create your views here.
@api_view(['GET'])
def verifyid(request):
    try:
        id = request.query_params.get('id', None)
        if not id:
            return Response({'error': 'id is required'}, status=status.HTTP_400_BAD_REQUEST)
        users=[]
        user_ref = db.collection('verified_user').stream()
        exist = False
        for user in user_ref:
            user_dic = user.to_dict()
            if user.id == id:
                exist = True
                break
        email=user_dic['email']
        subject = 'just for testing'
        message='you have been verified'
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [email])
        if not exist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success':"user verified and email sent successfully"})
    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
def send_email_with_pdf(request):
    from_email = settings.EMAIL_HOST_USER
    email = EmailMessage(
        'Hello',
        'Body goes here',
        from_email,
        ['shivamgupta@iitg.ac.in'],
        headers = {'Reply-To': 's.sanyal@iitg.ac.in'}
    )
    with open('IMG20240211171953.jpg', 'rb') as img_file:
    # Attach the image file with the name and the MIME type
        email.attach('IMG20240211171953.jpg', img_file.read(), 'image/jpeg')
    # Open the file in bynary mode
    # binary_file = open('ss.pdf', 'rb')

    # Attach the file with the name and the MIME type
    # email.attach('ss.pdf', binary_file.read(), 'application/pdf')

    # Don't forget to close the file after you have finished processing it
    # binary_file.close()

    email.send()