/* Copyright 2022 The JAX Authors.

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

// Registers MLIR dialects used by JAX.
// This module is called by mlir/__init__.py during initialization.
#include <nanobind/nanobind.h>

#include "mlir-c/Dialect/Arith.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/ControlFlow.h"
#include "mlir-c/Dialect/Func.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/GPU.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/LLVM.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/Math.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/MemRef.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/NVGPU.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/NVVM.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/SCF.h"  // IWYU pragma: keep
#include "mlir-c/Dialect/Vector.h"  // IWYU pragma: keep
#include "mlir-c/IR.h"
#include "mlir-c/Transforms.h"
#include "mlir/Bindings/Python/NanobindAdaptors.h"  // IWYU pragma: keep
#include "shardy/integrations/c/passes.h"
#include "jaxlib/mosaic/gpu/integrations/c/passes.h"
#include "xla/service/spmd/shardy/integrations/c/passes.h"

namespace nb = nanobind;

#define REGISTER_DIALECT(name)                                           \
  MlirDialectHandle name##_dialect = mlirGetDialectHandle__##name##__(); \
  mlirDialectHandleInsertDialect(name##_dialect, registry)

NB_MODULE(register_jax_dialects, m) {
  m.doc() = "Registers upstream MLIR dialects used by JAX.";

  m.def("register_dialects", [](MlirDialectRegistry registry) {
    REGISTER_DIALECT(arith);
    REGISTER_DIALECT(func);
    REGISTER_DIALECT(math);
    REGISTER_DIALECT(memref);
    REGISTER_DIALECT(scf);
    REGISTER_DIALECT(vector);
    // For Mosaic GPU
    REGISTER_DIALECT(cf);
    REGISTER_DIALECT(gpu);
    REGISTER_DIALECT(nvgpu);
    REGISTER_DIALECT(nvvm);
    REGISTER_DIALECT(llvm);
    mlirMosaicGpuRegisterPasses();
    mlirRegisterTransformsPasses();
    // For Shardy
    mlirRegisterAllSdyPassesAndPipelines();
    mlirRegisterAllXlaSdyPassesAndPipelines();
    // Transforms used by JAX.
    mlirRegisterTransformsStripDebugInfo();
  });
}
