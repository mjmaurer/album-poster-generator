import util

class SpotifyHelper(object):

    def __init__(self, spotipy, cols, rows, time):
        self.spotipy = spotipy
        self.cols = cols
        self.rows = rows
        self.time = time
        self.span_sized = "span" + str(12 / cols)
        self.numTiles = self.rows * self.cols

    # Create based on class name:
    def factory(sort_type, spotipy, cols, rows, time):
        if sort_type == "Album": return AlbumHelper(spotipy, cols, rows, time)
        if sort_type == "Artist": return ArtistHelper(spotipy, cols, rows, time)
        assert 0, "Bad SpotifyHelper creation: " + sort_type
    factory = staticmethod(factory)

class AlbumHelper(SpotifyHelper):
    def create_context(self):
        return util.build_poster_template_context(self.rows, self.cols, self.time, self.spotipy)

class ArtistHelper(SpotifyHelper):
    def create_context(self):
        result = self.spotipy.current_user_top_artists(limit=self.rows * self.cols, offset=0, time_range=self.time)
        artists = result['items']
        context = {}
        context['artist_rows'] = {}
        context['span_sized'] = self.span_sized
        for i in range(self.rows):
            newRow = {}
            for j in range(self.cols):
                artist = artists[i * self.cols + j]
                newRow[j] = {artist['name'] : artist['images'][0]['url']}
            context['artist_rows'][i] = newRow
        return context
