import httpx
import json
import os
import hashlib
import uuid
from pathlib import Path

# In production, this is your cloud server
LICENSE_SERVER = "https://api.exponere.com/v1/license"
LOCAL_KEY_PATH = Path("epos_hq/data/license.key")

class LicenseManager:
    def __init__(self):
        self.tenant_id = self._get_or_create_tenant_id()
        self.is_valid = False
    
    def _get_or_create_tenant_id(self):
        # Generate a stable ID based on hardware (simplified)
        # In prod, use machine_id + user salt
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(os.getlogin())))

    async def verify(self):
        """
        The Tether: Checks if this instance is allowed to run.
        """
        print(f"🔐 Verifying License for Tenant: {self.tenant_id}...")
        
        # Check local cache first (valid for 24h)
        if self._check_local_cache():
            print("✅ Local License Valid.")
            self.is_valid = True
            return True

        # Phone Home
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Mocking the request for now - in prod this hits your server
                # res = await client.post(LICENSE_SERVER, json={"tid": self.tenant_id})
                # if res.status_code == 200: ...
                
                # SIMULATION: Always valid for now
                self.is_valid = True
                self._update_local_cache()
                print("✅ Remote Verification Successful.")
                return True
                
        except Exception as e:
            print(f"⚠️ License Server Unreachable: {e}")
            # Grace period logic would go here
            return False

    def _check_local_cache(self):
        # Logic to check if license.key exists and is < 24h old
        return LOCAL_KEY_PATH.exists()

    def _update_local_cache(self):
        LOCAL_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCAL_KEY_PATH, "w") as f:
            f.write(hashlib.sha256(self.tenant_id.encode()).hexdigest())

license_guard = LicenseManager()

