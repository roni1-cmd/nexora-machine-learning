# Copyright 2018 The JAX Authors.
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

import importlib
import os
from setuptools import setup
from setuptools.dist import Distribution

__version__ = None
project_name = 'jaxlib'

def load_version_module(pkg_path):
  spec = importlib.util.spec_from_file_location(
    'version', os.path.join(pkg_path, 'version.py'))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module

_version_module = load_version_module(project_name)
__version__ = _version_module._get_version_for_build()
_cmdclass = _version_module._get_cmdclass(project_name)

with open('README.md') as f:
  _long_description = f.read()

cuda_version = os.environ.get("JAX_CUDA_VERSION")
cudnn_version = os.environ.get("JAX_CUDNN_VERSION")
if cuda_version and cudnn_version:
  __version__ += f"+cuda{cuda_version.replace('.', '')}-cudnn{cudnn_version.replace('.', '')}"

rocm_version = os.environ.get("JAX_ROCM_VERSION")
if rocm_version:
    __version__ += f"+rocm{rocm_version.replace('.', '')}"

class BinaryDistribution(Distribution):
  """This class makes 'bdist_wheel' include an ABI tag on the wheel."""

  def has_ext_modules(self):
    return True

setup(
    name=project_name,
    version=__version__,
    cmdclass=_cmdclass,
    description='XLA library for JAX',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    author='JAX team',
    author_email='jax-dev@google.com',
    packages=['jaxlib'],
    python_requires='>=3.11',
    install_requires=[
        'scipy>=1.12',
        'numpy>=1.26',
        'ml_dtypes>=0.5.0',
    ],
    url='https://github.com/jax-ml/jax',
    license='Apache-2.0',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Free Threading :: 3 - Stable",
    ],
    package_data={
        'jaxlib': [
            '*.so',
            '*.dylib',
            '*.dll',
            '*.pyd*',
            'py.typed',
            'cpu/*',
            'cuda/*',
            'cuda/nvvm/libdevice/libdevice*',
            'mosaic/*.py',
            'mosaic/dialect/gpu/*.py',
            'mosaic/gpu/*.so',
            'mosaic/python/*.py',
            'mosaic/python/*.so',
            'mlir/*.py',
            'mlir/*.pyi',
            'mlir/dialects/*.py',
            'mlir/dialects/gpu/*.py',
            'mlir/dialects/gpu/passes/*.py',
            'mlir/extras/*.py',
            'mlir/_mlir_libs/*.dll',
            'mlir/_mlir_libs/*.dylib',
            'mlir/_mlir_libs/*.so',
            'mlir/_mlir_libs/*.pyd',
            'mlir/_mlir_libs/*.py',
            'mlir/_mlir_libs/*.pyi',
            'rocm/*',
            'triton/*.py',
            'triton/*.pyi',
            'triton/*.pyd',
            'triton/*.so',
            'include/xla/ffi/api/*.h',
        ],
    },
    zip_safe=False,
    distclass=BinaryDistribution,
)
