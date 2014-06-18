# minecraft-utils

The source code to [tools.imaginarycode.com](http://tools.imaginarycode.com).

## Requirements

* [Flask](http://flask.pocoo.org)
* [Flask-Classy](http://pythonhosted.org/Flask-Classy/)
* [Flask-WTF](http://pythonhosted.org/Flask-WTF/)
* [PyYAML](http://www.pyyaml.org)
* [redis-py](https://github.com/andymccurdy/redis-py) (eventually)

A suitable `requirements.txt` is included as `minecraftutils/requirements.txt`.

## What's inside

* **bungeecord.py**: BungeeCord tools (currently only the Plugin Helper)
* **yamlchecker.py**: Configuration Checker

More tools are planned to be written - please send a pull request if you'd like to contribute one!

## Running

For development, use `DEBUG=1 python minecraftutils.py` in the `minecraftutils` directory.