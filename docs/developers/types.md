# The Sematic type infrastructre


Why a registry pattern for casting and serialization logic, as opposed to a
abstract base class?

We need to support built-ins, `typing`, and custom types. So we can't have a
common abstract base class across all.

Also we want to enable any class to be a type.