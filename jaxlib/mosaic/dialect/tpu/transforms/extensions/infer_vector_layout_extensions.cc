/* Copyright 2024 The JAX Authors.

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

#include "jaxlib/mosaic/dialect/tpu/transforms/infer_vector_layout_extensions.h"

#include <array>
#include <cstdint>

#include "mlir/IR/Operation.h"
#include "mlir/Support/LLVM.h"
#include "mlir/Support/LogicalResult.h"

namespace mlir::tpu::extensions {

bool canInferVectorLayout(const Operation &op) { return false; }

LogicalResult inferVectorLayout(const Operation &op,
                                std::array<int64_t, 2> target_shape) {
  return failure();
}

}  // namespace mlir::tpu::extensions
