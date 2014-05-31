# Changes to twisted-csp #

## 0.2.0 ##
- ADDED: A set of deferred-based API to use with Twisted's `@inlineCallbacks`.
- ADDED: Priority and default options for `alts`.
- ADDED: Named special values:
  + `DEFAULT`: Returned as `.channel` when no operation is ready for a non-blocking `alts`.
  + `CLOSED`: Returned when taking from a closed channel (still equal to `null`).
- ADDED: `Channel.is_closed`.
- ADDED: `go_channel` and `go_deferred`.
- ADDED: Early return from a goroutine is now possible via `stop`.
- ADDED: Tests.
- CHANGED: Rename `wait` into `sleep`.
- CHANGED: `go` now takes a function and its arguments to be called, not a generator.
- FIXED: Pending puts are now properly processed when takes make place for them in the buffer.
- FIXED: `yield`ing normal values is now allowed.

## 0.1.7 ##

- Initial release.
