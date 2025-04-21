![Movie Meter Banner](movieMeterBanner.png)

# Rapid Prototyping Project – Movie Review Platform

---

## Features

### Home Page
- Secure login/register to access features  
- Browse trending movies (Top 50 by vote average)  
- Search movies by **title**  
- Filter by **genre**  

### General Movie Details
- Poster  
- Movie Overview  
- General Information such as: genres, cast, production info, and release date  
- User reviews and ratings (1–10)  
- See all community reviews with timestamps  

### Favourites
- Users can add/remove movies from their personal favourites page  

### Statistics
- View Top 10 trending movies by vote average  
- Compare with user-generated average ratings  
- Trending section with highest-rated films  

### User Security
- Secure registration with hashed passwords  
- Login/logout flows  
- Session protection using **Flask-Login**  

### FAQ
- There is a page dedicated to users' frequently asked questions, allowing users to easily manage our website

---
## Basic Setup Instructions

### Prerequisites
- pip  
- Python 3.7+  
- Flask  
- Virtual Environment (venv)  
- Git  

Install Flask and required extensions:
`pip install flask flask-login flask-bcrypt flask-wtf
python -m pip install Flask-SQLAlchemy`

To view and manage your SQLite database: [Download DB Browser for SQLite](https://sqlitebrowser.org/dl/)


## Running Instructions
Clone the git repository by running this command in your terminal: 
<br>
`git clone https://github.com/Selena8877/Rapid-Prototyping-Project.git`

`cd Rapid-Prototyping-Project`
<br>
<br>
If you dont have flask installed, download it by running the follow command: 
<br>
`- pip install flask flask-login flask-bcrypt flask-wtf`
<br>
<br>
Run the flask server: 
<br>
`python app.py`
<br>
<br>
Open `http://127.0.0.1:5000/` in your browser


## Technologies Used
- Flask – Web Framework
- Flask-Login – User authentication
- Flask-Bcrypt – Secure password hashing
- Flask-WTF – Form management and validation
- Flask-SQLAlchemy – ORM for SQLite
- HTML/CSS – Frontend templates (Jinja2)
- CSV – Movie data loading

