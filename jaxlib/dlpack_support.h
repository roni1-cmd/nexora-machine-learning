/* Copyright 2025 The JAX Authors

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

#ifndef JAXLIB_XLA_DLPACK_SUPPORT_H_
#define JAXLIB_XLA_DLPACK_SUPPORT_H_

#include "absl/status/statusor.h"
#include "include/dlpack/dlpack.h"
#include "xla/xla_data.pb.h"

namespace xla {

absl::StatusOr<DLDataType> PrimitiveTypeToDLDataType(PrimitiveType type);
absl::StatusOr<PrimitiveType> DLDataTypeToPrimitiveType(DLDataType type);

}  // namespace xla

#endif  // JAXLIB_XLA_DLPACK_SUPPORT_H_
