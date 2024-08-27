from smtplib import SMTP_SSL, SMTPAuthenticationError, SMTPConnectError, SMTPException
from ssl import create_default_context
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from os.path import basename
from keyring import get_password

class SecureEmailSender:
    def __init__(self, smtp_server, smtp_port):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        # Get Keyring
        self.sender_email = get_password('email_service', 'email_user')
        self.sender_password = get_password('email_service', 'email_pass')
        self.context = create_default_context()

    def send_email(self, recipient_email, subject, body, file_path=None):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if file_path:
            try:
                with open(file_path, 'rb') as attachment_file:
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(attachment_file.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename= {basename(file_path)}')
                msg.attach(attachment)
            except Exception as e:
                print(f"Failed to attach file: {e}")
                return

        try:
            with SMTP_SSL(self.smtp_server, self.smtp_port, context=self.context) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
                print("Email envoyé avec succès")
        except SMTPAuthenticationError:
            print("Échec de l'authentification avec le serveur SMTP. Vérifiez vos identifiants.")
        except SMTPConnectError:
            print("Échec de la connexion au serveur SMTP. Vérifiez l'adresse et le port du serveur.")
        except SMTPException as e:
            print(f"Une erreur SMTP est survenue: {e}")
        except Exception as e:
            print(f"Échec de l'envoi de l'email: {e}")


if __name__ == "__main__":
    # exemple temporaire (à faire à partir d'un fichier) depuis le main
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465

    secure_email_sender = SecureEmailSender(smtp_server, smtp_port)
    recipient_email = 'destinataire@gmail.com'
    subject = 'security feedback'
    body = ''
    file_path = 'itsatest.txt'

    secure_email_sender.send_email(recipient_email, subject, body, file_path)
