# File: /mnt/c/Users/Jamie/workspace/epos_mcp/containers/governance-gate/server.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
print('Service governance-gate starting...')
from fastapi import FastAPI
app=FastAPI()
@app.get('/health')
async def h(): return {'status':'ok'}
