# File: C:/Users/Jamie/workspace/epos_mcp/containers/context-server/server.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
print('Service context-server starting...')
from fastapi import FastAPI
app=FastAPI()
@app.get('/health')
async def h(): return {'status':'ok'}
