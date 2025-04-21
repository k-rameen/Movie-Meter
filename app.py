from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import InputRequired, Length, NumberRange
import csv
import ast
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import random
from faker import Faker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    review = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None

# Forms
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8)])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8)])
    submit = SubmitField("Login")

class ReviewForm(FlaskForm):
    review_text = TextAreaField('Review', validators=[InputRequired(), Length(min=1, max=500)])
    rating = IntegerField('Rating (1-10)', validators=[InputRequired(), NumberRange(min=1, max=10)])
    submit = SubmitField('Submit')

# Load movie data
CSV_FILE = 'movies_metadata.csv'

def load_movies_from_csv():
    movies = []
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                movie = {
                    "id": int(row['id']),
                    "title": row['title'],
                    "belongs_to_collection": ast.literal_eval(row['belongs_to_collection']) if row['belongs_to_collection'] != 'False' else None,
                    "genres": ast.literal_eval(row['genres']),
                    "production_companies": ast.literal_eval(row['production_companies']),
                    "production_countries": ast.literal_eval(row['production_countries']),
                    "spoken_languages": ast.literal_eval(row['spoken_languages']),
                    "release_date": row['release_date'],
                    "overview": row['overview'],
                    "tagline": row['tagline'] if 'tagline' in row else '',
                    "vote_average": float(row['vote_average']) if row['vote_average'] else 0.0,
                    "runtime": float(row['runtime']) if row['runtime'] else 0.0,
                    "poster_path": row['poster_path'] if row['poster_path'] else None,
                    "budget": float(row['budget']) if row['budget'] else 0,
                    "revenue": float(row['revenue']) if row['revenue'] else 0,
                    "cast": ast.literal_eval(row['cast']) if 'cast' in row and row['cast'] else []
                }
                movies.append(movie)
            except (KeyError, ValueError, SyntaxError):
                continue
        generate_fake_reviews(movies)
    return movies

def generate_fake_reviews(movies, num_reviews_per_movie=3):
    fake = Faker()
    for movie in movies:
        movie_id = movie['id']
        existing_reviews_count = Review.query.filter_by(movie_id=movie_id).count()
        reviews_needed = max(0, num_reviews_per_movie - existing_reviews_count)
        
        if reviews_needed > 0:
            base_rating = min(10, max(1, round(movie['vote_average'])))
            
            for _ in range(reviews_needed):
                username = fake.user_name()
                rating = min(10, max(1, base_rating + random.randint(-2, 2)))
                
                if rating >= 8:
                    review_text = fake.sentence() + " " + random.choice([
                        "Absolutely loved it!",
                        "One of the best movies I've seen!",
                        "Would watch it again and again!"
                    ])
                elif rating >= 5:
                    review_text = fake.sentence() + " " + random.choice([
                        "Pretty good overall.",
                        "Enjoyable but not perfect.",
                        "Worth watching once."
                    ])
                else:
                    review_text = fake.sentence() + " " + random.choice([
                        "Could have been better.",
                        "Disappointing.",
                        "Not my cup of tea."
                    ])
                
                timestamp = fake.date_time_this_year()
                
                new_review = Review(
                    movie_id=movie_id,
                    user_id=0,  # Using 0 for fake users
                    username=username,
                    review=review_text,
                    rating=rating,
                    timestamp=timestamp
                )
                db.session.add(new_review)
            db.session.commit()

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('User already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('UI.html')

@app.route('/movies', methods=['GET'])
def get_movies():
    search_text = request.args.get('search', '').lower()
    filter_value = request.args.get('filter', '').lower()

    movies = load_movies_from_csv()
    
    if not search_text and not filter_value:
        return jsonify(movies[:100])  # Return first 100 for autocomplete
        
    filtered_movies = [
        movie for movie in movies
        if (search_text in movie['title'].lower() or 
            any(search_text in actor.lower() for actor in movie.get('cast', []))) and 
           (not filter_value or any(genre['name'].lower() == filter_value for genre in movie['genres']))
    ]
    return jsonify(filtered_movies if filtered_movies else [])

@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def movie_details(movie_id):
    movies = load_movies_from_csv()
    movie = next((m for m in movies if m['id'] == movie_id), None)

    if not movie:
        flash('Movie not found!', 'danger')
        return redirect(url_for('home'))

    generate_fake_reviews([movie], num_reviews_per_movie=3)

    form = ReviewForm()

    if form.validate_on_submit():
        existing_review = Review.query.filter_by(
            movie_id=movie_id, 
            user_id=current_user.id
        ).first()

        if existing_review:
            existing_review.review = form.review_text.data
            existing_review.rating = form.rating.data
            existing_review.timestamp = datetime.now()
        else:
            new_review = Review(
                movie_id=movie_id,
                user_id=current_user.id,
                username=current_user.username,
                review=form.review_text.data,
                rating=form.rating.data,
                timestamp=datetime.now()
            )
            db.session.add(new_review)
        
        db.session.commit()
        flash('Your review has been submitted!', 'success')
        return redirect(url_for('movie_details', movie_id=movie_id))

    movie_reviews = Review.query.filter_by(movie_id=movie_id).order_by(Review.timestamp.desc()).all()
    fav_ids = [fav.movie_id for fav in Favorite.query.filter_by(user_id=current_user.id).all()]

    return render_template(
        'movie_details.html',
        movie=movie,
        form=form,
        movie_reviews=movie_reviews,
        favourites=fav_ids
    )

@app.route('/stats')
@login_required
def stats():
    movies = load_movies_from_csv()
    trending = sorted(movies, key=lambda x: x['vote_average'], reverse=True)[:10]

    stats_data = []
    for movie in trending:
        reviews = Review.query.filter_by(movie_id=movie['id']).all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            stats_data.append({
                'title': movie['title'],
                'avg_rating': round(avg_rating, 2),
                'vote_average': movie['vote_average']
            })

    return render_template('stats.html', stats=stats_data)

@app.route('/add_favourite/<int:movie_id>', methods=['POST'])
@login_required
def add_favourite(movie_id):
    existing = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not existing:
        new_fav = Favorite(user_id=current_user.id, movie_id=movie_id)
        db.session.add(new_fav)
        db.session.commit()
    return '', 200

@app.route('/remove_favourite/<int:movie_id>', methods=['POST'])
@login_required
def remove_favourite(movie_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return '', 200

@app.route('/favourites')
@login_required
def favourites_page():
    movies = load_movies_from_csv()
    user_fav_ids = [fav.movie_id for fav in Favorite.query.filter_by(user_id=current_user.id).all()]
    favourite_movies = [movie for movie in movies if movie['id'] in user_fav_ids]
    return render_template('favourites.html', favourite_movies=favourite_movies)

@app.route('/trending')
@login_required
def trending_movies():
    movies = load_movies_from_csv()
    trending = sorted(movies, key=lambda x: x['vote_average'], reverse=True)[:50]
    return render_template('trending.html', trending_movies=trending)

@app.route('/faq')
@login_required
def faq():
    return render_template('faq.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)