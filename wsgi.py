import os
from app import create_app

# Default to production if not set
env = os.environ.get("FLASK_ENV", "production")
app = create_app(env)

if __name__ == "__main__":
    app.run()
