from flask import Flask, render_template
import os

app = Flask(__name__)

try:
    with file(".secret_key", "r") as secret_key:
        app.secret_key = secret_key.read()
except IOError:
    from hashlib import sha1

    key = sha1(os.urandom(32)).hexdigest()
    try:
        with file(".secret_key", "a") as secret_key:
            secret_key.write(key)
    except IOError:
        pass
    app.secret_key = key

from bungeecord import PluginHelperView
from yamlchecker import YamlCheckerView

PluginHelperView.register(app)
YamlCheckerView.register(app)


@app.route("/")
def main():
    return render_template("index.html")


if __name__ == "__main__":
    do_debug = "DEBUG" in os.environ
    app.run(debug=do_debug)
