from quart import Quart, request, redirect
import aiohttp
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Quart(__name__)

CLIENT_ID = "1510361485199671566"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # put this in your .env!
REDIRECT_URI = "http://localhost:5000/callback"
FIREBASE_URL = "https://roblox-control-52d72-default-rtdb.firebaseio.com/"

@app.route('/login')
def login():
    roblox_user = request.args.get('roblox_user', 'Unknown')
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify+email"
        f"&state={roblox_user}"
    )
    return redirect(discord_oauth_url)

@app.route('/callback')
async def callback():
    code = request.args.get('code')
    roblox_user = request.args.get('state', 'Unknown')

    if not code:
        return "❌ Authorization canceled or missing code.", 400

    async with aiohttp.ClientSession() as session:
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        async with session.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers) as resp:
            token_json = await resp.json()
            access_token = token_json.get('access_token')

        if not access_token:
            return "❌ Failed to retrieve access token from Discord.", 400

        user_headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get('https://discord.com/api/v10/users/@me', headers=user_headers) as user_resp:
            user_data = await user_resp.json()

    discord_id = user_data.get('id')
    discord_tag = user_data.get('username')
    user_email = user_data.get('email', 'No Email Provided')

    payload = {
        "DiscordID": discord_id,
        "DiscordTag": discord_tag,
        "Email": user_email
    }

    firebase_req = requests.put(f"{FIREBASE_URL}linked_accounts/{roblox_user.lower()}.json", json=payload)

    if firebase_req.status_code == 200:
        return f"<h3>✅ Success! Your Roblox profile ({roblox_user}) is now linked to Discord account {discord_tag}. You can close this tab.</h3>"
    else:
        return "❌ Linked successfully, but failed to write records to Firebase.", 500

if __name__ == '__main__':
    app.run(port=5000)