from src.web.app import create_app

# Instantiate the Flask web application
app = create_app(db_path='data/academyops.db')

if __name__ == '__main__':
    print("🚀 AcademyOps REST API Booting Local Service...")
    print("👉 Exercisable Target URL: http://127.0.0.1:5000/api/v1")
    app.run(host='127.0.0.1', port=5000, debug=True)