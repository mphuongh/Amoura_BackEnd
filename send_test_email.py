# send_test_email.py

from app.core.email_client import send_email

def main():
    print("Sending test email...")

    send_email(
        to_email="YOUR_EMAIL@gmail.com",   # <-- đổi thành email bạn muốn nhận
        subject="[Amoura] Test Email",
        text_body="This is a plain text test email from Amoura backend.",
        html_body="<h1>HTML Test Email</h1><p>This is a <b>test</b> email.</p>",
    )

    print("If no errors: email sent! Check your inbox.")

if __name__ == "__main__":
    main()
