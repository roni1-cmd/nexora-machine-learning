/* Copyright 2022 The JAX Authors

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

#include "jaxlib/util.h"

#include <memory>
#include <vector>

#include "absl/status/status.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"
#include "absl/types/span.h"
#include "nanobind/nanobind.h"
#include "xla/pjrt/pjrt_future.h"
#include "xla/python/ifrt/array.h"
#include "xla/python/ifrt/client.h"
#include "xla/python/ifrt/future.h"
#include "xla/python/ifrt/value.h"
#include "xla/python/version.h"
#include "xla/tsl/concurrency/async_value.h"
#include "xla/tsl/concurrency/ref_count.h"
#include "xla/util.h"

namespace xla {

void BlockUntilReadyWithCancel(xla::PjRtFuture<>& future) {
  future.BlockUntilReady([](tsl::AsyncValue* value) {
    auto state = std::make_shared<absl::Notification>();
    value->AndThen([state]() { state->Notify(); });
    while (true) {
      if (state->WaitForNotificationWithTimeout(absl::Milliseconds(200))) {
        break;
      }
      nanobind::gil_scoped_acquire gil_acquire;
      if (PyErr_CheckSignals() != 0) {
        throw nanobind::python_error();
      }
    }
  });
}

absl::Status AwaitBuffersReady(absl::Span<ifrt::Array* const> ifrt_arrays) {
  if (ifrt_arrays.empty()) {
    return absl::OkStatus();
  }

  ifrt::Future<> future;
  if (ifrt_arrays.size() == 1) {
    future = ifrt_arrays[0]->GetReadyFuture();
  } else {
    std::vector<ifrt::ValueRef> values;
    values.reserve(ifrt_arrays.size());
    for (ifrt::Array* const ifrt_array : ifrt_arrays) {
      values.push_back(tsl::FormRef(ifrt_array));
    }
    ifrt::Client* const client = ifrt_arrays.front()->client();
    future = client->GetReadyFuture(values);
  }
  BlockUntilReadyWithCancel(future);
  absl::Status s = future.Await();
  if (!s.ok()) {
    // Fix up error string because some clients rely on it.
    if (s.message() == "GetReadyFuture() called on deleted or donated buffer") {
      s = InvalidArgument(
          "BlockHostUntilReady() called on deleted or donated buffer");
    }
  }
  return s;
}

}  // namespace xla
