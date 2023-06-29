from pathlib import Path

# Acquire the location of defaults relative to the module
module_location: Path = Path(__file__).parent.parent.parent
default_run_reqs_file: Path = module_location / "env_files" / "lock-runtime.txt"
default_dev_reqs_file: Path = module_location / "env_files" / "lock-dev.txt"
run_reqs_path_str = str(default_run_reqs_file)
dev_reqs_path_str = str(default_dev_reqs_file)
