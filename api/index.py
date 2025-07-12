from app import app

# For Vercel Python serverless function
def handler(environ, start_response):
    return app(environ, start_response)
