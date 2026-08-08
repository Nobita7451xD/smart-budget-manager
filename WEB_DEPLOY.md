# Smart Budget Manager Web Edition

## Run locally

```powershell
py -m pip install -r web-requirements.txt
py web_app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Create a public link with Render

1. Create a GitHub repository and upload this project.
2. Sign in to [Render](https://render.com) with GitHub.
3. Select **New → Blueprint**, choose the repository, then deploy.
4. Render will show a public `onrender.com` URL. Share that URL with friends.

Important: the default SQLite file is suitable for local demos, but production hosting should use PostgreSQL because a free host can reset local files on redeploy.
