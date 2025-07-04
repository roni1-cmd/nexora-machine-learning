# Copyright 2023 The JAX Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for the building JAX related python packages."""

from __future__ import annotations

import os
import pathlib
import platform
import shutil
import sys
import subprocess
import glob
from collections.abc import Sequence
from jaxlib.tools import platform_tags


MAIN_RUNFILES_DIR = "__main__/"


def is_windows() -> bool:
  return sys.platform.startswith("win32")


def create_wheel_sources_map(wheel_sources, root_packages):
  """Returns a map of paths relative to the root package to the full paths."""
  wheel_sources_map = {}
  if not wheel_sources:
    return wheel_sources_map
  for source in wheel_sources:
    for package in root_packages:
      if source.startswith("{}/".format(package)):
        wheel_sources_map[source] = source
        continue
      root_package_ind = source.find("/{}/".format(package))
      if root_package_ind >= 0:
        wheel_sources_map[source[root_package_ind + 1:]] = source
  return wheel_sources_map


# TODO(ybaturina): remove the method when we switch to the new wheel build rules
# and the runfiles are not needed.
def get_source_file_prefix(wheel_sources):
  return "" if wheel_sources else MAIN_RUNFILES_DIR


def copy_file(
    src_files: str | Sequence[str],
    dst_dir: pathlib.Path,
    dst_filename=None,
    runfiles=None,
    wheel_sources_map=None,
) -> None:
  dst_dir.mkdir(parents=True, exist_ok=True)
  if isinstance(src_files, str):
    src_files = [src_files]
  for src_file in src_files:
    if wheel_sources_map:
      src_file_loc = wheel_sources_map.get(src_file, None)
    # TODO(ybaturina): remove the runfiles part when we switch to the new wheel
    # build rules and the runfiles are not needed.
    elif runfiles:
      src_file_loc = runfiles.Rlocation(src_file)
    else:
      raise RuntimeError(
          "Either runfiles or wheel_sources_map should be provided!"
      )
    if src_file_loc is None:
      raise ValueError(f"Unable to find wheel source file {src_file}")

    src_filename = os.path.basename(src_file_loc)
    dst_file = os.path.join(dst_dir, dst_filename or src_filename)
    if is_windows():
      shutil.copyfile(src_file_loc, dst_file)
    else:
      shutil.copy(src_file_loc, dst_file)


def platform_tag(cpu: str) -> str:
  platform_name, cpu_name = platform_tags.PLATFORM_TAGS_DICT[
      (platform.system(), cpu)
  ]
  return f"{platform_name}_{cpu_name}"


def build_wheel(
    sources_path: str,
    output_path: str,
    package_name: str,
    git_hash: str = "",
    build_wheel_only: bool = True,
    build_source_package_only: bool = False,
) -> None:
  """Builds a wheel in `output_path` using the source tree in `sources_path`."""
  env = dict(os.environ)
  if git_hash:
    env["JAX_GIT_HASH"] = git_hash
  if is_windows() and (
      "USERPROFILE" not in env
      and "HOMEDRIVE" not in env
      and "HOMEPATH" not in env
  ):
    env["USERPROFILE"] = env.get("SYSTEMDRIVE", "C:")
  subprocess.run(
      [sys.executable, "-m", "build", "-n"]
      + (["-w"] if build_wheel_only else [])
      + (["-s"] if build_source_package_only else []),
      check=True,
      cwd=sources_path,
      env=env,
  )
  for wheel in glob.glob(os.path.join(sources_path, "dist", "*.whl")):
    output_file = os.path.join(output_path, os.path.basename(wheel))
    sys.stderr.write(f"Output wheel: {output_file}\n\n")
    sys.stderr.write(f"To install the newly-built {package_name} wheel " +
                     "on system Python, run:\n")
    sys.stderr.write(f"  pip install {output_file} --force-reinstall\n\n")

    py_version = ".".join(platform.python_version_tuple()[:-1])
    sys.stderr.write(f"To install the newly-built {package_name} wheel " +
                     "on hermetic Python, run:\n")
    sys.stderr.write(f'  echo -e "\\n{output_file}" >> build/requirements.in\n')
    sys.stderr.write("  bazel run //build:requirements.update" +
                     f" --repo_env=HERMETIC_PYTHON_VERSION={py_version}\n\n")
    shutil.copy(wheel, output_path)
  if build_source_package_only:
    for dist in glob.glob(os.path.join(sources_path, "dist", "*.tar.gz")):
      output_file = os.path.join(output_path, os.path.basename(dist))
      sys.stderr.write(f"Output source package: {output_file}\n\n")
      shutil.copy(dist, output_path)


def build_editable(
    sources_path: str, output_path: str, package_name: str
) -> None:
  sys.stderr.write(
    f"To install the editable {package_name} build, run:\n\n"
    f"  pip install -e {output_path}\n\n"
  )
  shutil.rmtree(output_path, ignore_errors=True)
  shutil.copytree(sources_path, output_path)


def update_setup_with_cuda_version(file_dir: pathlib.Path, cuda_version: str):
  src_file = file_dir / "setup.py"
  with open(src_file) as f:
    content = f.read()
  content = content.replace(
      "cuda_version = 0  # placeholder", f"cuda_version = {cuda_version}"
  )
  with open(src_file, "w") as f:
    f.write(content)

def update_setup_with_rocm_version(file_dir: pathlib.Path, rocm_version: str):
  src_file = file_dir / "setup.py"
  with open(src_file) as f:
    content = f.read()
  content = content.replace(
      "rocm_version = 0  # placeholder", f"rocm_version = {rocm_version}"
  )
  with open(src_file, "w") as f:
    f.write(content)
