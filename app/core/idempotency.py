from functools import wraps
from datetime import datetime, timezone, timedelta
import json
from sqlalchemy import select
from fastapi import Depends, Header, HTTPException
from typing import Optional

from ..database.session import AsyncSessionLocal
from ..models.idempotency import IdempotencyKey

def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

async def check_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
) -> Optional[str]:
    if idempotency_key and len(idempotency_key) > 255:
        raise HTTPException(
            status_code=400,
            detail="Idempotency key must be less than 255 characters"
        )
    return idempotency_key

def idempotent_operation(ttl_hours: int = 24):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            idempotency_key = kwargs.get('idempotency_key')
            if not idempotency_key:
                return await func(*args, **kwargs)
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
                )
                existing_key = result.scalars().first()
                
                if existing_key:
                    if existing_key.expires_at < datetime.now(timezone.utc):
                        await session.delete(existing_key)
                        await session.commit()
                    else:
                        return json.loads(existing_key.response)
                
                response = await func(*args, **kwargs)
                
                idempotency_record = IdempotencyKey(
                    key=idempotency_key,
                    endpoint=func.__name__,
                    response=json.dumps(response, default=datetime_handler),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                )
                session.add(idempotency_record)
                await session.commit()
                
                return response
        return wrapper
    return decorator