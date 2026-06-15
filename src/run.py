"""Entry point for running the Alexa Shopping List Flask app."""

from flaskapp.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="oli-desktop", port=5000)
