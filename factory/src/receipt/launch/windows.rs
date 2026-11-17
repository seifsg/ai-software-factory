//! A redirected child must not inherit the host's original command-output pipes.

use std::ffi::c_void;
use std::io;
use std::os::windows::io::{AsRawHandle, RawHandle};

const INHERIT: u32 = 1;

#[link(name = "kernel32")]
unsafe extern "system" {
    fn GetHandleInformation(handle: *mut c_void, flags: *mut u32) -> i32;
    fn SetHandleInformation(handle: *mut c_void, mask: u32, flags: u32) -> i32;
}

/// Keep the original handles private while spawning with explicitly redirected streams.
pub(super) struct PrivateStreams(Vec<RawHandle>);

impl PrivateStreams {
    pub(super) fn new() -> io::Result<Self> {
        let mut streams = Self(Vec::with_capacity(3));
        for handle in [io::stdin().as_raw_handle(), io::stdout().as_raw_handle(), io::stderr().as_raw_handle()] {
            let mut flags = 0;
            // Read-only query on the process's own standard handles. Missing streams have no inheritable handle.
            if unsafe { GetHandleInformation(handle, &mut flags) } == 0 || flags & INHERIT == 0 {
                continue;
            }
            // The launcher is single threaded. Leave the stream open and restore its flag after the spawn.
            if unsafe { SetHandleInformation(handle, INHERIT, 0) } == 0 {
                return Err(io::Error::last_os_error());
            }
            streams.0.push(handle);
        }
        Ok(streams)
    }
}

impl Drop for PrivateStreams {
    fn drop(&mut self) {
        for &handle in &self.0 {
            // These standard handles were kept open for the lifetime of the flag override.
            unsafe { SetHandleInformation(handle, INHERIT, INHERIT) };
        }
    }
}
