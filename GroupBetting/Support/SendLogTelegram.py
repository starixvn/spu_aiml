import requests
import logging

def send_message(err):
    url = f"https://bot.nexdev.net/skynex/api/messages/forwardwithtoken?token=0A40aOc7CtpzjbBSJu8KNWQRoXyjRvf9&message={err}&conversationId=-596361283"
    requests.post(url)
    

