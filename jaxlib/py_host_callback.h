/* Copyright 2023 The JAX Authors

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

#ifndef JAXLIB_PY_HOST_CALLBACK_H_
#define JAXLIB_PY_HOST_CALLBACK_H_

#include <cstdint>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/types/span.h"
#include "llvm/Support/ExtensibleRTTI.h"
#include "nanobind/nanobind.h"
#include "xla/pjrt/host_callback.h"
#include "xla/python/ifrt/client.h"
#include "xla/python/ifrt/host_callback.h"
#include "xla/python/pjrt_ifrt/pjrt_host_callback.h"
#include "xla/shape.h"
#include "xla/tsl/concurrency/ref_count.h"
#include "xla/util.h"

namespace xla {

using PyLoadedHostCallback = ::xla::ifrt::LoadedHostCallback;

class PyFfiLoadedHostCallback final
    : public llvm::RTTIExtends<PyFfiLoadedHostCallback,
                               ifrt::PjRtFfiLoadedHostCallback> {
 public:
  PyFfiLoadedHostCallback(ifrt::Client* ifrt_client,
                          nanobind::callable callable)
      : llvm::RTTIExtends<PyFfiLoadedHostCallback,
                          ifrt::PjRtFfiLoadedHostCallback>(ifrt_client,
                                                           callable.ptr()),
        callable_(std::move(callable)) {}
  ~PyFfiLoadedHostCallback() override;

  ifrt::Client* client() const override { return ifrt_client_; }
  absl::StatusOr<std::string> Serialize() const override {
    return Unimplemented(
        "PyFfiLoadedHostCallback::Serialize() is not supported");
  };

  static char ID;  // NOLINT

 private:
  ifrt::Client* ifrt_client_;
  nanobind::callable callable_;
};

// `PyHostSendAndRecvLoadedHostCallback` implements a Python host callback that
// uses XLA host send and recv. This object should be passed to the compiler
// when creating `xla::ifrt::LoadedExecutable`.
//
// Serialization is supported if the Python host callback using the
// `cloudpickle` third-party library.
//
// TODO(hyeontaek): Update the comment ("compiler" to "client") after splitting
// compilation and loading.
class PyHostSendAndRecvLoadedHostCallback final
    : public llvm::RTTIExtends<PyHostSendAndRecvLoadedHostCallback,
                               ifrt::PjRtHostSendAndRecvLoadedHostCallback> {
 public:
  static absl::StatusOr<tsl::RCReference<PyHostSendAndRecvLoadedHostCallback>>
  Create(ifrt::Client* ifrt_client, nanobind::callable callable,
         absl::Span<const Shape> operand_shapes,
         absl::Span<const Shape> result_shapes,
         absl::Span<const uint16_t> send_channel_ids,
         absl::Span<const uint16_t> recv_channel_ids,
         nanobind::callable serializer);

  // PjRtLoadedHostCallback implementation.

  ~PyHostSendAndRecvLoadedHostCallback() override;

  absl::StatusOr<std::string> Serialize() const override;

  static char ID;  // NOLINT

 private:
  PyHostSendAndRecvLoadedHostCallback(
      ifrt::Client* ifrt_client,
      std::unique_ptr<xla::HostCallback> xla_host_callback,
      nanobind::callable callable, absl::Span<const Shape> operand_shapes,
      absl::Span<const Shape> result_shapes,
      absl::Span<const uint16_t> send_channel_ids,
      absl::Span<const uint16_t> recv_channel_ids,
      nanobind::callable serializer);

  template <typename T, typename... Args>
  friend tsl::RCReference<T> tsl::MakeRef(Args&&... args);

  // Retained arguments for host callback serialization.
  nanobind::callable callable_;
  std::vector<Shape> operand_shapes_;
  std::vector<Shape> result_shapes_;
  std::vector<uint16_t> send_channel_ids_;
  std::vector<uint16_t> recv_channel_ids_;
  nanobind::callable serializer_;
};

}  // namespace xla

#endif  // JAXLIB_PY_HOST_CALLBACK_H_
