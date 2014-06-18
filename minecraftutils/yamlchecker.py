from flask import render_template, request, flash, get_flashed_messages
from flask.ext.classy import FlaskView
from flask_wtf import Form
from flask_wtf.file import FileField
from markupsafe import Markup
from wtforms import TextAreaField, SelectField
import wtforms
from yaml import safe_load as load_yaml
from yaml import YAMLError


class ConfigChecker(object):
    def check_config(self, config):
        pass

    def _is_defined(self, config, sect):
        return sect in config and config[sect] is not None and config[sect] is not ""


class BungeeCordConfigChecker(ConfigChecker):
    def check_config(self, config):
        # Start poking around the structure...

        # servers
        servers_defined = self._is_section_defined(config, "servers")
        if not servers_defined or len(config['servers']) == 0:
            yield {"message": "No servers are defined!", "class": "urgent"}
        else:
            # Servers just need addresses.
            server_addresses_declared = {}
            for server in config['servers']:
                if not self._is_defined(config['servers'][server], "address"):
                    yield {"message": "Server " + server + " does not have an address!", "class": "urgent"}
                elif config['servers'][server]['address'] in server_addresses_declared:
                    yield {"message": "Server " + server + " has a duplicate IP address (" +
                                      config['servers'][server]['address'] + "), used by server " +
                                      server_addresses_declared[config['servers'][server]['address']] + ".",
                           "class": "warning"}
                else:
                    server_addresses_declared[config['servers'][server]['address']] = server

        # Check for permissions section existence.
        # We will validate permissions afterwards.
        permissions_defined = self._is_section_defined(config, "permissions")
        if not permissions_defined:
            yield {"message": "No groups are defined!", "class": "urgent"}

        # groups
        groups_defined = self._is_section_defined(config, "groups")
        if not groups_defined or len(config['groups']) == 0:
            yield {"message": "No users are in groups.", "class": "warning"}
        else:
            for user in config['groups']:
                for group in config['groups'][user]:
                    if permissions_defined and group not in config['permissions']:
                        yield {"message": user + " is assigned the group " + group + ", which does not exist.",
                               "class": "warning"}

        # permissions
        if permissions_defined:
            for group in config['permissions']:
                if config['permissions'][group] is None or len(config['permissions'][group]) == 0:
                    yield {"message": "The group " + group + " does not have any permissions defined.",
                           "class": "warning"}

        # listeners
        if not self._is_section_defined(config, "listeners") or len(config['listeners']) == 0:
            yield {"message": "You have no listeners defined, or they are not formatted properly.", "class": "urgent"}
        else:
            if not isinstance(config['listeners'], list):
                yield {"message": "Your listeners are not formatted properly. Listeners are formatted as a list.",
                       "class": "urgent"}
            else:
                number = 0
                for listener in config['listeners']:
                    number += 1
                    if not self._is_defined(listener, "host"):
                        yield {"message": "Listener #" + str(number) + " does not have a host associated!",
                               "class": "urgent"}
                        continue

                    if ':' in listener['host']:
                        hostname = listener['host'].split(':')[0]
                    else:
                        hostname = listener['host']

                    if hostname == '127.0.0.1' or hostname == 'localhost':
                        yield {"message": "Listener " + listener['host'] + " is running on localhost.",
                               "class": "warning"}

                    if servers_defined and self._is_defined(listener, 'fallback_server') and \
                                    listener['fallback_server'] not in config['servers']:
                        yield {"message": "Listener " + listener['host'] + " has the fallback server " +
                                          listener['fallback_server'] + ", which does not exist.", "class": "warning"}
                    if servers_defined and self._is_defined(listener, 'default_server') and \
                                    listener['default_server'] not in config['servers']:
                        yield {"message": "Listener " + listener['host'] + " has the default server " +
                                          listener['default_server'] + ", which does not exist!", "class": "urgent"}
                    if servers_defined and self._is_defined(listener, 'forced_hosts'):
                        for host, server in listener['forced_hosts'].items():
                            if server not in config['servers']:
                                yield {
                                    "message": "Forced host " + host + " refers to the non-existent server " + server +
                                               ".",
                                    "class": "warning"}

    def _is_section_defined(self, config, sect):
        return sect in config and config[sect] is not None and len(config[sect]) > 0


class RedisBungeeConfigChecker(ConfigChecker):
    def check_config(self, config):
        # This is a very simple handler.
        for required in ['redis-server', 'server-id']:
            if not self._is_defined(config, required):
                yield {"message": required + " is missing from your configuration!", "class": "urgent"}
            elif (required == "server-id" or required == "redis-server") and config[required] == "":
                yield {"message": required + " is empty!", "class": "urgent"}


class YamlCheckerForm(Form):
    yaml_file = FileField("Upload your configuration", [wtforms.validators.input_required()])
    type = SelectField("Configuration type", [wtforms.validators.required()],
                       choices=[("bungeecord", "BungeeCord"), ("redisbungee", "RedisBungee")])


class YamlCheckerView(FlaskView):
    def index(self):
        return render_template("yamlchecker/main.html", form=YamlCheckerForm())

    def post(self):
        form = YamlCheckerForm()

        if not form.validate_on_submit():
            return render_template("yamlchecker/main.html", form=form)

        if form.type.data == "bungeecord":
            checker = BungeeCordConfigChecker()
        elif form.type.data == "redisbungee":
            checker = RedisBungeeConfigChecker()
        else:
            form.type.errors.append("This is an invalid configuration type.")
            return render_template("yamlchecker/main.html", form=form)

        try:
            yaml = load_yaml(form.yaml_file.data)
        except YAMLError:
            flash(
                Markup('A syntax error was detected. You may want to use '
                '<a href="http://yaml-online-parser.appspot.com/">this tool</a> '
                'to determine the problem.'),
                "formerror")
            return render_template("yamlchecker/main.html", form=form)

        if not isinstance(yaml, dict):
            flash("This YAML file does not represent a dictionary (mapping).", "formerror")
            return render_template("yamlchecker/main.html", form=form)

        for message in checker.check_config(yaml):
            flash(message['message'], message['class'])

        return render_template("yamlchecker/main.html", validated=len(get_flashed_messages()) == 0,
                               form=form)
