import requests
from functools import wraps
from requests.auth import HTTPProxyAuth

from tor_handler import TorSessionHandler,create_tor_handler



class RequestsHandler():
    
    def __init__(self,session:requests.Session,tor_handler : TorSessionHandler|None ):
        
        self.session = session
        self.tor_handler = tor_handler
        
        
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
    
    def get_response_headers(self , url : str , request_type : str, get_data_header : str , params : dict[str,str] = None):
        
        if not params :
            params = {}
        
        response = self.session.request(request_type , url , params)
        
        if response.status_code != 200:
            
            raise Exception('something went wrong')

        return response.headers.get(get_data_header,"")

    def renew_tor_connection(self):
        if self.tor_handler :
            self.tor_handler.renew_connection()
            self.session = self.tor_handler.session

def create_requests_handler() -> RequestsHandler:
        
    tor_handler = create_tor_handler()
    tor_handler.session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer':'https://www.google.com/',
        'X-Requested-With': 'XMLHttpRequest'
        })
    return RequestsHandler(session = tor_handler.session,
                            tor_handler = tor_handler
                            )