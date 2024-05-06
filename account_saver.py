from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from accounts_models import Account

class AccountSaverManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def save_account(self, account: Account):
        session = self.Session()
        session.add(account)
        session.commit()
        session.close()

    def mark_account_as_activated(self, account_name: str):
        session = self.Session()
        account = session.query(Account).filter(Account.name == account_name).first()
        if account:
            account.is_activated = True
            session.commit()
        session.close()