import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_service_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    expected_token = os.getenv("AI_SERVICE_SECRET")
    
    if not expected_token:
        if os.getenv("ENVIRONMENT", "production").lower() == "development":
            print("WARNING: AI_SERVICE_SECRET is not set; development bypass enabled")
            return True
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service authentication is not configured",
        )
        
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
