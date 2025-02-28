import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)
dual_handlers = [stdout_handler, stderr_handler]
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(asctime)s: %(message)s', handlers=dual_handlers)

counter = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global counter
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    counter += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Health check
@app.route('/healthz')
def status():
    response = app.response_class(
        response=json.dumps({"result":"OK - healthy"}),
        status=200,
        mimetype='application/json'
        )
    app.logger.info('Status request successfull')
    return response

#Metrics function
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts =  connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
        response=json.dumps({"status":"success", "code":0,"data":{"db_connection_count": counter, "posts": len(posts)}}),
        status=200,
        mimetype='application/json')
    app.logger.info('Metrics request successfull')
    return response

#Gracefully shutdown the app without using CTRL+C
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug server')
    func()

# gracefully shutdown the app
@app.route('/shutdown', methods=['GET'])
def shutdown_server():
    shutdown()
    return 'Server shutting down'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')

