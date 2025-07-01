from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from .config import CLIENT_ID, CLIENT_SECRET
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid email profile'
        },
)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('/welcome')
    return templates.TemplateResponse(
        name="home.html",
        context={"request": request}
    )

@app.get('/welcome')
async def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse('/')
    
    # Debug: Print user data to see the structure
    print("User data:", user)
    
    return templates.TemplateResponse(
        name="welcome.html",
        context={"request": request, "user": user}
    )

@app.get("/login")
async def login(request: Request):
    url = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, url)

@app.route("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name="error.html",
            context={"request": request, "error": e.error}
        )
    user = token.get('userinfo')
    if user:
        # Debug: Print the token and user info structure
        print("Token:", token)
        print("User info:", user)
        request.session['user'] = dict(user)

    return RedirectResponse('/welcome')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse('/')