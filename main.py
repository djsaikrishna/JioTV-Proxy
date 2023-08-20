import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, JSONResponse

from fastapi.templating import Jinja2Templates

from Modules.utils import *
from time import time

from os import path

import sqlite3
import logging

logger = logging.getLogger("uvicorn")


def store_creds(email, password, expire_time):
    # Store the credentials along with expire time in sqlite
    db = sqlite3.connect("creds.db")
    cursor = db.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS creds(
        email TEXT,
        password TEXT,
        expire NUMERIC
    )"""
    )
    cursor.execute(
        """INSERT INTO creds VALUES(?,?,?)""", (email, password, expire_time)
    )
    db.commit()
    db.close()


def get_expire():
    db = sqlite3.connect("creds.db")
    cursor = db.cursor()
    cursor.execute("""SELECT expire FROM creds""")
    expire_time = cursor.fetchone()[0]
    db.close()
    return expire_time


def clear_creds():
    db = sqlite3.connect("creds.db")
    cursor = db.cursor()
    cursor.execute("""DELETE FROM creds""")
    db.commit()
    db.close()


def get_creds():
    db = sqlite3.connect("creds.db")
    cursor = db.cursor()
    cursor.execute("""SELECT email,password FROM creds""")
    creds_ = cursor.fetchone()
    db.close()
    return creds_


def create_creds():
    db = sqlite3.connect("creds.db")
    cursor = db.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS creds(
        email TEXT,
        password TEXT,
        expire NUMERIC
    )"""
    )
    db.commit()
    db.close()


def check_session():
    """
    Check if the user is logged in and if the session has expired.

    Returns:
        - "ALL OK" if the user is logged in and the session has not expired.
        - "Expired" if the user is logged in but the session has expired.
        - "Not Logged In" if the user is not logged in.
    """

    expire_time = (
        get_expire() if path.exists(path.join("data", "jio_headers.json")) else 0
    )
    current_time = time()

    if (
        path.exists(path.join("data", "jio_headers.json"))
        and expire_time > current_time
    ):
        return "ALL OK"

    elif (
        path.exists(path.join("data", "jio_headers.json"))
        and expire_time < current_time
    ):
        logger.warning("[!] Session has expired and auto relogin initiated.")

        email, password = get_creds()
        login(email, password)

        return "Expired"

    else:
        logger.warning(f"Not Logged In. Go to http://{get_local_ip()}:8000/login")
        return "Not Logged In"


def welcome_msg():
    server_ip = get_local_ip()
    print("===================================================")
    print("Welcome to JioTV-Proxy")
    print("Version 1.3")
    print(f"Please Login at http://{server_ip}:8000/login")
    print(f"Playlist: http://{server_ip}:8000/playlist.m3u")
    print("===================================================")
    print()


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.middleware("http")
async def middleware(request: Request, call_next):
    """
    Middleware function that intercepts incoming HTTP requests and performs certain actions based on the request path.

    Parameters:
        - request (Request): The incoming HTTP request object.
        - call_next (Callable): The next middleware or route handler to call.

    Returns:
        - Response: The HTTP response object to be sent back to the client.
    """
    if request.url.path in ["/login", "/playlist.m3u", "/createToken"]:
        response = await call_next(request)
        return response

    elif check_session() == "Not Logged In":
        return JSONResponse(
            content={
                "status_code": 403,
                "error": "Session not authenticated.",
                "details": f"Seems like you are not logged in, please login by going to http://{get_local_ip}:8000/login",
            },
            status_code=403,
        )

    else:
        check_session()
        response = await call_next(request)
        return response


@app.get("/createToken")
def createToken(email, password):
    """
    A function that creates a token for the given email and password.

    Parameters:
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        str: The login response containing the token.
    """
    if path.exists(path.join("creds.db")):
        logger.warning("[!] Creds already available. Clearing existing creds.")
        clear_creds()

    else:
        logger.info("[-] First Time Logging in.")

    login_response = login(email, password)
    if login_response == "[SUCCESS]":
        store_creds(email, password, time() + 432000)
        return login_response

    return login_response


@app.get("/login")
async def loginJio(request: Request):
    """
    Get the login page.

    Parameters:
        request (Request): The HTTP request object.

    Returns:
        TemplateResponse: The response containing the login page HTML template.
    """
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/playlist.m3u")
async def get_playlist(request: Request):
    """
    Retrieves a playlist in the form of an m3u file.

    Returns:
        A PlainTextResponse object containing the playlist in the specified media type.
    """
    return PlainTextResponse(
        get_playlists(request.headers.get("host")), media_type="application/x-mpegurl"
    )


@app.get("/m3u8")
async def get_m3u8(cid):
    """
    Retrieves the m3u8 playlist for a given channel ID.

    Parameters:
    - cid: The ID of the channel to retrieve the m3u8 playlist for. (type: any)

    Returns:
    - The m3u8 playlist for the specified channel. (type: PlainTextResponse)
    """
    return PlainTextResponse(get_channel_url(cid), media_type="application/x-mpegurl")


@app.get("/get_audio")
async def get_multi_audio(uri, cid, cookie):
    """
    A function that handles the GET request to retrieve audio.

    Parameters:
    - uri (str): The URI of the audio.
    - cid (str): The CID (Client ID) of the audio.
    - cookie (str): The cookie associated with the audio.

    Returns:
    - Response: The response object containing the audio.
    """
    return Response(get_audio(uri, cid, cookie), media_type="application/x-mpegurl")


@app.get("/get_subs")
async def get_subtitles(uri, cid, cookie):
    """
    Retrieves subtitles for a given URI using the specified CID and cookie.

    Args:
        uri (str): The URI for which to retrieve subtitles.
        cid (str): The CID associated with the URI.
        cookie (str): The cookie required for authentication.

    Returns:
        str: The subtitles for the specified URI.

    """
    return Response(get_subs(uri, cid, cookie))


@app.get("/get_ts")
async def get_tts(uri, cid, cookie):
    """
    A function that handles GET requests to the "/get_ts" endpoint.

    Parameters:
    - uri (str): The URI for the request.
    - cid (str): The CID for the request.
    - cookie (str): The cookie for the request.

    Returns:
    - Response: Gets the segments from the specified URI.
    """
    return Response(get_ts(uri, cid, cookie), media_type="video/MP2T")


@app.get("/get_key")
async def get_keys(uri, cid, cookie):
    """
    Retrieves a key from the specified URI using the provided CID and cookie.

    Parameters:
    - uri (str): The URI from which to retrieve the key.
    - cid (str): The CID associated with the key.
    - cookie (str): The cookie to use for authentication.

    Returns:
    - Response: The response containing the DRM key.
    """
    return Response(get_key(uri, cid, cookie), media_type="application/octet-stream")


@app.get("/play")
async def play(uri, cid, cookie):
    """
    This function is a route handler for the "/play" endpoint of the API. It expects three parameters:

    - `uri`: A string representing the URI.
    - `cid`: A string representing the CID.
    - `cookie`: A string representing the cookie.

    The function calls the `final_play` function passing in the `uri`, `cid`, and `cookie` parameters, and returns the result as a `PlainTextResponse` object with the media type set to "application/x-mpegurl".

    Returns:
    - A `PlainTextResponse` object with the media type set to "application/x-mpegurl".
    """
    return PlainTextResponse(
        final_play(uri, cid, cookie), media_type="application/x-mpegurl"
    )


if __name__ == "__main__":
    welcome_msg()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")