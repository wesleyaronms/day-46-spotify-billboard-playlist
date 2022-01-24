from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import spotipy
import os


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SPOTIFY_USER = os.getenv("SPOTIFY_USER")


def get_date():
    """Input: DD/MM/AAAA; Return: self[0] = AAAA-MM-DD, self[1] = DD/MM/AAAA"""
    date_format = "%d/%m/%Y"
    user_input = input("Para qual ano você gostaria de viajar? Por favor, digite no formato DD/MM/YYYY:\n")
    while True:
        try:
            datetime.strptime(user_input, date_format)
            day = user_input.split("/")[0]
            month = user_input.split("/")[1]
            year = user_input.split("/")[2]
            return [f"{year}-{month}-{day}", user_input]
        except ValueError:
            print("Desculpe, formato de data inválido. Exemplo de data válido: 19/04/2022\n")
            user_input = input("Tente novamente:\n")


date = get_date()


response = requests.get(f"https://www.billboard.com/charts/hot-100/{date[0]}")
response.raise_for_status()
web_page = response.text


# playlist = [[Artista, Nome da Música], ...]; Top 100 da Billboard na data específica.
playlist = []

soup = BeautifulSoup(web_page, "html.parser")
for songs in soup.find_all(name="li", class_="o-chart-results-list__item"):
    try:
        song = songs.find(name="h3", id="title-of-a-story")
        song_text = song.getText().strip("\n").lower()
        artist = songs.find(name="span", class_="c-label")
        artist_text = artist.getText().strip("\n").lower()
        playlist.append([artist_text, song_text])
    except AttributeError:
        pass

# Remover esses caracteres ajuda a encontrar mais resultados
remove = ["featuring", "feat", ",", "&", "duet", "+", "duo", "'", "/", "with"]

for track in playlist:
    for i in remove:
        track[0].replace(i, "")
        track[1].replace(i, "")
    if len(track[0].split()) > 3:
        track[0] = " ".join(track[0].split()[:3])


playlist_parameters = {
    "user": SPOTIFY_USER,
    "name": f"{date[1]} Billboard's Top 100",
}

scope = "playlist-modify-public playlist-modify-private"
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=scope,
                        show_dialog=False)

sp = spotipy.Spotify(auth_manager=sp_oauth)


playlist_ids = []
# Retorna o id da música, se encontrar.
for song in playlist:
    track = sp.search(q=f"{song[1]} {song[0]}", type="track", limit="1")
    try:
        playlist_ids.append(track["tracks"]["items"][0]["id"])
    except IndexError:
        pass

# Cria a playlist.
sp.user_playlist_create(user=playlist_parameters["user"], name=playlist_parameters["name"])

# Insere no playlist_parameters o id da playlist criada.
user_playlists = sp.user_playlists(user=playlist_parameters["user"])

for playlist in user_playlists["items"]:
    if playlist["name"] == playlist_parameters["name"]:
        playlist_parameters["id"] = playlist["id"]
        break


# Adiciona as música à playlist criada
sp.playlist_add_items(playlist_id=playlist_parameters["id"], items=playlist_ids)

print(f"Aqui está a playlist:\nhttps://open.spotify.com/playlist/{playlist_parameters['id']}\n"
      f"E aqui a página da Billboard:\nhttps://www.billboard.com/charts/hot-100/{date[0]}")
