from ponysynth.widgets import jupyterbridge
from IPython import display as ipd
import json
import re

tempvars = {}


def initialize():
    ipd.display(
        ipd.Javascript("""
		window.ponysynth = new Object();
		window.ponysynth.data = new Object();
		"""))


def export_data(varname, data):
    # make sure the variable name is valid
    assert re.match(r'[a-zA-Z_$][a-zA-z0-9_$]*', varname)

    # temporary variable to be read by javascript
    jupyterbridge.tempvars[varname] = json.dumps(data)

    # python commands to be executed by javascript when importing data
    import_line = "from ponysynth.widgets import jupyter_bridge"
    delete_tempvar = f"{import_line}; del jupyterbridge.tempvars['{varname}']"
    read_tempvar = f"{import_line}; print(jupyterbridge.tempvars['{varname}'])"

    exec_import = f"""
		// callback that receives the data as a JSON string
		function import_data(output) {{
			const kernel = IPython.notebook.kernel;

			// store the data in ponysynth.data
			window.ponysynth.data.{varname} = JSON.parse(output.content.text);

			// delete the temporary variable in the python side
			kernel.execute("{delete_tempvar}");

			console.log("imported into ponysynth.data.{varname}");
		}}

		// pass the python data string to the callback function
		const kernel = IPython.notebook.kernel;
		kernel.execute(
			"{read_tempvar}",
			{{iopub: {{"output": import_data}}}});"""

    ipd.display(ipd.Javascript(exec_import))
