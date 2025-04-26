from sqlalchemy import select

from ..database.session import AsyncSessionLocal
from ..models.user import User
from ..models.device import Device
from ..core.auth import get_password_hash
from ..config import DEVICES

async def initialize_database():
    async with AsyncSessionLocal() as session:
        # Create initial admin user if no users exist
        result = await session.execute(select(User))
        if not result.scalars().first():
            admin_user = User(
                name="admin",
                cash=0,
                hashed_password=get_password_hash("admin"),
                is_admin=True
            )
            session.add(admin_user)
        
        # Initialize or update devices from config
        for device_config in DEVICES:
            result = await session.execute(
                select(Device).where(Device.id == device_config["id"])
            )
            device = result.scalars().first()
            
            if not device:
                device = Device(id=device_config["id"])
                session.add(device)
        
        # Remove devices that are no longer in config
        result = await session.execute(select(Device))
        existing_devices = result.scalars().all()
        config_device_ids = [d["id"] for d in DEVICES]
        
        for device in existing_devices:
            if device.id not in config_device_ids:
                await session.delete(device)
        
        await session.commit()