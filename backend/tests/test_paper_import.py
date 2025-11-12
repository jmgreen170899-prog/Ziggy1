import sys


sys.path.append("c:/ZiggyClean/backend")

try:
    from app.api.routes_paper import router

    print("SUCCESS: Paper router imported successfully")
    print(f"Router has {len(router.routes)} routes")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
