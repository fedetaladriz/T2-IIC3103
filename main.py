from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

ID_LENGTH_LIMIT = 22

# db.drop_all()
#

class Artist(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    albums = db.relationship('Album', backref='artist', lazy=True)

    @property
    def serialize(self):
        
        url = f"{request.url_root}artists/{self.id}"

        return {
        #    'id': self.id,
           'name': self.name, 
           'age': self.age, 
           'self': url,
           'tracks': url + "/tracks",
           'albums': url + "/albums"
       }
    

class Album(db.Model):
    id = db.Column(db.String, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)

    name = db.Column(db.String, nullable=False)
    genre = db.Column(db.Integer, nullable=False)

    tracks = db.relationship('Track', backref='album', lazy=True)

    @property
    def serialize(self):
        
        url = f"{request.url_root}albums/{self.id}"

        return {
        #    'id': self.id,
           'artist_id': self.artist_id,
           'name': self.name, 
           'genre': self.genre, 
           'self': url,
           'tracks': url + "/tracks",
           'artist': f"{request.url_root}artists/{self.artist_id}"
       }
    

class Track(db.Model):
    id = db.Column(db.String, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)

    name = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    times_played = db.Column(db.Integer, nullable=False)

    @property
    def artist(self):
        return self.album.artist

    @property
    def serialize(self):

        return {
        #    'id': self.id,
           'album_id': self.album_id,
           'name': self.name, 
           'duration': self.duration, 
           'times_played': self.times_played, 
           'self': f"{request.url_root}albums/{self.id}",
           'artist': f"{request.url_root}artists/{self.artist.id}",
           'album': f"{request.url_root}albums/{self.album_id}"
       }

db.create_all()



@app.route("/")
def index():
    return "Hello stranger"

###########################
### COMPLETE TABLE
###########################

@app.route('/artists', methods=["GET", "POST"])
def multipleArtists():

    if request.method == "GET":
        result = Artist.query.all()
        return jsonify([item.serialize for item in result]), 200


    elif request.method == "POST":

        if not (request.json.get("name") and\

                isinstance(request.json["name"], str) and\
                request.json.get("age") and\
                isinstance(request.json["age"], int)):
            abort(400)


        id = b64encode(request.json["name"].encode()).decode('utf-8')
        if len(id) > ID_LENGTH_LIMIT:
            id = id[:ID_LENGTH_LIMIT]

        result = Artist.query.get(id)
        
        if result:
            return jsonify(result.serialize), 409


        artist = Artist(id=id,
                        name=request.json["name"],
                        age=request.json["age"]
                        )
                    
        db.session.add(artist)
        db.session.commit()

        return jsonify(artist.serialize), 201


@app.route("/albums", methods=["GET"])
def multipleAlbums():

    result = Album.query.all()
    
    return jsonify([item.serialize for item in result]), 200
    

@app.route("/tracks", methods=["GET"])
def multipleTracks():
    result = Track.query.all()
    return jsonify([item.serialize for item in result]), 200

########################### 
### SEARCH BY ID
###########################

@app.route('/artists/<artist_id>', methods=["GET", "DELETE"])
def singleArtist(artist_id):

    if request.method == "GET":
        result = Artist.query.get(artist_id)

        if not result:
            abort(404, message="No artist found!")
        return result.serialize, 200

    elif request.method == "DELETE":
        result = Artist.query.get(artist_id)

        if not result:
            abort(404, message="No artist found!")

        albums = Album.query.filter_by(artist_id=artist_id)

        for album in albums.all():
            Track.query.filter_by(album_id=album.id).delete()
        
        albums.delete()
        db.session.delete(result)

        db.session.commit()
        return result.serialize, 204


@app.route('/albums/<album_id>', methods=["GET", "DELETE"])
def singleAlbum(album_id):

    if request.method == "GET":
        result = Album.query.get(album_id)

        if not result:
            abort(404, message="Album not found!")
        return result.serialize, 200

    elif request.method == "DELETE":
        result = Album.query.get(album_id)

        if not result:
            abort(404, message="Album not found!")

        Track.query.filter_by(album_id=album_id).delete()
        db.session.delete(result)

        db.session.commit()
        return result.serialize, 204


@app.route('/tracks/<track_id>', methods=["GET", "DELETE"])
def singleTrack(track_id):

    if request.method == "GET":
        result = Track.query.get(track_id)

        if not result:
            abort(404, message="Track not found!")
        return result.serialize, 200

    elif request.method == "DELETE":
        result = Track.query.get(track_id)

        if not result:
            abort(404, message="Track not found!")

        db.session.delete(result)
        db.session.commit()
        return result.serialize, 204


########################### 
### ONE-TO-MANY
###########################

@app.route('/artists/<artist_id>/albums', methods=["GET", "POST"])
def artistAlbums(artist_id):

    if request.method == "GET":
        artist = Artist.query.get(artist_id)
        if not artist:
            abort(404, message="Artist not found!")
        
        #result = Album.query.filter_by(artist_id=artist_id).all()

        return jsonify([item.serialize for item in artist.albums]), 200


    elif request.method == "POST":
        
        if not (request.json.get("name") and\
                isinstance(request.json["name"], str) and\
                request.json.get("genre") and\
                isinstance(request.json["genre"], str)):

            abort(400)

        id = b64encode(request.json["name"].encode()).decode('utf-8')
        if len(id) > ID_LENGTH_LIMIT:
            id = id[:ID_LENGTH_LIMIT]

        result = Album.query.get(id)
        if result:
            return jsonify(result.serialize), 409
        
        artist = Artist.query.get(artist_id)
        if not artist:
            abort(422)
        
        album = Album(id=id,
                        name=request.json["name"],
                        genre=request.json["genre"],
                        artist_id=artist_id
                        )
                    
        db.session.add(album)
        db.session.commit()

        return jsonify(album.serialize), 201

@app.route('/artists/<artist_id>/tracks', methods=["GET"])
def artistTracks(artist_id):

    artist = Artist.query.get(artist_id)
    if not artist:
        abort(404, message="Artist not found!")
    
    result = []
    for album in artist.albums:
        result.extend(album.tracks)

    return jsonify([item.serialize for item in result]), 200



@app.route('/albums/<album_id>/tracks', methods=["GET", "POST"])
def albumTracks(album_id):
    
    if request.method == "GET":
        album = Album.query.get(album_id)
        
        if not album:
            abort(404, message="Album not found!")

        return jsonify([item.serialize for item in album.tracks]), 200


    elif request.method == "POST":

        if not (request.json.get("name") and\
                isinstance(request.json["name"], str) and\
                request.json.get("duration") and\
                (isinstance(request.json["duration"], float) or isinstance(request.json["duration"], int))):
            abort(400)


        id = b64encode(request.json["name"].encode()).decode('utf-8')
        if len(id) > ID_LENGTH_LIMIT:
            id = id[:ID_LENGTH_LIMIT]

        result = Track.query.get(id)
        if result:
            return jsonify(result.serialize), 409

        album = Album.query.get(album_id)
        if not album:
            abort(422)

        album = Track(id=id,
                        name=request.json["name"],
                        duration=request.json["duration"],
                        times_played=0,
                        album_id=album_id
                        )
                    
        db.session.add(album)
        db.session.commit()

        return jsonify(album.serialize), 201


########################### 
### PLAY
###########################

@app.route('/artists/<artist_id>/albums/play', methods=["PUT"])
def playArtist(artist_id):
    
    artist = Artist.query.get(artist_id)
    if not artist:
        abort(404)

    for album in artist.albums:
        for track in album.tracks:
            track.times_played+=1

    db.session.commit()
    return "", 200


@app.route('/albums/<album_id>/tracks/play', methods=["PUT"])
def playAlbum(album_id):
    album = Album.query.get(album_id)
    if not album:
        abort(404)

    for track in album.tracks:
        track.times_played+=1

    db.session.commit()
    return "", 200


@app.route('/tracks/<track_id>/play', methods=["PUT"])
def playTrack(track_id):
    track = Track.query.get(track_id)
    if not track:
        abort(404)

    track.times_played +=1

    db.session.commit()
    return "", 200



if __name__ == "__main__":
    app.run(debug=False)