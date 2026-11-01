"""Wire the plugin class into EDMC"""
from .plugin import RhinoDataExporterPlugin

# Maintain single instance to the plugin class
plugin_instance = None

def plugin_start3(plugin_dir):
    """Start the EDMC plugin"""
    global plugin_instance
    plugin_instance = RhinoDataExporterPlugin(plugin_dir)
    return plugin_instance.plugin_name

def plugin_stop():
    """Stop the EDMC plugin"""
    if plugin_instance:
        plugin_instance.stop()

def plugin_prefs(parent, cmdr, is_beta):
    """Build the preferences"""
    return plugin_instance.build_prefs(parent)

def prefs_changed(cmdr, is_beta):
    """Indicate if the preferences were changed"""
    plugin_instance.prefs_changed()

def journal_entry(cmdr, is_beta, system, station, entry, state_data):
    """Populate the journal entry"""
    plugin_instance.journal_entry(cmdr, is_beta, system, station, entry, state_data)

def cmdr_data(data, is_beta):
    """Set the cmdr data"""
    plugin_instance.cmdr_data(data, is_beta)

def dashboard_entry(cmdr, is_beta, entry):
    """Populate the dashboard entry"""
    plugin_instance.dashboard_entry(cmdr, is_beta, entry)