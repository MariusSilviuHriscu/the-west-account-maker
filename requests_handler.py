import typing
import requests
from functools import wraps

#from tor_handler import create_tor_handler

from connection_sessions.tor_handler import create_tor_session

from connection_sessions.standard_request_session import StandardRequestsSession

class RequestsHandler():
    
    def __init__(self,session : requests.Session | StandardRequestsSession ):
        
        self.session = session
        
        
    def get(self , url : str , params : dict[str,str] = None):
            
        if not params :
            params = {}
        if url.startswith('ttps') :
            url = 'h' + url
        response = self.session.get(url = url ,data=params)
        
        if response.status_code != 200:
            
            raise Exception('something went wrong')
        return response
    
    def get_full_response(self , url : str , params : dict[str,str] = None):
        
        if not params :
            params = {}
        
        response = self.session.get(url = url ,data=params)
        
        if response.status_code != 200:
            
            raise Exception('something went wrong')
        
        return response
    def post(self , url : str , params : dict[str,str] = None):
        if url.startswith('ttps') :
            url = 'h' + url
        if not params :
            params = {}
        
        response = self.session.post(url,data=params)
        
        
        if response.status_code != 200:
            
            raise Exception('something went wrong')
        
        return response

    def renew_connection(self):
        if not isinstance(self.session, requests.Session):
            self.session.new_connection()

def create_requests_handler(session_builder_func : typing.Callable[[],StandardRequestsSession|requests.Session]) -> RequestsHandler:
        
    session = session_builder_func()
    return RequestsHandler(session = session
                            )