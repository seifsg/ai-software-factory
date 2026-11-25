//! AI Software Factory core: the run guard and the free checks, shared by the `factory` binary and the
//! pro add-on's crate (git dependency). Modules stay small; the public items below are the stable API.

pub mod closeout;
pub mod contracts;
pub mod doctor;
pub mod evidence;
pub mod git;
pub mod guard;
pub mod hook;
pub mod lint;
pub mod machine;
pub mod paths;
pub mod proof;
pub mod queue;
pub mod receipt;
pub mod reserve;
pub mod review;
pub mod run;
pub mod update;

/// Crate version; release tooling keeps it equal to the plugin version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
