from flask import render_template, request, flash, get_flashed_messages, make_response
from flask_classy import FlaskView
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from markupsafe import Markup
from wtforms import TextAreaField, SelectField
import wtforms
from yaml import safe_load as load_yaml
from yaml import dump
from yaml import YAMLError
from collections import OrderedDict

var_mappings = {
  "{DARK_GRAY}": "&8",
  "{DARK_GREEN}": "&2",
  "{DARK_PURPLE}": "&5",
  "{DARK_RED}": "&4",
  "{GOLD}": "&6",
  "{GRAY}": "&7",
  "{GREEN}": "&a",
  "{LIGHT_PURPLE}": "&d",
  "{RED}": "&c",
  "{WHITE}": "&f",
  "{YELLOW}": "&e",
  "{BOLD}": "&l",
  "{ITALIC}": "&o",
  "{MAGIC}": "&k",
  "{RESET}": "&r",
  "{STRIKE}": "&m",
  "{STRIKETHROUGH}": "&m",
  "{UNDERLINE}": "&n",
  "{service}": "%service%",
  "{servicename}": "%service%",
  "{SERVICE}": "%service%",
  "{username}": "%player%",
  "{votes}": "%votes%",
  "{uuid}": "%uuid%"
}

def to_superbvote_msg(msg):
  nm = msg
  for k, v in var_mappings.items():
    nm = nm.replace(k, v)
  return nm

def convert_reward(gal):
  sb = {"broadcast-message": to_superbvote_msg(gal["broadcast"]), "player-message":
          to_superbvote_msg(gal["playermessage"])}
  sb["commands"] = map(to_superbvote_msg, gal["commands"])
  return sb

def sort_map_items(m):
  return sorted(m.items(), key=lambda k: k[0])

def sort_map_items_i(m):
  return sorted(m.items(), key=lambda k: int(k[0]))

# SuperbVote requires precise vote ordering.
# GAListener processes lucky, cumulative, permission, and then service based votes, in this order only.
def process_configuration(gal):
  sb_rewards = []
  if "luckyvotes" in gal:
    for k, v in sort_map_items_i(gal["luckyvotes"]):
      r = convert_reward(v)
      r["if"] = {"chance": int(k)}
      r["allow-cascading"] = True
      sb_rewards.append(r)
  if "cumulative" in gal:
    for k, v in sort_map_items_i(gal["cumulative"]):
      r = convert_reward(v)
      r["if"] = {"cumulative-votes": int(k)}
      r["allow-cascading"] = True
      sb_rewards.append(r)
  if "perms" in gal:
    for k, v in sort_map_items(gal["perms"]):
      r = convert_reward(v)
      r["if"] = {"permission": "gal." + k}
      sb_rewards.append(r)
  for k, v in sort_map_items(gal["services"]):
    r = convert_reward(v)
    if k == "default":
      r["if"] = {}
    else:
      r["if"] = {"service": k}
    sb_rewards.append(r)
  return {"rewards": sb_rewards}


class ConfigurationConverterForm(FlaskForm):
    yaml_file = FileField("Upload your GAListener configuration", [wtforms.validators.input_required()])


class GAListenerToSuperbVoteView(FlaskView):
    def index(self):
        return render_template("superbvote/convert.html", form=ConfigurationConverterForm())

    def post(self):
        form = ConfigurationConverterForm()

        if not form.validate_on_submit():
            return render_template("superbvote/convert.html", form=form)

        try:
            yaml = load_yaml(form.yaml_file.data)
        except YAMLError:
            flash(
                Markup('A syntax error was detected. You may want to use '
                       '<a href="http://yaml-online-parser.appspot.com/">this tool</a> '
                       'to determine the problem.'),
                "formerror")
            return render_template("superbvote/convert.html", form=form)

        if not isinstance(yaml, dict):
            flash("This YAML file does not represent a dictionary (mapping).", "formerror")
            return render_template("superbvote/convert.html", form=form)

        try:
            result = process_configuration(yaml)
        except Exception as e:
            flash("This YAML file does not look like a GAListener configuration.", "formerror")
            return render_template("superbvote/convert.html", form=form)

        return make_response((dump(result), 200, {"Content-Type": "application/yaml",
                                                  "Content-Disposition": "attachment; filename=superbvote_config.yml"}))
