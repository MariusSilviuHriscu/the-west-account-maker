import secmail
import requests
import typing
import random
from bs4 import BeautifulSoup
import string

from account_saver import AccountSaverManager
from accounts_models import Account_db

from requests_handler import RequestsHandler

class UnsuccessfullRegistrationException(Exception):
    """Exception raised when registration is unsuccessful."""
    pass


class ConfirmationEmailException(Exception):
    """Exception raised when confirmation email cannot be processed."""
    pass


class Account:
    """Class representing an account."""

    def __init__(self, name: str, password: typing.Optional[str] = None):
        """
        Initialize an Account object.

        Args:
            name (str): The name of the account.
            password (str, optional): The password of the account. If not provided, a random password will be generated.
        """
        self.name = name
        self.password = password or self.random_password()

    def random_password(self, password_length: int = 10):
        """
        Generate a random password.

        Args:
            password_length (int): Length of the generated password.

        Returns:
            str: The randomly generated password.
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=password_length))


def extract_href(html_str: str) -> str:
    """
    Extract the validation link from an HTML string.

    Args:
        html_str (str): The HTML string containing the validation link.

    Returns:
        str: The validation link extracted from the HTML string.
    """
    cleaned_html = html_str.strip().replace('\t', '').replace('\n', '')
    soup = BeautifulSoup(cleaned_html, 'lxml')
    return soup.find(lambda tag: tag.get('href', '').startswith('https://www.the-west.ro/?mode=validate_email&hash='))['href']


class WestEmailConfirmer:
    """Class for confirming emails for The West registration."""

    def __init__(self, client: secmail.Client , requests_handler : RequestsHandler):
        """
        Initialize a WestEmailConfirmer object.

        Args:
            client (secmail.Client): The client used for accessing email services.
        """
        self.client = client
        self.handler = requests_handler

    def get_emails(self, email: str) -> list[secmail.Inbox]:
        """
        Get the list of emails received for a specific email address.

        Args:
            email (str): The email address to check for received emails.

        Returns:
            list[secmail.Inbox]: The list of received emails.
        """
        return self.client.get_inbox(address=email)

    def confirm_email(self, accept_url: str) -> None:
        """
        Confirm the email registration by accessing the provided URL.

        Args:
            accept_url (str): The URL for confirming email registration.

        Raises:
            ConfirmationEmailException: If the confirmation email cannot be processed.
        """
        result = self.handler.get(accept_url)
        if result.status_code != 200:
            raise ConfirmationEmailException('Could not activate account ! ')

    def get_email_body(self, email: str, email_id: int) -> str:
        """
        Get the body of an email message.

        Args:
            email (str): The email address from which the message was received.
            email_id (int): The ID of the email message.

        Returns:
            str: The HTML body of the email message.
        """
        return self.client.get_message(address=email, message_id=email_id).html_body

    def confirm(self, email: str):
        """
        Confirm the registration by processing the confirmation email.

        Args:
            email (str): The email address used for registration.
        """
        received_emails = self.get_emails(email=email)
        if len(received_emails) == 0:
            inbox = self.client.await_new_message(address=email)
        else:
            inbox = received_emails[0]

        if inbox.from_address.split('@')[-1] != 'the-west.net':
            raise Exception('Got incorrect received email ! ')

        accept_url = extract_href(html_str=self.get_email_body(email=email, email_id=inbox.id))
        self.confirm_email(accept_url=accept_url)


class WestRegistrationRequest:
    """Class representing a registration request for The West."""

    def __init__(self, email: str , requests_handler : RequestsHandler):
        """
        Initialize a WestRegistrationRequest object.

        Args:
            email (str): The email address to be used for registration.
        """
        self.email = email
        self.handler = requests_handler
        self.usable_email = True

    def try_to_register(self, username: str, email: str, password: str) -> bool:
        """
        Attempt to register a user with provided credentials.

        Args:
            username (str): The username of the account.
            email (str): The email address of the account.
            password (str): The password of the account.

        Returns:
            bool: True if registration is successful, False otherwise.
        """
        payload = {
            'name': f'{username}',
            'email': f'{email}',
            'agb': 1,
            'emails_optin': 1,
            'password': f'{password}',
            'password_confirm': f'{password}',
            'friendsdata': []
        }
        response = self.handler.post('https://www.the-west.ro/index.php?page=register&ajax=registration&locale=ro_RO&world=0',
                                 params = payload
                                     )
        if response.json().get('success', '') != "Înregistrare reușită!":
            return False
        return True

    def register(self, name: str, password: str, confirmer: WestEmailConfirmer, account_saver: AccountSaverManager) -> bool:
        """
        Register a user with provided credentials and confirm the registration via email.

        Args:
            name (str): The username of the account.
            password (str): The password of the account.
            confirmer (WestEmailConfirmer): The email confirmer object.

        Returns:
            bool: True if registration is successful, False otherwise.

        Raises:
            UnsuccessfullRegistrationException: If registration is unsuccessful.
            Exception: For any other unexpected errors.
        """
        register_bool = self.try_to_register(username=name,
                                              email=self.email,
                                              password=password
                                              )
        if not register_bool:
            raise UnsuccessfullRegistrationException(f'Could not register using  {name} : {password}')

        self.usable_email = False
        account_saver.save_account(account = Account_db(name=name, password=password,email = self.email))
        confirmer.confirm(email=self.email)
        account_saver.mark_account_as_activated(account_name=name)


    @staticmethod
    def from_client(email: str , handler : RequestsHandler) -> 'WestRegistrationRequest':
        """
        Create a WestRegistrationRequest instance from a client.

        Args:
            email (str): The email address to be used for registration.

        Returns:
            WestRegistrationRequest: The WestRegistrationRequest instance.
        """
        return WestRegistrationRequest(email=email,
                                       requests_handler=handler)


class WestRegistration:
    """Class for managing the registration process for The West."""

    def __init__(self, client: secmail.Client, handler : RequestsHandler):
        """
        Initialize a WestRegistration object.

        Args:
            client (secmail.Client): The client used for accessing email services.
        """
        self.client = client
        self.handler = handler
        self.confirmer = WestEmailConfirmer(client=client , requests_handler = handler)
        self.account_saver = AccountSaverManager(db_url='sqlite:///accounts.db')
        self.current_registration_request = self._refresh_registration_request()

    def _refresh_registration_request(self) -> WestRegistrationRequest:
        """
        Create a new email for registration.

        Returns:
            WestRegistrationRequest: The new registration request object.
        """
        new_email = self.client.random_email(amount=1)[0]
        return WestRegistrationRequest.from_client(email=new_email,handler=self.handler)

    def refresh_registration_request(self) -> None:
        """Refresh the registration request."""
        if not self.current_registration_request.usable_email:
            self.current_registration_request = self._refresh_registration_request()
        self.handler.renew_tor_connection()

    def register_account(self, account: Account):
        """
        Register an account with the provided credentials.

        Args:
            account (Account): The account object containing the username and password.
        """
        try:
            success_status = self.current_registration_request.register(name=account.name,
                                                                        password=account.password,
                                                                        confirmer=self.confirmer,
                                                                        account_saver = self.account_saver
                                                                        )
            self.refresh_registration_request()
            print(f'Successfully registered the account {account.name} with password {account.password} status : {success_status}')
        except UnsuccessfullRegistrationException:
            print('Could not register this account ! ')
        except Exception as e:
            raise e

