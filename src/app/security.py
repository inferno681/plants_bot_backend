from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login_doc')
oauth2_dependency = Depends(oauth2_scheme)
