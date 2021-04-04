# The original file doesn't import it and has no endpoints attached at all
from app import app, views  # pylint: disable=unused-import

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
