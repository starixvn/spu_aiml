import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry



def send_message(err):
    url = f"https://bot.nexdev.net/skynex/api/messages/forwardwithtoken?token=0A40aOc7CtpzjbBSJu8KNWQRoXyjRvf9&message={err}&conversationId=-596361283"
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount(url, adapter)
    session.mount(url, adapter)

    session.post(url)
    #requests.post(url)