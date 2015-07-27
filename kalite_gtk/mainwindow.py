from __future__ import print_function
from __future__ import unicode_literals

from gi.repository import Gtk, Gdk, GLib, Pango
from pkg_resources import resource_filename  # @UnresolvedImport
import logging

from . import cli
from kalite_gtk import validators
from kalite_gtk.exceptions import ValidationError


logger = logging.getLogger(__name__)


def run_async(func):
    """
    http://code.activestate.com/recipes/576684-simple-threading-decorator/

        run_async(func)
            function decorator, intended to make "func" run in a separate
            thread (asynchronously).
            Returns the created Thread object

            E.g.:
            @run_async
            def task1():
                do_something

            @run_async
            def task2():
                do_something_too

    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        # Never return anything, idle_add will think it should re-run the
        # function because it's a non-False value.
        return None

    return async_func


class Handler:

    def __init__(self, mainwindow):
        # Store new settings here and use for sync / reset
        # This only includes valid settings
        self.unsaved_settings = {}
        self.mainwindow = mainwindow

    def on_delete_window(self, *args):
        Gtk.main_quit(*args)

    @run_async
    def on_start_button_clicked(self, button):
        self.log_message("Starting KA Lite...\n")
        GLib.idle_add(button.set_sensitive, False)
        for stdout, stderr, returncode in cli.start():
            if stdout:
                self.log_message(stdout)
        if returncode == 0:
            self.log_message("KA Lite started!\n")
        elif stderr:
            self.log_message(stderr)
        GLib.idle_add(button.set_sensitive, True)
        GLib.idle_add(self.mainwindow.update_status)

    @run_async
    def on_stop_button_clicked(self, button):
        GLib.idle_add(button.set_sensitive, False)
        self.log_message("Stopping KA Lite...\n")
        for stdout, stderr, returncode in cli.stop():
            if stdout:
                self.log_message(stdout)
        if returncode:
            self.log_message("Failed to stop\n")
        if stderr:
            self.log_message(stderr)
        GLib.idle_add(button.set_sensitive, True)
        GLib.idle_add(self.mainwindow.update_status)

    @run_async
    def on_diagnose_button_clicked(self, button):
        GLib.idle_add(button.set_sensitive, False)
        start_iter = self.mainwindow.diagnostics.get_start_iter()
        end_iter = self.mainwindow.diagnostics.get_end_iter()
        GLib.idle_add(lambda: self.mainwindow.diagnostics.delete(start_iter, end_iter))
        stdout, stderr, returncode = cli.diagnose()
        if stdout:
            GLib.idle_add(self.mainwindow.diagnostics_message, stdout)
        if stderr:
            GLib.idle_add(self.mainwindow.diagnostics_message, stderr)
        if returncode:
            GLib.idle_add(self.mainwindow.set_status, "Failed to diagnose!")
        GLib.idle_add(button.set_sensitive, True)

    @run_async
    def on_startup_service_button_clicked(self, button):
        GLib.idle_add(button.set_sensitive, False)
        if cli.is_installed():
            self.log_message("Removing startup service\n")
            stdout, stderr, returncode = cli.remove()
            if stdout:
                self.log_message(stdout)
            if stderr:
                self.log_message(stderr)
            if returncode:
                self.log_message("Failed to remove startup service\n")
            self.log_message("Removed!\n")
        else:
            self.log_message("Installing startup service\n")
            stdout, stderr, returncode = cli.install()
            if stdout:
                self.log_message(stdout)
            if stderr:
                self.log_message(stderr)
            if returncode:
                self.log_message("Failed to install startup service\n")
            self.log_message("Installed!\n")
        GLib.idle_add(self.mainwindow.set_from_settngs)
        GLib.idle_add(button.set_sensitive, True)

    def on_username_entry_changed(self, entry):
        value = entry.get_text()
        if not value:
            self.mainwindow.default_user_radio_button.set_active(True)
            return
        self.mainwindow.username_radiobutton.set_active(True)
        try:
            value = validators.username(value)
            self.unsaved_settings['user'] = value
            self.settings_changed()
        except ValidationError:
            self.mainwindow.settings_feedback_label.set_label(
                'Username invalid'
            )

    @run_async
    def on_save_and_restart_button_clicked(self, button):
        cli.save_settings()
        GLib.idle_add(button.set_sensitive, False)
        GLib.idle_add(
            self.mainwindow.settings_feedback_label.set_label,
            'Settings saved, restarting server...'
        )
        self.log_message("Restarting KA Lite...\n")
        GLib.idle_add(self.mainwindow.start_button.set_sensitive, False)
        for stdout, stderr, returncode in cli.start():
            if stdout:
                self.log_message(stdout)
        if returncode == 0:
            self.log_message("KA Lite restarted!\n")
        elif stderr:
            self.log_message(stderr)
        GLib.idle_add(button.set_sensitive, False)

    def settings_changed(self):
        """
        We should make individual handlers for widgets, but this is easier...
        """
        cli.settings.update(self.unsaved_settings)
        cli.save_settings()
        self.mainwindow.settings_feedback_label.set_label(
            'Settings OK - they will be saved and take effect when you restart the server!'
        )

    def log_message(self, msg):
        """Logs a message using idle callback"""
        GLib.idle_add(self.mainwindow.log_message, msg)


class MainWindow:

    def __init__(self):

        self.builder = Gtk.Builder()
        glade_file = resource_filename(__name__, "glade/mainwindow.glade")
        self.builder.add_from_file(glade_file)

        # Save glade builder XML tree objects to object properties all in
        # one place so we don't get confused. Don't call get_object other places
        # PLEASE.
        self.window = self.builder.get_object('mainwindow')
        self.log_textview = self.builder.get_object('log_textview')
        self.diagnose_textview = self.builder.get_object('diagnose_textview')
        self.diagnostics = self.builder.get_object('diagnostics')
        self.status_entry = self.builder.get_object('status_label')
        self.default_user_radio_button = self.builder.get_object('radiobutton_user_default')
        self.kalite_command_entry = self.builder.get_object('kalite_command_entry')
        self.port_spinbutton = self.builder.get_object('port_spinbutton')
        self.content_root_filechooserbutton = self.builder.get_object('content_root_filechooserbutton')
        self.username_entry = self.builder.get_object('username_entry')
        self.username_radiobutton = self.builder.get_object('radiobutton_username')
        self.log = self.builder.get_object('log')
        self.start_button = self.builder.get_object('start_button')
        self.stop_button = self.builder.get_object('stop_button')
        self.diagnose_button = self.builder.get_object('diagnose_button')
        self.startup_service_button = self.builder.get_object('startup_service_button')
        self.settings_feedback_label = self.builder.get_object('settings_feedback_label')
        self.start_stop_instructions_label = self.builder.get_object('start_stop_instructions_label')
        self.save_and_restart_button = self.builder.get_object('save_and_restart_button')

        # Save old label so we can continue to replace text
        self.start_stop_instructions_label_original_text = self.start_stop_instructions_label.get_label()

        # Auto-connect handlers defined in mainwindow.glade
        self.builder.connect_signals(Handler(self))

        # Style the log like a terminal
        self.log_textview.override_font(
            Pango.font_description_from_string('DejaVu Sans Mono 9')
        )
        self.log_textview.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        self.log_textview.override_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))
        self.log_textview.override_background_color(
            Gtk.StateFlags.SELECTED, Gdk.RGBA(0.7, 1, 0.5, 1))

        # Style the diagnose view like a terminal
        self.diagnose_textview.override_font(
            Pango.font_description_from_string('DejaVu Sans Mono 9')
        )
        self.diagnose_textview.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        self.diagnose_textview.override_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))
        self.diagnose_textview.override_background_color(
            Gtk.StateFlags.SELECTED, Gdk.RGBA(0.7, 1, 0.5, 1))

        # Load settings into widgets
        self.set_from_settings()

        # Show widgets
        self.window.show_all()

        # Update status bar
        GLib.idle_add(self.update_status)
        GLib.timeout_add(60 * 1000, lambda: self.update_status or True)

    def diagnostics_message(self, msg):
        self.diagnostics.insert_at_cursor(msg)

    def log_message(self, msg):
        self.log.insert_at_cursor(msg)

    def set_from_settings(self):
        # Insert username of currently running user
        label = self.start_stop_instructions_label_original_text.replace(
            '{username}', cli.settings['user']
        )
        self.start_stop_instructions_label.set_label(label)

        label = self.default_user_radio_button.get_label()
        label = label.replace('{default}', cli.DEFAULT_USER)
        self.default_user_radio_button.set_label(label)
        self.kalite_command_entry.set_text(cli.settings['command'])
        self.port_spinbutton.set_value(int(cli.settings['port']))

        self.content_root_filechooserbutton.set_filename(cli.settings['content_root'])

        if cli.DEFAULT_USER != cli.settings['user']:
            self.username_entry.set_text(cli.settings['user'])
            self.username_radiobutton.set_active(True)
            self.default_user_radio_button.set_active(False)
        else:
            self.username_radiobutton.set_active(False)
            self.default_user_radio_button.set_active(True)

        self.startup_service_button.set_sensitive(cli.has_init_d())
        if cli.has_init_d():
            if cli.is_installed():
                self.startup_service_button.set_label("Remove system service")
            else:
                self.startup_service_button.set_label("Install system service")

    @run_async
    def update_status(self):
        GLib.idle_add(self.set_status, "Updating status...")
        GLib.idle_add(self.set_status, "Server status: " + (cli.status() or "Error fetching status").split("\n")[0])

    def set_status(self, status):
        self.status_entry.set_label(status)


if __name__ == "__main__":
    win = MainWindow()
    Gtk.main()
