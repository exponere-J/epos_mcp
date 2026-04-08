# File: C:/Users/Jamie/workspace/epos_mcp/containers/learning-server/server.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
print('Service learning-server starting...')
from fastapi import FastAPI
app=FastAPI()
@app.get('/health')
async def h(): return {'status':'ok'}
