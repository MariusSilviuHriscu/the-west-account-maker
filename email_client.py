
import time
from typing import Type, TypeVar

from typing import Protocol

T = TypeVar('T')


class EmailProtocol(Protocol):
    email : str
    def __str__(self) -> str:
        ...
    def get_inbox(self) -> list[dict[str, str]]:
        ...
    def get_mail_content(self, message_id: str) -> str:
        ...
    def wait_for_new_email(self , delay : float , timeout : int) -> list[dict[str, str]]:
        ...
    
class EmailProvider(Protocol):
    def __call__(self) -> EmailProtocol:
        ...


class Client():
    
    def __init__(self , email_provider: Type[EmailProvider]):
        self.email_provider = email_provider
        self._email_dict : dict[str : EmailProtocol] = {}
    
    def save_email(self, email: EmailProtocol) -> dict[str : EmailProtocol]:
        self._email_dict[email.email] = email
        return self._email_dict
    
    def _get_random_emails(self , ammount : int) -> list[EmailProtocol]:
        for _ in range(5):
            try :
                return [self.email_provider.__call__() for _ in range(ammount)]
            except Exception as e:
                print(f'Error: {e}')
                time.sleep(10)
                continue
        return [self.email_provider.__call__() for _ in range(ammount)]
    
    def random_email(self, ammount : int) -> list[str]:
        
        new_emails : list[EmailProtocol] = self._get_random_emails(ammount)
        for email in new_emails:
            self.save_email(email)
        return [email.email for email in new_emails]
    def get_emails(self , email: str) -> list[dict[str, str]]:
        return self._email_dict[email].get_inbox()
    
    def get_message(self, adress : str, message_id: str) -> str:
        return self._email_dict[adress].get_mail_content(message_id)
    
    def await_new_message(self, adress: str) -> list[dict[str, str]]:
        self._email_dict[adress].wait_for_new_email(delay=1.0, timeout=120)
        return self.get_emails(adress)