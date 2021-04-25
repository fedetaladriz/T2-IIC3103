from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# db.drop_all()


class Artist(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    albums = db.relationship('Album', backref='artist', lazy=True)

    @property
    def serialize(self):
        
        url = f"{request.url_root}artists/{self.id}"

        return {
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
    return request.base_url

###########################
### COMPLETE TABLE
###########################

@app.route('/artists', methods=["GET", "POST"])
def multipleArtists():

    if request.method == "GET":

        result = Artist.query.all()
        if not result:
            abort(404, message="No artists found!")
        return jsonify([item.serialize for item in result])

    elif request.method == "POST":

        artist = Artist(id=b64encode(request.form["name"].encode()).decode('utf-8'),
                        name=request.form["name"],
                        age=request.form["age"]
                        )
                    
        db.session.add(artist)
        db.session.commit()

        return jsonify(artist.serialize), 201


@app.route("/albums", methods=["GET"])
def multipleAlbums():

    result = Album.query.all()
    if not result:
        print("-"*20)
        abort(404, message="No albums found!")
    
    return jsonify([item.serialize for item in result])
    

@app.route("/tracks", methods=["GET"])
def multipleTracks():

    result = Track.query.all()
    if not result:
        print("-"*20)
        abort(404, message="No tracks found!")
    
    return jsonify([item.serialize for item in result])

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
        result = Album.query.filter_by(artist_id=artist_id).all()
        print("-frr"*20)
        print(result)
        print(bool(result))
        if not result:
            abort(404, message="No albums found!")
        return jsonify([item.serialize for item in result])


    elif request.method == "POST":
        album = Album(id=b64encode(request.form["name"].encode()).decode('utf-8'),
                        name=request.form["name"],
                        genre=request.form["genre"],
                        artist_id=artist_id
                        )
                    
        db.session.add(album)
        db.session.commit()

        return jsonify(album.serialize), 201

@app.route('/artists/<artist_id>/tracks', methods=["GET"])
def artistTracks(artist_id):

    albums = Album.query.filter_by(artist_id=artist_id).all()
    
    result = []
    for album in albums:
        result.extend(Track.query.filter_by(album_id=album.id).all())

    if not result:
        abort(404, message="No tracks found!")

    return jsonify([item.serialize for item in result])



@app.route('/albums/<album_id>/tracks', methods=["GET", "POST"])
def albumTracks(album_id):

    if request.method == "GET":
        result = Track.query.filter_by(album_id=album_id).all()
        print("-frr"*20)
        print(result)
        print(bool(result))
        if not result:
            abort(404, message="No albums found!")
        return jsonify([item.serialize for item in result])


    elif request.method == "POST":
        album = Track(id=b64encode(request.form["name"].encode()).decode('utf-8'),
                        name=request.form["name"],
                        duration=request.form["duration"],
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
    for album in artist.albums:
        for track in album.tracks:
            track.times_played+=1

    db.session.commit()
    return "", 200


@app.route('/albums/<album_id>/tracks/play', methods=["PUT"])
def playAlbum(album_id):
    album = Album.query.get(album_id)
    for track in album.tracks:
        track.times_played+=1

    db.session.commit()
    return "", 200


@app.route('/tracks/<track_id>/play', methods=["PUT"])
def playTrack(track_id):
    track = Track.query.get(track_id)
    track.times_played +=1

    db.session.commit()
    return "", 200



if __name__ == "__main__":
    app.run(debug=False)