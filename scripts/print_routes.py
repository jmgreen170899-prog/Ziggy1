from app.main import app
from fastapi.routing import APIRoute

for r in app.routes:
    if isinstance(r, APIRoute):
        print(f"{','.join(r.methods):8} {r.path}  tags={r.tags}  include_in_schema={r.include_in_schema}")