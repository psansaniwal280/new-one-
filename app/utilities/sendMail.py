import sendgrid
from decouple import config
import jwt
from sendgrid.helpers.mail import Mail, Email, To, Content
from graphql_jwt.utils import jwt_encode, jwt_payload
from django.template.loader import render_to_string
import socket
import pyotp

def sendMailToUser(name, username, email):
    token = jwt.encode({'user': username}, "1232141" ,algorithm='HS256').decode('utf-8')
    print(socket.gethostbyname(socket.gethostname()))
    context = {
        'small_text_detail': 'Welcome! Thank you for creating an account. \n Please confirm your email to set up your account.',
        'email': email,
        'domain': "http://127.0.0.1:8000",
        'token': token,
        'username': username,
    }
    msg_html = render_to_string('email.html', context)   
    sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
    from_email = Email(config('EMAIL_HOST'))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    subject = "Email Confirmation Request"
    mail = Mail(from_email, to_email, subject, html_content=msg_html)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
    
    # html = render_to_string('activationSuccess.html', context)
    
    if response.status_code == 202:
        response = {
        'message': "Successfully registered for user "+username,
        'token': token
        }
        return response

def sendPasswordResetCodeMailToUser(email, username, user_id):
    print("In mail")
    base32secret = pyotp.random_base32()
    code = pyotp.TOTP(base32secret, interval=300)
    context = {
        'small_text_detail': 'Please enter this password in the application.',
        'code':code.now(),
        'email': email,
        'username': username,
        'userId': user_id
    }
    msg_html = render_to_string('resetpasswordemail.html', context)
    sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
    from_email = Email(config('EMAIL_HOST'))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    subject = "Reset Password Request"
    mail = Mail(from_email, to_email, subject, html_content=msg_html)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
    
    # # html = render_to_string('activationSuccess.html', context)
    
    # if response.status_code == 202:
    #     response = {
    #     'message': "Successfully registered for user "+username,
    #     'token': token
    #     }
    #     return response
    if response.status_code == 202:
        return {'message':"successfully sent the code to the email provided", 'code': response.status_code, 'secretcode': base32secret}
        
def sendPostReportMailToUser(username, email, reason):
    # token = jwt.encode({'user': username}, "1232141" ,algorithm='HS256').decode('utf-8')
    print(socket.gethostbyname(socket.gethostname()))
    context = {
        'small_text_detail': 'Hello!, your post have been reported for the following reason.',
        'email': email,
        'reason': reason,
        'username': username,
    }
    msg_html = render_to_string('reportpost.html', context)
    sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
    from_email = Email(config('EMAIL_HOST'))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    subject = "Post Reported"
    mail = Mail(from_email, to_email, subject, html_content=msg_html)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
    
    # html = render_to_string('activationSuccess.html', context)
    
    if response.status_code == 202:
        response = {
        'message': "successfully sent an email for user regarding their reported post"+username,
        }
        return response
    else:
        return None
    
def sendUserReportMailToUser(username, email, reason):
    # token = jwt.encode({'user': username}, "1232141" ,algorithm='HS256').decode('utf-8')
    print(socket.gethostbyname(socket.gethostname()))
    context = {
        'small_text_detail': 'Hello!, your profile has been reported for the following reason.',
        'email': email,
        'reason': reason,
        'username': username,
    }
    msg_html = render_to_string('reportuser.html', context)
    sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
    from_email = Email(config('EMAIL_HOST'))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    subject = "User Profile Reported"
    mail = Mail(from_email, to_email, subject, html_content=msg_html)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
    
    # html = render_to_string('activationSuccess.html', context)
    
    if response.status_code == 202:
        response = {
        'message': "successfully sent an email for user regarding their reported post"+username,
        }
        return response
    else:
        return None


def sendInvoiceMailToUser(name,email,content):
    # token = jwt.encode({'user': username}, "1232141" ,algorithm='HS256').decode('utf-8')
    print(socket.gethostbyname(socket.gethostname()))
    context = {
        'small_text_detail': 'Hello!, your booking invoice',
        'email': email,
        'reason': content,
        'username': name,
    }
    sg = sendgrid.SendGridAPIClient(api_key=config('SENDGRID_API_KEY'))
    from_email = Email(config('EMAIL_HOST'))  # Change to your verified sender
    to_email = To(email)  # Change to your recipient
    subject = "Booking Invoice"
    mail = Mail(from_email, to_email, subject, html_content=content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)

    # html = render_to_string('activationSuccess.html', context)

    if response.status_code == 202:
        response = {
            'message': "successfully sent an email of invoice" + name,
        }
        return response
    else:
        return None
