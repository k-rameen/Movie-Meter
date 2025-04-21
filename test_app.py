import unittest
import os
import sys
from app import app, db, User, load_movies_from_csv
from flask_bcrypt import generate_password_hash

class FlaskAppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nSetting up test environment...")
        # Configure test app
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['CSV_FILE'] = 'movies_metadata.csv'

        # Ensure the actual CSV file exists
        if not os.path.exists(app.config['CSV_FILE']):
            raise FileNotFoundError(f"{app.config['CSV_FILE']} not found. Please make sure it's in the project directory.")

        with app.app_context():
            db.create_all()
            print("Loading movies from CSV...")
            load_movies_from_csv()
            print("Test environment ready.")

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            # Clear users table but keep movies
            db.session.rollback()
            User.query.delete()
            db.session.commit()

            # Create test user
            hashed_password = generate_password_hash("testpassword").decode('utf-8')
            user = User(username="testuser", password=hashed_password)
            db.session.add(user)
            db.session.commit()
        print("\nStarting new test...")

    def tearDown(self):
        with app.app_context():
            db.session.rollback()
        print("Test completed.")

    def login(self):
        return self.app.post('/login', 
                           data={'username': 'testuser', 'password': 'testpassword'},
                           follow_redirects=True)

    def test_load_movies_from_csv(self):
        """TEST 1: Verify movie data loading"""
        print("Running test_load_movies_from_csv...")
        csv_path = app.config['CSV_FILE']
        self.assertTrue(os.path.exists(csv_path), f"CSV file {csv_path} not found.")

        with app.app_context():
            movies = load_movies_from_csv()
            self.assertIsInstance(movies, list)
            self.assertGreater(len(movies), 0, "No movies were loaded from the CSV file.")
            required_fields = ['id', 'title', 'genres']
            for field in required_fields:
                self.assertIn(field, movies[0])
        print("✓ Movie data loaded successfully")

    def test_home_route(self):
        """TEST 2: Home route redirect"""
        print("Running test_home_route...")
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
        print("✓ Home route behaves correctly")

    def test_register_login_logout(self):
        """TEST 3: User registration flow"""
        print("Running test_register_login_logout...")
        # Test registration
        response = self.app.post('/register',
                               data={'username': 'newuser', 'password': 'newpassword'},
                               follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test login
        response = self.app.post('/login',
                               data={'username': 'newuser', 'password': 'newpassword'},
                               follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
        print("✓ Registration flow works")

    def test_invalid_login(self):
        """TEST 4: Invalid login attempt"""
        print("Running test_invalid_login...")
        response = self.app.post('/login',
                               data={'username': 'wronguser', 'password': 'wrongpass'},
                               follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'invalid', response.data.lower())
        print("✓ Invalid login handled properly")

    def test_get_movies(self):
        """TEST 5: Movie search"""
        print("Running test_get_movies...")
        self.login()
        response = self.app.get('/movies')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        print("✓ Movie search works")

    def test_movie_details(self):
        """TEST 6: Movie details"""
        print("Running test_movie_details...")
        self.login()
        with app.app_context():
            movies = load_movies_from_csv()
            valid_id = movies[0]['id']
        
        # Test valid movie
        response = self.app.get(f'/movie/{valid_id}')
        self.assertEqual(response.status_code, 200)
        
        # Test invalid movie
        response = self.app.get('/movie/999999', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        print("✓ Movie details work")

    def test_protected_routes(self):
        """TEST 7: Protected routes"""
        print("Running test_protected_routes...")
        # Test FAQ without login
        response = self.app.get('/faq', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

        # Test FAQ with login
        self.login()
        response = self.app.get('/faq', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        print("✓ Route protection works")

if __name__ == '_main_':
    # Set verbosity level (2 = verbose)
    unittest.main(argv=['first-arg-is-ignored'], verbosity=2, exit=True)
    print("\nStarting test suite...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(FlaskAppTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\nTest Summary:")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    # Exit with proper status code
    sys.exit(not result.wasSuccessful())