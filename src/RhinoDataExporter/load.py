from .plugin import RhinoDataExporterPlugin

plugin_instance = None

def plugin_start3(plugin_dir):
    global plugin_instance
    plugin_instance = RhinoDataExporterPlugin(plugin_dir)
    return plugin_instance.plugin_name

def plugin_stop():
    if plugin_instance:
        plugin_instance.stop()

def plugin_prefs(parent, cmdr, is_beta):
    return plugin_instance.build_prefs(parent)

def prefs_changed(cmdr, is_beta):
    plugin_instance.prefs_changed()

def journal_entry(cmdr, is_beta, system, station, entry, state_data):
    plugin_instance.journal_entry(cmdr, is_beta, system, station, entry, state_data)

def cmdr_data(data, is_beta):
    plugin_instance.cmdr_data(data, is_beta)

def dashboard_entry(cmdr, is_beta, entry):
    plugin_instance.dashboard_entry(cmdr, is_beta, entry)
