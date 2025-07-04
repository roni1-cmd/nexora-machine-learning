/* Copyright 2023 The JAX Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include <cstdint>
#include <string>

#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "third_party/gpus/cuda/include/cuda.h"
#include "nanobind/nanobind.h"
#include "jaxlib/gpu/gpu_plugin_extension.h"
#include "jaxlib/gpu/py_client_gpu.h"
#include "jaxlib/kernel_nanobind_helpers.h"
#include "xla/pjrt/status_casters.h"

namespace nb = nanobind;

namespace xla {
namespace {

static std::string ToString(CUresult result) {
  const char* error_name;
  if (cuGetErrorName(result, &error_name)) {
    return absl::StrCat("UNKNOWN ERROR (", static_cast<int>(result), ")");
  }
  const char* error_string;
  if (cuGetErrorString(result, &error_string)) {
    return error_name;
  }
  return absl::StrCat(error_name, ": ", error_string);
}

nb::dict FfiRegistrations() {
  nb::dict dict;
  nb::dict gpu_callback_dict;
  gpu_callback_dict["instantiate"] =
      jax::EncapsulateFfiHandler(jax::cuda::kGpuTransposePlanCacheInstantiate);
  gpu_callback_dict["execute"] =
      jax::EncapsulateFfiHandler(jax::cuda::kXlaFfiPythonGpuCallback);
  dict["xla_ffi_python_gpu_callback"] = gpu_callback_dict;
  dict["xla_ffi_partitioned_python_gpu_callback"] = gpu_callback_dict;
  dict["xla_buffer_python_gpu_callback"] =
      jax::EncapsulateFfiHandler(jax::cuda::kXlaBufferPythonGpuCallback);
  dict["xla_buffer_python_gpu_callback_cmd_buffer"] =
      jax::EncapsulateFfiHandler(
          jax::cuda::kXlaBufferPythonGpuCallbackCmdBuffer);
  return dict;
}

}  // namespace

NB_MODULE(cuda_plugin_extension, m) {
  BuildGpuPluginExtension(m);
  m.def("ffi_registrations", &FfiRegistrations);

  m.def(
      "get_device_ordinal",
      [](std::intptr_t data_value) {
        if (data_value == 0) {
          return 0;
        }
        int device_ordinal;
        void* data_ptr = reinterpret_cast<void*>(data_value);
        CUresult result =
            cuPointerGetAttribute(static_cast<void*>(&device_ordinal),
                                  CU_POINTER_ATTRIBUTE_DEVICE_ORDINAL,
                                  reinterpret_cast<CUdeviceptr>(data_ptr));
        if (result != CUDA_SUCCESS) {
          xla::ThrowIfError(absl::InvalidArgumentError(absl::StrCat(
              "Not able to get the device_ordinal: ", ToString(result))));
        }
        return device_ordinal;
      },
      nb::arg("data_value"));
}
}  // namespace xla
