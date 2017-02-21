from tempfile import TemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
from flask import render_template, request, flash, get_flashed_messages, make_response
from flask_classy import FlaskView
from wtforms.fields import BooleanField, StringField
import wtforms.validators
from flask_wtf import FlaskForm


class AlphanumericValidator(object):
    def __call__(self, form, field):
        if not field.data.isalpha():
            raise wtforms.validators.ValidationError("Field is not alphanumeric")


class JavaPackageValidator(object):
    def __call__(self, form, field):
        if not self._check_package_name(field.data):
            raise wtforms.validators.ValidationError("Field does not have a valid Java package name")

    @staticmethod
    def _check_package_name(package):
        tree = package.split('.')

        if len(tree) == 0:
            return False

        for node in tree:
            if not node.replace("_", "").isalpha():
                return False

        return True


class PluginHelperForm(FlaskForm):
    name = StringField("Plugin name", [wtforms.validators.data_required(),
                                       AlphanumericValidator()])
    package = StringField("Plugin package", [wtforms.validators.data_required(),
                                             JavaPackageValidator()])
    author = StringField("Plugin author", [wtforms.validators.data_required(),
                                           wtforms.validators.regexp("\w", message="Field has invalid characters")])
    version = StringField("Plugin version", [wtforms.validators.data_required(),
                                             wtforms.validators.regexp("\w", message="Field has invalid characters")])
    include_listener = BooleanField("Include a listener for me, please.", [wtforms.validators.optional()])


class PluginHelperView(FlaskView):
    route_prefix = '/bungeecord/'

    def index(self):
        return render_template("pluginhelper/main.html", form=PluginHelperForm())

    def post(self):
        # Check if we have everything we need
        form = PluginHelperForm()

        if not form.validate_on_submit():
            return render_template("pluginhelper/main.html", errors=True, form=form)

        # Looks good. Render everything we need.
        pom = render_template("pluginhelper/zipfile/pom_xml.html", package=form.package.data, name=form.name.data,
                              author=form.author.data, version=form.version.data)
        yml = render_template("pluginhelper/zipfile/plugin_yml.html", package=form.package.data, name=form.name.data,
                              author=form.author.data, version=form.version.data)
        main = render_template("pluginhelper/zipfile/main_java.html", package=form.package.data, name=form.name.data,
                               include_listener=form.include_listener.data)

        # Create the ZIP
        with TemporaryFile() as zfile:
            with ZipFile(zfile, "a", ZIP_DEFLATED) as zip:
                zip.writestr("pom.xml", pom)
                zip.writestr("src/main/resources/plugin.yml", yml)
                zip.writestr("src/main/java/" + form.package.data.replace(".", "/") + "/" + form.name.data + ".java",
                             main)
                if form.include_listener.data:
                    listener = render_template("pluginhelper/zipfile/listener_java.html", package=form.package.data,
                                               name=form.name.data, author=form.author.data, version=form.version.data)
                    zip.writestr(
                        "src/main/java/" + form.package.data.replace(".", "/") + "/" + form.name.data + "Listener.java",
                        listener)

            zfile.seek(0)

            return make_response((zfile.read(), 200, {"Content-Type": "application/zip",
                                                      "Content-Disposition": "attachment; filename=" + form.name.data + ".zip"}))