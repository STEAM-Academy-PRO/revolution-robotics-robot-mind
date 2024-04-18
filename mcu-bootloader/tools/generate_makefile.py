import argparse
import json
import os
import shutil

import chevron

from cglue.utils.filesystem import change_file
from cglue.utils.common import list_to_chevron_list
from cglue.plugins.AsyncServerCalls import async_server_calls
from cglue.plugins.BuiltinDataTypes import builtin_data_types
from cglue.plugins.Locks import locks
from cglue.plugins.ProjectConfigCompactor import project_config_compactor
from cglue.plugins.RuntimeEvents import runtime_events
from cglue.cglue import CGlue


def generate_makefile(clean_up: bool, in_ci: bool) -> bool:
    """Generates Makefile for the project and returns whether it was changed or not."""

    rt = CGlue("./project.json")
    rt.add_plugin(project_config_compactor())
    rt.add_plugin(builtin_data_types())
    rt.add_plugin(runtime_events())
    rt.add_plugin(locks())
    rt.add_plugin(async_server_calls())

    rt.load()
    config = rt._project_config

    runtime_source = config["settings"]["generated_runtime"] + ".c"

    source_files = config["sources"]
    source_files.append(runtime_source)

    include_paths = config["includes"]

    for component in config["components"]:
        component_file = rt.component_dir(component) + "/{}"
        component_config_path = component_file.format("config.json")
        with open(component_config_path, "r") as f:
            component_config = json.load(f)

        source_files += [
            component_file.format(source) for source in component_config["source_files"]
        ]

    if in_ci:
        workspace_config = json.load(open(".vscode/settings.ci.json"))
    else:
        if not os.path.exists(".vscode/settings.json"):
            print("Looks like first run, copied vscode settings.example to settings!")
            shutil.copy(".vscode/settings.example.json", ".vscode/settings.json")

        workspace_config = json.load(open(".vscode/settings.json"))

    def gcc_binary(name: str) -> str:
        return f"{workspace_config['project.gcc.prefix']}{name}{workspace_config['project.gcc.suffix']}"

    template_context = {
        "sources": list_to_chevron_list(source_files, "source", "last"),
        "includes": list_to_chevron_list(include_paths, "path", "last"),
        "gcc": gcc_binary("gcc"),
        "objcopy": gcc_binary("objcopy"),
        "size": gcc_binary("size"),
    }
    makefile_template = open("tools/Makefile.tpl", "r").read()
    makefile_contents = chevron.render(makefile_template, template_context)

    if change_file("Makefile", makefile_contents, clean_up):
        print("New makefile generated")
        return True
    else:
        print("Makefile up to date")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cleanup", help="Clean up newly created backup", action="store_true"
    )
    parser.add_argument(
        "--ci", help="This script is running in CI", action="store_true"
    )

    args = parser.parse_args()

    generate_makefile(clean_up=args.cleanup, in_ci=args.ci)
