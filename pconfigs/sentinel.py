# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

class SentinelOperationError(Exception):
    pass


class Sentinel(type):
    def __str__(cls):
        return "[{}]".format(cls.__name__)

    def __repr__(self):
        return str(self)

    # Arithmetic Operations
    def __add__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __sub__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __mul__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __truediv__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __floordiv__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __mod__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __pow__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # Comparison Operations
    # def __eq__(self, other):
    #     raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # def __ne__(self, other):
    #     raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __lt__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __le__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __gt__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __ge__(self, other):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # Container and Sequence Methods
    # def __getitem__(self, key):
    #     raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __setitem__(self, key, value):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __delitem__(self, key):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __iter__(self):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __len__(self):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # Boolean Conversion
    def __bool__(self):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # Attribute Access
    def __getattr__(self, name):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # def __setattr__(self, name, value):
    #     raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __delattr__(self, name):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    # Context Managers
    def __enter__(self):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")

    def __exit__(self, exc_type, exc_value, traceback):
        raise SentinelOperationError(f"Cannot perform this operation on sentinel {str(self)}")
