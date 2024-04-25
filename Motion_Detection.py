import firebase_admin
from firebase_admin import credentials, firestore
import cv2,os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from twilio.rest import Client

video = cv2.VideoCapture(0)
first_frame = None

# Initialize Firebase Admin SDK
cred = credentials.Certificate("live_data_tracker.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Define a function to send data to Firebase
def send_data_to_firebase(collection_name, data):
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    doc_ref = db.collection(collection_name).document("time{}".format(current_time))
    doc_ref.set(data)
    print("Data sent successfully to Firebase.")

# Function to send email
def send_email(subject, body, recipient_email, attachment=None):
    sender_email = "rahulbui555@gmail.com"  # Replace with your email
    sender_password = "wwni xurr ovdz uysc"  # Replace with your email password
    
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    if attachment:
        with open(attachment, 'rb') as img_file:
            img_part = MIMEImage(img_file.read(), name=f"suspicious_activity_{formatted_time}.jpg")
            message.attach(img_part)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        print("Email sent successfully.")
        server.quit()
    except Exception as e:
        print("Error sending email:", str(e))

# Function to send SMS using Twilio
def send_sms(sms_body, recipient_phone_number):
    account_sid = "AC2b5c444d0d8bfe239fee4a4b5d426fbc"  # Replace with your Twilio account SID
    auth_token = "aa7d02a43e0ce5d0a71ad96f7a38f5d8"  # Replace with your Twilio auth token
    sender_phone_number = "+13187088680"  # Replace with your Twilio phone number

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=sms_body,
        from_=sender_phone_number,
        to=recipient_phone_number
    )

    print("SMS sent successfully:", message.sid)

while True: 
    check, frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    if first_frame is None:
        first_frame = gray 
        continue
    
    delta_frame = cv2.absdiff(first_frame, gray)
    threshold_frame = cv2.threshold(delta_frame, 50, 255, cv2.THRESH_BINARY)[1]
    threshold_frame = cv2.dilate(threshold_frame, None, iterations=2)
    contours, _ = cv2.findContours(threshold_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cval=False
    for contour in contours: 
        if cv2.contourArea(contour) < 775:
            continue  
        
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 205, 0), 3)
        cval = True
    
    collection_name1 = "Motion_Time"
    if cval:
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        data_to_send = {"time": current_time}  # Data to be sent to Firestore
        send_data_to_firebase(collection_name1, data_to_send)
        # Ensure the "Suspicious" directory exists
        if not os.path.exists("Suspicious"):
            os.makedirs("Suspicious")
            
        # Define the path for the image including the "Suspicious" directory
        #suspicious_image_path = "Suspicious/suspicious_activity.jpg"
        #  # Ensure the "Suspicious" directory exists
        # if not os.path.exists("Suspicious"):
        #     os.makedirs("Suspicious")
        # Save the suspicious activity image in the "Suspicious" directory
        #cv2.imwrite(suspicious_image_path, frame)
        # Adjust the filename to include the current time
        formatted_time = time.strftime("%Y-%m-%d_%H-%M-%S", t)  # This formats the time in a way suitable for filenames
        suspicious_image_filename = f"suspicious_activity_{formatted_time}.jpg"
        suspicious_image_path = os.path.join("Suspicious", suspicious_image_filename)
        
        # Save the suspicious activity image with the current time in the filename
        cv2.imwrite(suspicious_image_path, frame)
        # Send email when suspicious activity is detected
        subject = "Suspicious Activity Detected"
        user_name = "Rahul Rai"  # Replace with the user's name
        body = f"Hey, {user_name}, there is someone who is entering in your home/office in your absence at {current_time}."
        recipient_email = "rahulbui420@gmail.com"  # Replace with recipient's email
        #cv2.imwrite("suspicious_activity.jpg", frame)  # Save the suspicious activity image
        send_email(subject, body, recipient_email, attachment=suspicious_image_path)

        # Send SMS notification
        sms_body = f"Suspicious Activity Detected: {body}"
        recipient_phone_number = "+91 95656 43520"  # Replace with recipient's phone number
        send_sms(sms_body, recipient_phone_number)
    
    cv2.imshow("Rahul Rai", frame)
    key = cv2.waitKey(1)
    
    if key == ord('q'):
        break 

video.release()
cv2.destroyAllWindows()
