import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'monteretroion@gmail.com'
SMTP_PASS = os.environ.get('MUE_SMTP_PASS', '')
SMTP_FROM = 'monteretroion@gmail.com'
SMTP_TLS = True

# SECURITY email gets tunnel notifications
TO_EMAIL = 'monteretroion@gmail.com'
TUNNEL_URL = 'https://cardiff-forever-needed-mattress.trycloudflare.com/go'

if not SMTP_PASS:
    print('SMTP_PASS not set - cannot send email')
    print('Tunnel URL: ' + TUNNEL_URL)
else:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'MUE Dashboard - Cloudflare Tunnel URL (Security)'
    msg['From'] = SMTP_FROM
    msg['To'] = TO_EMAIL

    text = 'MUE Review Dashboard - Cloudflare Tunnel URL\n\nYour Cloudflare tunnel has been restarted with a fresh public URL:\n\n' + TUNNEL_URL + '\n\nThis URL will remain active while the review server is running.\nAccess the dashboard from any network using this link.\n\n---\nSent by MUE Review Server (Security Notification)'

    html = '<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">'
    html += '<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">'
    html += '<div style="background:linear-gradient(135deg,#dc3545,#ff6b6b);padding:24px;color:#fff">'
    html += '<h1 style="margin:0;font-size:20px">🔐 MUE Dashboard - Tunnel URL (Security)</h1>'
    html += '</div>'
    html += '<div style="padding:24px">'
    html += '<p style="font-size:14px;color:#333">Your Cloudflare tunnel has been restarted with a fresh public URL:</p>'
    html += '<div style="background:#fff0f0;border:2px solid #dc3545;border-radius:8px;padding:16px;margin:16px 0;text-align:center">'
    html += '<a href="' + TUNNEL_URL + '" style="font-size:16px;font-weight:600;color:#dc3545;text-decoration:none">' + TUNNEL_URL + '</a>'
    html += '</div>'
    html += '<p style="font-size:13px;color:#666">This URL will remain active while the review server is running. Access the dashboard from any network using this link.</p>'
    html += '<hr style="border:none;border-top:1px solid #eee;margin:24px 0">'
    html += '<p style="font-size:11px;color:#aaa;text-align:center">Sent by MUE Review Server - Security Notification</p>'
    html += '</div></div></body></html>'

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        if SMTP_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [TO_EMAIL], msg.as_string())
        server.quit()
        print('Tunnel URL sent to SECURITY email: ' + TO_EMAIL)
    except Exception as e:
        print('Failed to send email: ' + str(e))
        print('Tunnel URL: ' + TUNNEL_URL)