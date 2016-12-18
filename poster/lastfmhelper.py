class LastFmHelper(object):

    def __init__(self, user, cols, rows, time):
        self.user = user
        self.cols = cols
        self.rows = rows
        self.time = time
        self.span_sized = "span" + str(12 / cols)
        self.numTiles = self.rows * self.cols

    # Create based on class name:
    def factory(sort_type, user, cols, rows, time):
        if sort_type == "Album": return AlbumHelper(user, cols, rows, time)
        if sort_type == "Artist": return ArtistHelper(user, cols, rows, time)
        assert 0, "Bad LastFmHelper creation: " + sort_type
    factory = staticmethod(factory)

class AlbumHelper(LastFmHelper):
    def create_context(self):
        topAlbums = self.user.get_top_albums(limit=self.numTiles, period=self.time)
        context = {}
        context['artist_rows'] = {}
        context['span_sized'] = self.span_sized
        for i in range(self.rows):
            newRow = {}
            for j in range(self.cols):
                album = topAlbums[i * self.cols + j].item
                newRow[j] = {album.get_name() : album.get_cover_image()}
            context['artist_rows'][i] = newRow
        return context


class ArtistHelper(LastFmHelper):
    def create_context(self):
        topArtists = self.user.get_top_artists(limit=self.numTiles, period=self.time)
        context = {}
        context['artist_rows'] = {}
        context['span_sized'] = self.span_sized
        for i in range(self.rows):
            newRow = {}
            for j in range(self.cols):
                artist = topArtists[i * self.cols + j].item
                newRow[j] = {artist.get_name() : artist.get_cover_image()}
            context['artist_rows'][i] = newRow
        return context
