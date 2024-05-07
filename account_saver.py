from sqlalchemy import create_engine,delete
from sqlalchemy.orm import sessionmaker
from accounts_models import Base, Account_db

class AccountSaverManager:
    def __init__(self, db_url: str):
        """
        Initialize the AccountSaverManager.

        Args:
            db_url (str): The URL of the database.
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        # Create the tables if they don't exist
        Base.metadata.create_all(self.engine)

    def save_account(self, account: Account_db):
        """
        Save an account to the database.

        Args:
            account (Account_db): The account to be saved.
        """
        session = self.Session()
        session.add(account)
        session.commit()
        session.close()

    def mark_account_as_activated(self, account_name: str):
        """
        Mark an account as activated in the database.

        Args:
            account_name (str): The name of the account to be marked as activated.
        """
        session = self.Session()
        account = session.query(Account_db).filter(Account_db.name == account_name).first()
        if account:
            account.is_activated = True
            session.commit()
        session.close()
    def delete_inactive_accounts(self):
        """
        Delete records where is_activated is False.
        """
        with self.Session() as session:
            try:
                session.execute(delete(Account_db).where(Account_db.is_activated == False))
                session.commit()
            except Exception as e:
                session.rollback()
                raise e