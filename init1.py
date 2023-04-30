#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors

#for uploading photo:
from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='FlaskDemo',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


#Define a route to hello function
# @app.route('/')
# def hello():
#     return render_template('index.html')

@app.route("/")
def index():
 
  query = request.args.get("q")

  songs = search_songs(query)

  return render_template("index.html")

@app.route("/browse")
def browse():
 

  genre = request.args.get("genre")
  rating_threshold = request.args.get("rating_threshold")
  artist = request.args.get("artist")
  songs = browse_songs(genre, rating_threshold, artist)
  return render_template("browse.html", songs=songs)


def search_songs(query):


  cursor = conn.cursor()

  cursor.execute('SELECT title, artist, album FROM song WHERE title LIKE "%{}%"'.format(query))

  results = cursor.fetchall()

  cursor.close()

  return results


def browse_songs(genre, rating_threshold, artist):

  cursor = conn.cursor()

  if genre is not None:
    query = 'SELECT title, artist, album FROM song WHERE genre = %s AND rating >= %s'
    cursor.execute(query, (genre, rating_threshold))
  if rating_threshold is not None:
    query = 'SELECT title, artist, album FROM song WHERE rating >= %s'
    cursor.execute(query, (rating_threshold,))
  if artist is not None:
    query = 'SELECT title, artist, album FROM song WHERE artist = %s'
    cursor.execute(query, (artist,))
  else:
    query = 'SELECT title, artist, album FROM song'
    cursor.execute(query)

  results = cursor.fetchall()

  cursor.close()

  return results

@app.route('/rateSong', methods=['POST'])
def rateSong():
    username = session['username']
    cursor = conn.cursor()
    songID_input = request.form['Song']
    rating_input = request.form['rateSong']
    query = 'INSERT INTO rateSong (username, songID, stars) VALUES(%s, %s, %s)'
    cursor.execute(query, (username, songID_input, int(rating_input)))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/reviewFriend', methods=['GET','POST'])
def reviewFriendFollower():
    username_input = session['username']
    cursor = conn.cursor()

    query = 'SELECT reviewText FROM reviewSong, friend WHERE reviewSong.username <> %s AND (friend.user1 = %s OR friend.user2 = %s) AND friend.acceptStatus = "Accepted"'
    cursor.execute(query, (username_input,username_input,username_input))
    data = cursor.fetchall()

    conn.commit()
    cursor.close()
    return render_template('reviewFriend.html', posts=data)

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)
    
@app.route("/new")
def new():
 
  username =  session['username']
#   reviewDate = 

  # Get the user's friends and followers.
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM friends WHERE username = %s', (username,))
  friends = cursor.fetchall()
  cursor.execute('SELECT * FROM followers WHERE username = %s', (username,))
  followers = cursor.fetchall()

  # Get the list of new reviews.
  cursor.execute('SELECT * FROM reviews')
  new_reviews = cursor.fetchall()

  # Get the list of new songs by artists the user is a fan of.
  cursor.execute ('SELECT * FROM song WHERE artist_id IN (SELECT id FROM artists WHERE id IN (SELECT favorite_artist_id FROM users')
  new_songs = cursor.fetchall()

  # Close the cursor.
  cursor.close()

  # Render the new items of interest page.
  return render_template("new.html", friends=friends, followers=followers, new_reviews=new_reviews, new_songs=new_songs)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO user VALUES(%s, %s)'
        cursor.execute(ins, (username, password))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
	if request.method == 'POST':
        # check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			flash('File successfully uploaded')
			return redirect('/')
		else:
			flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
			return redirect(request.url)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
