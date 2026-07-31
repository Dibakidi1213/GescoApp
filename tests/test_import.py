try:
    import routes.admin
    print("Import successful")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()