import pylast
from sets import Set

def get_period_from_string(string):
    if (string == "1 Week"):
        return pylast.PERIOD_7DAYS
    elif (string == "30 Days"):
        return pylast.PERIOD_1MONTH
    elif (string == "90 Days"):
        return pylast.PERIOD_3MONTHS
    elif (string == "180 Days"):
        return pylast.PERIOD_6MONTHS
    elif (string == "1 Year"):
        return pylast.PERIOD_12MONTHS
    elif (string == "All time"):
        return pylast.PERIOD_OVERALL
    else:
        return pylast.PERIOD_OVERALL


# Context is:
# artist_rows : 
#   1 : [{title: url}, {title: url}, ...]
#   2 : ...
# span_sized:
#   12 / cols
def build_poster_template_context(rows, cols, time, spotipy):
    result = spotipy.current_user_top_artists(limit=rows * cols, offset=0, time_range=time)
    artists = get_artist_ids(result)
    context = {}
    context['artist_rows'] = {}
    context['span_sized'] = "span" + str(12 / cols)
    for i in range(rows):
        newRow = {}
        for j in range(cols):
            albums_result = spotipy.artist_albums(artists[i * cols + j][0], album_type='album', country="US", limit=15)
            if (len(albums_result['items']) == 0):
                albums_result = spotipy.artist_albums(artists[i * cols + j][0], limit=5)
            album_data = parse_albums(albums_result)
            newRow[j] = album_data
        context['artist_rows'][i] = newRow
    return context


def build_custom_template_context(rows, cols):
    context = {}
    context['rows'] = range(rows)
    context['cols'] = range(cols)
    context['span_sized'] = "span" + str(12 / cols)
    return context

def parse_albums(albums_result):
    result = {}

    seen = Set()

    for album in albums_result["items"]:
        if (len(album['images']) > 0 and album['images'][0]['url'] not in seen):
            result[album['name']] =  album['images'][0]['url'] if len(album['images']) > 0 else "{% static 'poster/img/default_album.png' %}"
            seen.add(album['images'][0]['url'])
        # print album['name']
        # print album['images'][0]['url']
        # print len(album['images'])
        # TODO default pic for no 
    return result

def get_artist_ids(result):
    artists = []
    for artist in result['items']:
        # print (artist['id'], artist['name'])
        artists.append((artist['id'], artist['name']))
    return artists