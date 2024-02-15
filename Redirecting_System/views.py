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
def unique_id(length):
    iv = (db.collection('verified_user').stream())
    document_ids = [doc.id for doc in iv]
    while True:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if random_string not in document_ids:
            print(random_string)
            return random_string
def automation(request):
    dir = download_file('https://dev.bharatversity.com/events/website/api/event-amount-overview-excel-sheet-api/550b0b35-5bd1-47c0-88b2-8a952dd08e08')
    index=db.collection('index').document('rcT6Wb8kyh07erua4VaM').get().to_dict()['index']
    data=pd.read_excel('Book1.xlsx')
    pendinguser=db.collection('pending_user').stream()
    pend=[]
    for puser in pendinguser:
        user=puser.to_dict()
        ind = user['index']
        if data['PAYMENT_STATUS'][ind]== 'SUCCESS':
            verified = db.collection('verified_user').document(unique_id(7))
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
            verified = db.collection('verified_user').document(unique_id(7))
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

# def generate_pdf_for_transaction(transaction_data):
#     script_dir = os.path.dirname(__file__)
#     pdf_bytes_list = []  # Initialize the list to hold byte strings of each PDF
#     for user in transaction_data:
#         pass_type = user['pass_type']
        
#         pdf = FPDF('L', 'mm', (270, 870))
#         pdf.add_page()
#         pdf_bytes_list = []
#         if pass_type == 'ebsp':
#             pdf.Image("images/EBSP.png", 0, 0, pdf.w, pdf.h)
            
#         elif pass_type == 'NORMAL':
#             image_path = os.path.join(script_dir, "NSP.jpg")
#             pdf.image(image_path, 0, 0, pdf.w, pdf.h)
#             # pdf.image("NSP.jpg", 0, 0, pdf.w, pdf.h)
#             qr_code_data = 'https://www.example.com/' + user['user_id']  # Use 'user' instead of 'transaction_data'
#             aztec = qrcode.QRCode(version=1, box_size=10, border=4)
#             aztec.add_data(qr_code_data)
#             aztec.make(fit=True)
#             if pass_type == 'ebsp':
#                 aztec_img = aztec.make_image(fill_color="white", back_color="#677DE0")
#             elif pass_type == 'NORMAL':
#                 aztec_img = aztec.make_image(fill_color="white", back_color="#F28E15")
#                 qr_code_path = f'aztec_code_{user["user_id"]}.png'  # Use 'user' instead of 'transaction_data'
                   
#                 aztec_img.save(qr_code_path)
#                 aztec_img = aztec_img.resize((85, 85))
#                 pdf.image(qr_code_path, pdf.w - 365, pdf.h - 230, 150, 150)  # Use 'qr_code_path' instead of 'aztec_code.png'
#                 pdf.add_page()
#                 image_path = os.path.join(script_dir, "BoardPassBack2.png")
#                 pdf.image(image_path, 0, 0, pdf.w, pdf.h)
#                 # print("Hii") 
#                 # pdf.image("images/BoardPassBack2.png", 0, 0, pdf.w, pdf.h)
                
#         else : 
#             print("kharab")
            
#         pdf_string = pdf.output(dest='S')

#         # Create a BytesIO object
#         output = io.BytesIO()

#         # Write the PDF string to the BytesIO object
#         output.write(pdf_string.encode('latin1'))

#         # Get the value of the BytesIO object
#         output.seek(0)
#         pdf_bytes = output.read()

#         # Print the byte
#         # Close the BytesIO object
#         output.close()
#         pdf_bytes_list.append(pdf_bytes)  # Append byte string of current PDF to the list

#     return pdf_bytes_list  # Return list of byte strings
 



def generate_jpg_for_transaction(transaction_data):
    script_dir = os.path.dirname(__file__)
    jpg_bytes_list = []  # Initialize the list to hold byte strings of each JPEG
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_filename = os.path.join(base_dir, 'Redirecting_System')
    local_filename = os.path.join(local_filename, 'Uncut-Sans-Regular.otf')
    for user in transaction_data:
        pass_type = user['pass_type']
        
        if pass_type == 'ebsp':
            img = Image.open("images/EBSP.png")
            
        elif pass_type == 'NORMAL':
            image_path = os.path.join(script_dir, "NSP.jpg")
            img = Image.open(image_path)
            
            qr_code_data = 'http://localhost:8000/otp/?user_id=' + user['user_id']
            aztec = qrcode.QRCode(version=1, box_size=10, border=4)
            aztec.add_data(qr_code_data)
            aztec.make(fit=True)
            if pass_type == 'ebsp':
                aztec_img = aztec.make_image(fill_color="white", back_color="#677DE0")
            elif pass_type == 'NORMAL':
                aztec_img = aztec.make_image(fill_color="white", back_color="#F28E15")
                qr_code_path = f'aztec_code_{user["user_id"]}.png'
                   
                aztec_img.save(qr_code_path)
                aztec_img = aztec_img.resize((365, 365))  # Resize the QR code to be larger
                img.paste(aztec_img, (img.width - 950, img.height - 665))  # Paste the QR code onto the image
                
                # Create a new image to hold both the front and back images
                combined_img = Image.new('RGB', (img.width, img.height * 2))
                
                # Paste the front image onto the new image
                combined_img.paste(img, (0, 0))
                
                # Open the back image and paste it onto the new image
                back_img = Image.open(os.path.join(script_dir, "BoardPassBack2.jpg"))
                combined_img.paste(back_img, (0, img.height))
                
                # Use the combined image for the rest of the function
                img = combined_img
                
        else : 
            print("Invalid pass type")
        
        # Add user_id to the image
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(local_filename, 27)  # Choose your font and size
        draw.text((1320, 700), user['user_id'], fill="black",font=font)  # Choose position (x, y) and color
        # Add vertical user_id to the image
        text_img = Image.new('RGB', (320, 50), color = (255, 255, 255))  # Create a new image to draw the vertical text
        text_draw = ImageDraw.Draw(text_img)
        text_font = ImageFont.truetype(local_filename, 24)  # Choose your font and size
        text_draw.text((10, 10), user['user_id'], fill="black", font=text_font)  # Draw the text on the new image
        rotated_text_img = text_img.rotate(90, expand=1)  # Rotate the image with the text

        x_vertical = 70  # replace with your desired x-coordinate for vertical text
        y_vertical = 438  # replace with your desired y-coordinate for vertical text
        img.paste(rotated_text_img, (x_vertical, y_vertical))  # Paste the rotated text image onto the original image
        # Convert the image to a byte string
        output = io.BytesIO()
        img.save(output, format='JPEG')
        output.seek(0)
        jpg_bytes = output.read()
        output.close()
        jpg_bytes_list.append(jpg_bytes)  # Append byte string of current JPEG to the list

    return jpg_bytes_list 



def passes(request):
    try:
        user_email = "saraswatasanyal@gmail.com"
        passes_info = []
        iid=[]
        user_ref = db.collection('verified_user').where('email', '==', user_email).stream()
        img_storage = default_storage
        for us in user_ref:
            x = us.to_dict()
            id = us.id
            x['id'] = id
            iid.append(id)
            passes_info.append({
                'user_id': id,
                'pass_type': x['pass_type']
            })
        jpg_bytes_list = generate_jpg_for_transaction(passes_info)
        print(len(jpg_bytes_list))
        for i, jpg_bytes in enumerate(jpg_bytes_list):
            file_path = img_storage.save(f'media/imgs/{iid[i]}.jpg', ContentFile(jpg_bytes))
        # print(pdf_bytes_list)
        # Assuming you want to return a response with a link to the first generated PDF
        jpg_url = img_storage.url(file_path)
        response = HttpResponse(f'PDF generated and accessible at: {jpg_url}')
        return response
    
    except Exception as e:
        print(e)
        return HttpResponse("An error occurred.")
passes(3)

def passPage(request):
    # pass_instance = Pass.objects.get(id=pass_id)
    email = request.session.get('LeaderEmail')
    verifiedUsers = db.collection('verified_user').where('email', '==', email).stream()
    userPasses = []
    for user in verifiedUsers:
        data = user.to_dict()
        file_path = f'imgs/{user.id}.jpg'  # Adjust the path based on your actual structure
        file_url = settings.MEDIA_URL + file_path
        userPasses.append(file_url)
    
    return render(request,"Redirecting_System/passes.html", {'passes': userPasses})
passes(3)