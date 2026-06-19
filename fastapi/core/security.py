from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from core.config import settings

security = HTTPBearer()

def verify_supabase_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the Supabase JWT token.
    In Phase 1, Supabase JS handles this. In Phase 2, FastAPI acts as an API 
    so it must verify tokens using the Supabase JWT Secret.
    """
    token = credentials.credentials
    try:
        # Decode the token using the Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin(payload: dict = Depends(verify_supabase_jwt)):
    """
    Ensure the token belongs to an admin.
    Since role is in the custom 'profiles' table, we might need a DB call,
    but Supabase allows injecting custom claims into JWT via auth hooks if configured.
    For now, mock checking.
    """
    # TODO: Verify admin role from DB if not in JWT claims
    return payload
