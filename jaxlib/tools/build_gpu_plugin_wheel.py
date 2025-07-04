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

# Script that builds a jax cuda/rocm plugin wheel, intended to be run via bazel run
# as part of the jax cuda/rocm plugin build process.

# Most users should not run this script directly; use build.py instead.

import argparse
import functools
import os
import pathlib
import tempfile

from bazel_tools.tools.python.runfiles import runfiles
from jaxlib.tools import build_utils

parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
parser.add_argument(
    "--sources_path",
    default=None,
    help="Path in which the wheel's sources should be prepared. Optional. If "
    "omitted, a temporary directory will be used.",
)
parser.add_argument(
    "--output_path",
    default=None,
    required=True,
    help="Path to which the output wheel should be written. Required.",
)
parser.add_argument(
    "--jaxlib_git_hash",
    default="",
    required=True,
    help="Git hash. Empty if unknown. Optional.",
)
parser.add_argument(
    "--cpu", default=None, required=True, help="Target CPU architecture. Required."
)
parser.add_argument(
    "--platform_version",
    default=None,
    required=True,
    help="Target CUDA/ROCM version. Required.",
)
parser.add_argument(
    "--editable",
    action="store_true",
    help="Create an 'editable' jax cuda/rocm plugin build instead of a wheel.",
)
parser.add_argument(
    "--enable-cuda",
    default=False,
    help="Should we build with CUDA enabled? Requires CUDA and CuDNN.")
parser.add_argument(
    "--enable-rocm",
    default=False,
    help="Should we build with ROCM enabled?")
parser.add_argument(
    "--srcs", help="source files for the wheel", action="append"
)
args = parser.parse_args()

r = runfiles.Create()


def write_setup_cfg(sources_path, cpu):
  tag = build_utils.platform_tag(cpu)
  with open(sources_path / "setup.cfg", "w") as f:
    f.write(
        f"""[metadata]
license_files = LICENSE.txt

[bdist_wheel]
plat_name={tag}
python_tag=py3
"""
    )

def prepare_cuda_plugin_wheel(
    wheel_sources_path: pathlib.Path, *, cpu, cuda_version, wheel_sources
):
  """Assembles a source tree for the wheel in `wheel_sources_path`"""
  source_file_prefix = build_utils.get_source_file_prefix(wheel_sources)
  wheel_sources_map = build_utils.create_wheel_sources_map(
      wheel_sources, root_packages=["jax_plugins", "jaxlib"]
  )
  copy_files = functools.partial(
      build_utils.copy_file,
      runfiles=r,
      wheel_sources_map=wheel_sources_map,
  )

  plugin_dir = wheel_sources_path / "jax_plugins" / f"xla_cuda{cuda_version}"
  copy_files(
      dst_dir=wheel_sources_path,
      src_files=[
          f"{source_file_prefix}jax_plugins/cuda/pyproject.toml",
          f"{source_file_prefix}jax_plugins/cuda/setup.py",
      ],
  )
  build_utils.update_setup_with_cuda_version(wheel_sources_path, cuda_version)
  write_setup_cfg(wheel_sources_path, cpu)
  copy_files(
      dst_dir=plugin_dir,
      src_files=[
          f"{source_file_prefix}jax_plugins/cuda/__init__.py",
          f"{source_file_prefix}jaxlib/version.py",
      ],
  )
  copy_files(
      f"{source_file_prefix}jax_plugins/cuda/pjrt_c_api_gpu_plugin.so",
      dst_dir=plugin_dir,
      dst_filename="xla_cuda_plugin.so",
  )


def prepare_rocm_plugin_wheel(
    wheel_sources_path: pathlib.Path, *, cpu, rocm_version, wheel_sources
):
  """Assembles a source tree for the ROCm wheel in `wheel_sources_path`."""
  source_file_prefix = build_utils.get_source_file_prefix(wheel_sources)
  wheel_sources_map = build_utils.create_wheel_sources_map(
      wheel_sources, root_packages=["jax_plugins", "jaxlib"]
  )
  copy_files = functools.partial(
      build_utils.copy_file,
      runfiles=r,
      wheel_sources_map=wheel_sources_map,
  )

  plugin_dir = wheel_sources_path / "jax_plugins" / f"xla_rocm{rocm_version}"
  copy_files(
      dst_dir=wheel_sources_path,
        src_files=[
          f"{source_file_prefix}jax_plugins/rocm/pyproject.toml",
          f"{source_file_prefix}jax_plugins/rocm/setup.py",
      ],
  )
  build_utils.update_setup_with_rocm_version(wheel_sources_path, rocm_version)
  write_setup_cfg(wheel_sources_path, cpu)
  copy_files(
      dst_dir=plugin_dir,
      src_files=[
          f"{source_file_prefix}jax_plugins/rocm/__init__.py",
          f"{source_file_prefix}jaxlib/version.py",
      ],
  )
  copy_files(
      f"{source_file_prefix}jax_plugins/rocm/pjrt_c_api_gpu_plugin.so",
      dst_dir=plugin_dir,
      dst_filename="xla_rocm_plugin.so",
  )


tmpdir = None
sources_path = args.sources_path
if sources_path is None:
  tmpdir = tempfile.TemporaryDirectory(prefix="jaxgpupjrt")
  sources_path = tmpdir.name

try:
  os.makedirs(args.output_path, exist_ok=True)

  if args.enable_cuda:
    prepare_cuda_plugin_wheel(
        pathlib.Path(sources_path),
        cpu=args.cpu,
        cuda_version=args.platform_version,
        wheel_sources=args.srcs,
    )
    package_name = "jax cuda plugin"
  elif args.enable_rocm:
    prepare_rocm_plugin_wheel(
        pathlib.Path(sources_path),
        cpu=args.cpu,
        rocm_version=args.platform_version,
        wheel_sources=args.srcs,
    )
    package_name = "jax rocm plugin"
  else:
    raise ValueError("Unsupported backend. Choose either 'cuda' or 'rocm'.")

  if args.editable:
    build_utils.build_editable(sources_path, args.output_path, package_name)
  else:
    build_utils.build_wheel(
        sources_path,
        args.output_path,
        package_name,
        git_hash=args.jaxlib_git_hash,
    )
finally:
  if tmpdir:
    tmpdir.cleanup()
