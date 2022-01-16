import smtplib, ssl
from django.conf import settings

from manager.models import InOuting, HasBeenMailedOuting, Outing

port = 465  # For SSL
email_password = settings.EMAIL_HOST_PASSWORD

# Create a secure SSL context
context = ssl.create_default_context()

url = "http://secbc.herokuapp.com"


def sendOutingReminders(outing_id):
    outing = Outing.objects.get(id=outing_id)
    crsids = []

    body = """<html>
              <head></head>
              <body>
              <p>Dear rower/cox/coach,</p>
              <p>You have an outing coming up on """ + str(outing.date) + " at " + str(outing.meetingTime) + """.</p>
              <p>You can check your upcoming outings at http://secbc.herokuapp.com/myOutings/</p>
              <p>/SECBC Website</p>
              </body></html>
              """

    # Todo can be made more robust
    for inOuting in InOuting.objects.filter(outing=outing):
        person = inOuting.person

        if (HasBeenMailedOuting.objects.filter(person=person, outing=outing).count() == 0):
            crsids += [person.username]
            HasBeenMailedOuting(person=person, outing=outing).save()

    send_email(crsids, "[SECBC WEBSITE] Outing Reminder", body)


# Todo Use Django email api instead
def send_email(crsids, subject, body):
    sent_from = 'secbc.web@gmail.com'
    send_to = ",".join([crsid + "@cam.ac.uk" for crsid in crsids])
    headers = [
        "From: " + sent_from,
        "Subject: " + subject,
        "To: " + "stedmunds.captain@cucbc.org",
        "Bcc: " + send_to,
        "MIME-Version: 1.0",
        "Content-Type: text/html"]
    headers = "\r\n".join(headers)

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sent_from, email_password)
        server.sendmail(sent_from, send_to, headers + "\r\n\r\n" + body)


def sendSignupDetails(crsid, password):
    sent_from = 'secbc.web@gmail.com'
    send_to = crsid + "@cam.ac.uk"
    subject = 'Welcome to St. Edmunds College Boat Club'

    headers = [
        "From: " + sent_from,
        "Subject: " + subject,
        "To: " + send_to,
        "MIME-Version: 1.0",
        "Content-Type: text/html"]
    headers = "\r\n".join(headers)

    body = """<html>
      <head></head>
      <body>
      <p>Welcome to the SECBC website! Sign in at http://secbc.herokuapp.com using """ + password + """ as your password.</p>
      <p>Please remember to change your password after you've logged in</p>
      <p>HOW TO SIGN UP FOR ERG SESSIONS: Go to login -> Sign up for outings as a rower -> Click 'join' on any erg times for which you may be available</p>
      <p>Once you've marked yourself as available, the captains may assign you a spot on any of your available days.</p>
      <p>TO SEE IF YOU'VE BEEN ALLOTED FOR AN ERG SESSION: Check 'view my outings' a bit later (We'll also be sending out mails).</p>
      </body></html>
      """

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sent_from, email_password)
        server.sendmail(sent_from, send_to, headers + "\r\n\r\n" + body)
