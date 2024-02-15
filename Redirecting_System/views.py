from django.shortcuts import render
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .encrypt_decrypt import encrypt
print(settings.BASE_DIR)
def get_firebase_app(name):
    try:
        return firebase_admin.get_app(name)
    except ValueError:
        cred = credentials.Certificate('Redirecting_System/serviceAccountCredential.json')
        return firebase_admin.initialize_app(cred, name=name)

db = firestore.client(app=get_firebase_app('alcher-redirecting-system'))

def download_file(url):
    local_filename = 'book1.xlsx'
    r = requests.get(url)
    f = open(local_filename, 'wb')
    f.write(r.content)
    f.close()
    return

def automation(request):
    index=db.collection('index').document('rcT6Wb8kyh07erua4VaM').get().to_dict()['index']
    data=pd.read_excel(r'/Users/shivamg/Downloads/Book1.xlsx')
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
        email = request.query_params.get('Email', None)
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        users=[]
        user_ref = db.collection('transaction').where('Email','==',email).stream()
        print(email)
        for user in user_ref:
            user_dic = user.to_dict()
            print(user_dic['Email'])
            users.append(user_dic)
        if not users:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user = users[0]
        has_passes=user['err_des']['pass']
        print(has_passes+100)
        if has_passes:
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
    email = EmailMessage(
        'Hello',
        'Body goes here',
        'saraswatasanyal@gmail.com',
        ['shivamgupta@iitg.ac.in'],
        headers = {'Reply-To': 's.sanyal@iitg.ac.in'}
    )

    # Open the file in bynary mode
    binary_file = open('ss.pdf', 'rb')

    # Attach the file with the name and the MIME type
    email.attach('ss.pdf', binary_file.read(), 'application/pdf')

    # Don't forget to close the file after you have finished processing it
    binary_file.close()

    email.send()