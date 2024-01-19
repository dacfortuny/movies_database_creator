# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import datetime
import gzip
import os
import pandas as pd

from urllib.request import urlretrieve
# -

# # Settings

# ## Input

URL_DATASETS = "https://datasets.imdbws.com/"
DATA_FOLDER = "data"
FILE_TITLE_BASICS = "title.basics.tsv.gz"
FILE_TITLE_AKAS = "title.akas.tsv.gz"

# ## Output

MOVIES_FILE = "movies"
TITLES_FILE = "titles"
GENRES_FILE = "genres"
GENRES_NAMES_FILE = "genres_names"


# # Functions

# +
def show_progress(block_num, block_size, total_size):
    print(round(block_num * block_size / total_size *100,2), end="\r")
    
def download_file(url, destination):
    print(f"Downloading {destination} from {url}")
    output_folder = os.path.abspath(os.path.dirname(destination))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    urlretrieve(url, destination, show_progress)

def read_file(file):
    return pd.read_csv(file, compression="gzip", sep="\t", low_memory=False)

def retrieve_data(file):
    file_path = f"{DATA_FOLDER}/{file}"
    if not os.path.exists(file_path):
        url = f"{URL_DATASETS}{file}"
        download_file(url, file_path)
    return read_file(file_path)

def get_current_year():
    return str(datetime.date.today().year)

def get_date_string():
    current_date = datetime.datetime.now()
    return current_date.strftime("%Y%m%d")

def save_file(df, file):
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    file = f"{DATA_FOLDER}/{get_date_string()}_{file}.csv"
    df.to_csv(file, index=False, sep="|", encoding="utf-8")


# -

# # Retrieve data

title_basics = retrieve_data(FILE_TITLE_BASICS)
title_basics.head()

title_akas = retrieve_data(FILE_TITLE_AKAS)
title_akas.head()

# # Processing

# +
movies = title_basics.copy()

# Only movies
movies = movies[movies["titleType"] == "movie"].reset_index(drop=True)

# Filter non-wanted movies
movies = movies[movies["isAdult"] == "0"].reset_index(drop=True)
movies = movies[movies["startYear"] < get_current_year()].reset_index(drop=True)

# Create genres table and dictionary
genres = movies[["tconst", "genres"]].copy()
genres["genres"] = genres["genres"].str.split(",") 
genres = genres.explode("genres").reset_index(drop=True)
genres = genres[genres["genres"] != "\\N"].reset_index(drop=True)
genres = genres.rename(columns={"tconst": "id_movie", "genres": "genre"})
genres_dict = genres[["genre"]].drop_duplicates().sort_values("genre").reset_index(drop=True).reset_index(names="id_genre")
genres = genres.merge(genres_dict)
genres = genres.sort_values("id_movie").reset_index(drop=True)
del genres["genre"]
genres_dict = genres_dict[["id_genre", "genre"]]

# Keep necessary columns
movies = movies[["tconst", "originalTitle", "startYear", "runtimeMinutes"]]
movies = movies.rename(columns={"tconst": "id_movie", "originalTitle": "title_original", "startYear": "year", "runtimeMinutes": "duration"})
movies["year"] = movies["year"].replace("\\N", "")
movies["duration"] = movies["duration"].replace("\\N", "")

# Create titles table
titles = title_akas.copy()
titles = titles[titles["titleId"].isin(movies["id_movie"])].reset_index(drop=True)
titles = titles[titles["region"] == "ES"].reset_index(drop=True)
titles = titles[titles["language"].isin(["ca", "es"])].reset_index(drop=True)
titles = titles[["titleId", "language", "title"]]
titles = titles.rename(columns={"titleId": "id_movie"})
titles = titles.sort_values("id_movie")
# -

# # Export

save_file(movies, MOVIES_FILE)
save_file(titles, TITLES_FILE)
save_file(genres, GENRES_FILE)
save_file(genres_dict, GENRES_NAMES_FILE)
