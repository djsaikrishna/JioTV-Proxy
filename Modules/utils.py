from uuid import uuid4
import m3u8
import socket
import json
import httpx
from os import path


# Constants
IMG_PUBLIC = "https://jioimages.cdn.jio.com/imagespublic/"
IMG_CATCHUP = "https://jiotv.catchup.cdn.jio.com/dare_images/images/"
IMG_CATCHUP_SHOWS = "https://jiotv.catchup.cdn.jio.com/dare_images/shows/"
FEATURED_SRC = (
    "https://tv.media.jio.com/apis/v1.6/getdata/featurednew?start=0&limit=30&langId=6"
)
CHANNELS_SRC_NEW = "https://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?langId=6&os=android&devicetype=phone&usertype=tvYR7NSNn7rymo3F&version=285"
GET_CHANNEL_URL = "https://tv.media.jio.com/apis/v2.0/getchannelurl/getchannelurl?langId=6&userLanguages=All"
CATCHUP_SRC = "https://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?offset={0}&channel_id={1}&langId=6"
M3U_CHANNEL = '\n#EXTINF:0 tvg-id="{tvg_id}" tvg-name="{channel_name}" group-title="{group_title}" tvg-chno="{tvg_chno}" tvg-logo="{tvg_logo}"{catchup},{channel_name}\n{play_url}'
DICTIONARY_URL = "https://jiotvapi.cdn.jio.com/apis/v1.3/dictionary/dictionary?langId=6"
# ---------------------


class JioTV:
    def __init__(self) -> None:
        self.auth_headers = {}
        self.channel_headers = {}

        if path.exists(path.join("data", "jio_headers.json")):
            self.auth_headers = json.load(
                open(path.join("data", "jio_headers.json"), "r")
            )
            self.channel_headers = {
                "ssotoken": self.auth_headers["ssotoken"],
                "userId": self.auth_headers["userid"],
                "uniqueId": self.auth_headers["uniqueid"],
                "crmid": self.auth_headers["crmid"],
                "user-agent": "plaYtv/7.0.8 (Linux;Android 9) ExoPlayerLib/2.11.7",
                "deviceid": self.auth_headers["deviceId"],
                "devicetype": "phone",
                "os": "android",
                "osversion": "9",
            }

    def update_headers(self):
        self.auth_headers = json.load(open(path.join("data", "jio_headers.json"), "r"))
        self.channel_headers = {
            "ssotoken": self.auth_headers["ssotoken"],
            "userId": self.auth_headers["userid"],
            "uniqueId": self.auth_headers["uniqueid"],
            "crmid": self.auth_headers["crmid"],
            "user-agent": "plaYtv/7.0.8 (Linux;Android 9) ExoPlayerLib/2.11.7",
            "deviceid": self.auth_headers["deviceId"],
            "devicetype": "phone",
            "os": "android",
            "osversion": "9",
        }

    def get_local_ip(self):
        """
        Retrieves the local IP address of the machine.

        Returns:
            str: The local IP address of the machine.
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(("8.8.8.8", 80))
            IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    async def get_channels(self):
        """
        Retrieves channels from the specified source and saves them to a JSON file.

        This function sends a GET request to the CHANNELS_SRC_NEW endpoint with the specified headers. It retrieves the JSON response and extracts the 'result' field. The extracted data is then saved to a JSON file located at 'data/channels.json'.

        Parameters:
        None

        Returns:
        None
        """

        headers = {
            "Accept": "*/*",
            "User-Agent": "plaYtv/7.0.8 (Linux;Android 7.1.2) ExoPlayerLib/2.11.7",
        }

        response = await httpx.AsyncClient().get(CHANNELS_SRC_NEW, headers=headers)
        response = response.json()["result"]
        with open(r"data\channels.json", "w") as f:
            json.dump(response, f, ensure_ascii=False, indent=4)

    def sendOTP(self, mobile):
        body = {
            "identifier": mobile,
            "otpIdentifier": mobile,
            "action": "otpbasedauthn",
        }
        resp = httpx.post(
            "https://api.jio.com/v3/dip/user/otp/send",
            json=body,
            headers={"x-api-key": "l7xx75e822925f184370b2e25170c5d5820a"},
        )
        if resp.status_code != 204:
            return "[FAILED]"
        else:
            return "[SUCCESS]"

    def login(self, email, password, mode="unpw"):
        """
        Logs in a user with the given email and password.

        Args:
            email (str): The email address of the user.
            password (str): The password of the user.

        Returns:
            str: The success or failure message.
        """
        body = {
            "identifier": email,
            "password" if mode == "unpw" else "otp": password,
            "rememberUser": "T",
            "upgradeAuth": "Y",
            "returnSessionDetails": "T",
            "deviceInfo": {
                "consumptionDeviceName": "ZUK Z1",
                "info": {
                    "type": "android",
                    "platform": {"name": "ham", "version": "8.0.0"},
                    "androidId": str(uuid4()),
                },
            },
        }

        resp = httpx.post(
            f"https://api.jio.com/v3/dip/user/{mode}/verify",
            json=body,
            headers={
                "User-Agent": "JioTV",
                "x-api-key": "l7xx75e822925f184370b2e25170c5d5820a",
                "Content-Type": "application/json",
            },
        )

        resp = resp.json()

        if resp.get("ssoToken", "") != "":
            _CREDS = {
                "ssotoken": resp.get("ssoToken"),
                "userid": resp.get("sessionAttributes", {}).get("user", {}).get("uid"),
                "uniqueid": resp.get("sessionAttributes", {})
                .get("user", {})
                .get("unique"),
                "crmid": resp.get("sessionAttributes", {})
                .get("user", {})
                .get("subscriberId"),
                "subscriberid": resp.get("sessionAttributes", {})
                .get("user", {})
                .get("subscriberId"),
            }

            headers = {
                "deviceId": str(uuid4()),
                "devicetype": "phone",
                "os": "android",
                "osversion": "9",
                "user-agent": "plaYtv/7.0.8 (Linux;Android 9) ExoPlayerLib/2.11.7",
                "usergroup": "tvYR7NSNn7rymo3F",
                "versioncode": "289",
                "dm": "ZUK ZUK Z1",
            }

            headers.update(_CREDS)

            with open("data/jio_headers.json", "w") as f:
                json.dump(headers, f, indent=4)

            return "[SUCCESS]"
        else:
            return "[FAILED]"

    async def get_key(self, uri, cid, cookie):
        """
        Retrieves a key from the specified URI using the provided channel ID and cookie.

        Parameters:
            uri (str): The URI from which to retrieve the key.
            cid (int): The channel ID to use in the request headers.
            cookie (str): The cookie to include in the request headers.

        Returns:
            bytes: The retrieved key as bytes.
        """
        headers = self.auth_headers
        headers["channelid"] = str(cid)
        headers["srno"] = str(uuid4())
        headers["cookie"] = cookie
        headers["Content-type"] = "application/octet-stream"

        resp = await httpx.AsyncClient().get(uri, headers=headers)
        resp = resp.content
        return resp

    async def get_ts(self, uri, cid, cookie):
        """
        Retrieves the content from a given URI using the GET method and returns the response content.

        Args:
            uri (str): The URI to retrieve content from.
            cid (int): The channel ID.
            cookie (str): The cookie value.

        Returns:
            bytes: The response content.
        """
        headers = self.auth_headers
        headers["channelid"] = str(cid)
        headers["srno"] = str(uuid4())
        headers["cookie"] = cookie

        resp = await httpx.AsyncClient().get(uri, headers=headers)
        return resp.content

    async def get_audio(self, uri, cid, cookie):
        """
        Generate the audio m3u8 playlist with modified URLs.

        Args:
            uri (str): The URI of the original m3u8 playlist.
            cid (str): The cid value for the request.
            cookie (str): The cookie value for the request.

        Returns:
            str: The modified audio m3u8 playlist.
        """
        base_url = uri.split("/")
        base_url.pop()
        base_url = "/".join(base_url)

        audio_m3u8 = await self.get_ts(uri, cid, cookie)
        audio_m3u8 = audio_m3u8.decode()

        parsed_audio_m3u8 = m3u8.loads(audio_m3u8)

        for segment in parsed_audio_m3u8.segments:
            audio_m3u8 = audio_m3u8.replace(
                segment.uri,
                f"/get_ts?uri={base_url}/{segment.uri}&cid={cid}&cookie={cookie}",
            )

        for key in parsed_audio_m3u8.keys:
            if key is not None:
                audio_m3u8 = audio_m3u8.replace(
                    key.uri, f"/get_key?uri={key.uri}&cid={cid}&cookie={cookie}"
                )

        return audio_m3u8

    async def get_vtt(self, uri, cid, cookie):
        resp = await self.get_ts(uri, cid, cookie)
        resp = resp.decode()
        return resp

    async def get_subs(self, uri, cid, cookie):
        """
        Retrieves the subdomains for a given URI.

        Parameters:
            uri (str): The URI for which to retrieve the subdomains.
            cid (str): The client ID associated with the request.
            cookie (str): The authentication cookie.

        Returns:
            str: Gets subtitles URI.
        """
        base_url = uri.split("/")
        base_url.pop()
        base_url = "/".join(base_url)

        resp = await self.get_ts(uri, cid, cookie)
        resp = resp.decode()
        parsed_subs = m3u8.loads(resp)

        for segment in parsed_subs.segments:
            resp = resp.replace(
                segment.uri,
                f"/get_vtt?uri={base_url}/{segment.uri.replace('.webvtt','.vtt')}&cid={cid}&cookie={cookie}",
            )

        return resp

    async def get_channel_url(self, channel_id):
        """
        Retrieves the URL of a channel based on its ID.

        Args:
            channel_id (int): The ID of the channel.

        Returns:
            str: The URL of the channel with various query parameters appended.

        Raises:
            None: Does not raise any exceptions.
        """
        rjson = {"channel_id": int(channel_id), "stream_type": "Seek"}
        resp = await httpx.AsyncClient().post(
            GET_CHANNEL_URL, headers=self.channel_headers, json=rjson
        )

        resp = resp.json()

        onlyUrl = resp.get("bitrates", "").get("high", "")

        base_url = onlyUrl.split("?")[0].split("/")
        base_url.pop()
        base_url = "/".join(base_url)

        cookie = "__hdnea__" + resp.get("result", "").split("__hdnea__")[-1]

        first_m3u8 = await httpx.AsyncClient().get(
            onlyUrl, headers=self.channel_headers
        )
        first_m3u8 = first_m3u8.text

        firast_m3u8_parsed = m3u8.loads(first_m3u8)

        final_ = first_m3u8
        for playlist in firast_m3u8_parsed.playlists:
            final_ = final_.replace(
                playlist.uri,
                f"/play?uri={base_url}/{playlist.uri}&cid={channel_id}&cookie={cookie}",
            )

        for media in firast_m3u8_parsed.media:
            if media.type == "SUBTITLES":
                final_ = final_.replace(
                    media.uri,
                    f"/get_subs?uri={base_url}/{media.uri}&cid={channel_id}&cookie={cookie}",
                )

        for media in firast_m3u8_parsed.media:
            if media.type == "AUDIO" and media.uri is not None:
                final_ = final_.replace(
                    media.uri,
                    f"/get_audio?uri={base_url}/{media.uri}&cid={channel_id}&cookie={cookie}",
                )

        return final_

    async def final_play(self, uri, cid, cookie):
        """
        Fetches and processes a playlist file from the given URI.

        Args:
            uri (str): The URI of the playlist file.
            cid (str): The channel ID.
            cookie (str): The cookie value.

        Returns:
            str: The processed playlist file.

        Raises:
            None
        """
        headers = self.auth_headers
        headers["channelid"] = str(cid)
        headers["srno"] = str(uuid4())
        headers["cookie"] = cookie

        resp = await httpx.AsyncClient().get(uri, headers=headers)
        resp = resp.text

        parsed_m3u8 = m3u8.loads(resp)

        base_url = uri.split("/")
        base_url.pop()
        base_url = "/".join(base_url)

        temp_text = resp

        for segment in parsed_m3u8.segments:
            temp_text = temp_text.replace(
                segment.uri,
                f"/get_ts?uri={base_url}/{segment.uri}&cid={cid}&cookie={cookie}",
            )

        for key in parsed_m3u8.keys:
            if key is not None:
                temp_text = temp_text.replace(
                    key.uri, f"/get_key?uri={key.uri}&cid={cid}&cookie={cookie}"
                )

        return temp_text

    async def get_playlists(self, host):
        url = "https://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone"
        response = await httpx.AsyncClient().get(url)
        response = response.json()

        channels = response["result"]

        lang_id = {
            6: "English",
            1: "Hindi",
            2: "Marathi",
            3: "Punjabi",
            4: "Urdu",
            5: "Bengali",
            7: "Malayalam",
            8: "Tamil",
            9: "Gujarati",
            10: "Odia",
            11: "Telugu",
            12: "Bhojpuri",
            13: "Kannada",
            14: "Assamese",
            15: "Nepali",
            16: "French",
        }

        genre_id = {
            8: "Sports",
            5: "Entertainment",
            6: "Movies",
            12: "News",
            13: "Music",
            7: "Kids",
            9: "Lifestyle",
            10: "Infotainment",
            15: "Devotional",
            0x10: "Business",
            17: "Educational",
            18: "Shopping",
            19: "JioDarshan",
        }

        m3u8 = """#EXTM3U"""

        for channel in channels:
            channel_id = channel["channel_id"]
            channel_logo = (
                "http://jiotv.catchup.cdn.jio.com/dare_images/images/"
                + channel["logoUrl"]
            )
            channel_name = channel["channel_name"]
            channel_genre = genre_id[channel["channelCategoryId"]]

            # if (
            #     "sony" not in channel_logo.lower()
            #     and "sony" not in channel["channel_name"].lower()
            # ):
            m3u8 += f'#EXTINF:-1 tvg-id="{channel_id}" group-title="{channel_genre}" tvg-logo="{channel_logo}",{channel_name}\nhttp://{host}/m3u8?cid={channel_id}\n'

        return m3u8.strip()
