import requests
import json

def send_push_notification(user_id, title, body, data=None):
    """
    Simule l'envoi d'une notification push via Firebase (FCM).
    Dans une vraie app, on utiliserait firebase-admin.
    """
    # Dans une vraie implémentation :
    # message = messaging.Message(
    #     notification=messaging.Notification(title=title, body=body),
    #     token=user_device_token,
    #     data=data
    # )
    # response = messaging.send(message)

    print(f"[PUSH] Envoi à l'utilisateur {user_id}: {title} - {body}")
    return True

def notify_grade_drop(student_id, subject_id, new_value):
    """Vérifie si la note est en baisse significative et notifie les parents."""
    # Logique pour comparer avec la moyenne précédente
    # Si baisse > 20%, send_push_notification(...)
    pass
