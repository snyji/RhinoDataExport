import os
import tkinter as tk
import myNotebook as nb
from tkinter import filedialog
from datetime import datetime

class RhinoDataExporterPlugin:
    """EDMC Plugin for exporting bookmarks from RhinoSpotter"""

    plugin_name = "RhinoDataExporter"
    plugin_version = "1.0"

    def __init__(self, plugin_dir):
        """Register the plugin directory and RhinoSpotter database path

        Args:
            plugin_dir (string): plugin directory path
            output_dir (string): output directory path
        """
        self.plugin_dir = plugin_dir
        self.paths = {
            "db_path": "",
            "output_dir": ""
        }

    # -----------------------------------------------------------------------
    # Utility helpers
    # -----------------------------------------------------------------------

    def autodetect_db(self):
        """Attempt to locate the RhinoSpotter database, defaults to
        the default Windows location."""
        default = os.path.expanduser(r"~\AppData\Local\RhinoSpotter\db\rhinospotter.db")

        return default if os.path.isfile(default) else ""

    def ensure_export_dir(self):
        """Ensure the exports directory exists"""
        export_dir = os.path.join(self.plugin_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)

        return export_dir

    # -----------------------------------------------------------------------
    # Export logic
    # -----------------------------------------------------------------------

    def export_bookmarks(self):
        """Dump the database to a csv file."""
        # Get the paths
        db_path = self.paths["db_path"]
        out_dir = self.paths["output_dir"]

        # Validate paths
        if not os.path.isfile(db_path):
            print(f"[{self.plugin_name}] DB not found: {db_path}")
            return None
        if not os.path.isdir(out_dir):
            print(f"[{self.plugin_name}] Output directory missing: {out_dir}")
            return None

        # Prepare output file
        today = datetime.now().strftime("%Y-%m-%d")
        out_file = os.path.join(out_dir, f"RhinoExport_{today}.csv")

        # RhinoSpotter csv header columns
        headers = [
            "System", "Body", "Location", "Coords",
            "Rigs", "Material", "A/D", "Cmdr", "ImportData"
        ]

        # Field types allowed in the RhinoSpotter bookmark data used to
        #   create the import.
        allowed_fields = {
            "system": (str,),
            "system_address": (int,),
            "planet_name": (str,),
            "body_id": (int,),
            "planet_radius": (int, float),
            "latitude": (int, float),
            "longitude": (int, float),
            "heading": (int, float),
            "location_index": (int,),
            "commodity": (str,),
            "rigs": (int,),
            "amount": (str,),
            "density": (str,),
            "commander": (str,),
        }

        prefix = "RhinoData:"

        # Attempt to gracefully handle imports
        try:
            import csv
            import sqlite3
            import json
            import zlib
            import base64

            # Setup database connection
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Build the query
            stmt = """
                SELECT *
                FROM bookmarks
                ORDER BY system, body_id, location_index
            """

            # Get all rows
            rows = conn.execute(stmt)

            # Write the CSV file
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                # Loop through each row, write each row to the csv
                for row in rows:
                    # Read the stored json data
                    loc_data = json.loads(row["data"])

                    # Extract only allowed fields
                    extracted = {
                        key: loc_data[key]
                        for key in allowed_fields
                        if key in loc_data and loc_data[key] is not None
                    }

                    # From https://github.com/Fumlop/EDRhinoSpotter/blob/main/rs_core/share.py
                    # Compress + encode
                    raw = json.dumps(
                        extracted,
                        separators=(",", ":"),
                        sort_keys=True
                    ).encode("utf-8")

                    compressed = zlib.compress(raw, 9)
                    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
                    import_data = prefix + encoded

                    # Build CSV row
                    bookmark = {
                        "System": row["system"],
                        "Body": row["planet_name"],
                        "Location": row["location_index"],
                        "Coords": f"{loc_data['latitude']}, {loc_data['longitude']}",
                        "Rigs": row["rigs"],
                        "Material": row["commodity"],
                        "A/D": f"{loc_data['density']}/{loc_data['amount']}",
                        "Cmdr": loc_data["commander"],
                        "ImportData": import_data,
                    }

                    writer.writerow(bookmark)

            conn.close()
            print(f"[{self.plugin_name}] Exported to {out_file}")
            return out_file

        except Exception as e:
            print(f"[{self.plugin_name}] Export failed: {e}")
            return None


    # -----------------------------------------------------------------------
    # Preferences UI
    # -----------------------------------------------------------------------

    def build_prefs(self, parent):
        frame = nb.Frame(parent)

        tk.Label(
            frame,
            text=f"{self.plugin_name} Preferences",
            font=("TkDefaultFont", 12, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        # DB picker
        tk.Label(frame, text="RhinoSpotter database:").grid(row=1, column=0, sticky="w")

        db_var = tk.StringVar()
        autodetected = self.autodetect_db()
        if autodetected:
            db_var.set(autodetected)
            self.paths["db_path"] = autodetected

        def pick_db():
            file_path = filedialog.askopenfilename(
                title="Select RhinoSpotter DB",
                filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")]
            )
            if file_path:
                db_var.set(file_path)
                self.paths["db_path"] = file_path
            validate_export_button()

        tk.Entry(frame, textvariable=db_var, width=60).grid(row=2, column=0, sticky="w")
        tk.Button(frame, text="Browse…", command=pick_db).grid(row=2, column=1, sticky="w")

        # Output directory picker
        tk.Label(frame, text="Output directory:").grid(row=3, column=0, sticky="w", pady=(10, 0))

        out_var = tk.StringVar()
        default_export_dir = self.ensure_export_dir()
        out_var.set(default_export_dir)
        self.paths["output_dir"] = default_export_dir

        def pick_output_dir():
            dir_path = filedialog.askdirectory(title="Select output directory")
            if dir_path:
                out_var.set(dir_path)
                self.paths["output_dir"] = dir_path
            validate_export_button()

        tk.Entry(frame, textvariable=out_var, width=60).grid(row=4, column=0, sticky="w")
        tk.Button(frame, text="Browse…", command=pick_output_dir).grid(row=4, column=1, sticky="w")

        # Status message ABOVE the button
        status_var = tk.StringVar()
        status_label = tk.Label(frame, textvariable=status_var)
        status_label.grid(row=5, column=0, sticky="w", pady=(10, 0))
        status_var.set("Click Export to generate a new CSV file")
        status_label.config(fg="gray")

        # Export button
        def do_export():
            # Build the path
            today = datetime.now().strftime("%Y-%m-%d")
            expected_file = os.path.join(self.paths["output_dir"], f"RhinoExport_{today}.csv")
            existed_before = os.path.isfile(expected_file)

            # Do th export
            result = self.export_bookmarks()
            if result:
                parent_dir = os.path.basename(os.path.dirname(result))
                file_name = os.path.basename(result)
                # Indicate if written over existing
                if existed_before:
                    status_var.set(f"Success! (overwritten) {parent_dir}/{file_name}")
                    status_label.config(fg="orange")
                    status_label.after(300, lambda: status_label.config(fg="green"))
                else:
                    status_var.set(f"Success! {parent_dir}/{file_name}")
                    status_label.config(fg="green")
            else:
                # Indicate failure
                fail_name = f"RhinoExport_{today}.csv"
                status_var.set(f"Failure! Failed to write export file: '{fail_name}'")
                status_label.config(fg="red")

        export_btn = tk.Button(frame, text="Export Bookmarks", command=do_export)
        export_btn.grid(row=6, column=0, sticky="w", pady=(15, 0))

        # Open Export Dir button
        def open_export_dir():
            os.startfile(self.paths["output_dir"])

        tk.Button(frame, text="Open Export Dir", command=open_export_dir).grid(
            row=7, column=0, sticky="w", pady=(10, 0)
        )

        # Validation
        def validate_export_button():
            db_ok = os.path.isfile(self.paths["db_path"])
            out_ok = os.path.isdir(self.paths["output_dir"])
            export_btn["state"] = "normal" if (db_ok and out_ok) else "disabled"

        validate_export_button()

        return frame

    # -----------------------------------------------------------------------
    # EDMC event hooks, future use?
    # -----------------------------------------------------------------------

    def stop(self):
        # print(f"[{self.plugin_name}] plugin_stop called")
        pass

    def prefs_changed(self):
        # print(f"[{self.plugin_name}] prefs_changed called")
        pass

    def journal_entry(self, cmdr, is_beta, system, station, entry, state_data):
        # print(f"[{self.plugin_name}] Journal event: {entry.get('event')}")
        pass

    def cmdr_data(self, data, is_beta):
        # print(f"[{self.plugin_name}] Commander data received")
        pass

    def dashboard_entry(self, cmdr, is_beta, entry):
        # print(f"[{self.plugin_name}] Dashboard event: {entry.get('event')}")
        pass