//! The phases a run's wall time splits into, in the block's row order.

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Phase {
    Owner,
    Plan,
    Build,
    Tests,
    Review,
    Publish,
    Queue,
    Idle,
}

impl Phase {
    pub const ALL: [Phase; 8] =
        [Phase::Owner, Phase::Plan, Phase::Build, Phase::Tests, Phase::Review, Phase::Publish, Phase::Queue, Phase::Idle];

    /// The stamp file's and `--json`'s id.
    pub fn id(self) -> &'static str {
        ["owner", "plan", "build", "tests", "review", "publish", "queue", "idle"][self as usize]
    }

    /// The block's row label, in the owner's words.
    pub fn label(self) -> &'static str {
        ["waiting on you", "plan", "build", "tests + CI", "review + gates", "publish", "waiting on queue", "idle"][self as usize]
    }

    pub fn from_id(id: &str) -> Option<Phase> {
        Phase::ALL.into_iter().find(|p| p.id() == id)
    }

    /// The phase a factory step works in: 0-4 plan, 5 build, 6 and 8 review + gates, 7 publish.
    pub fn of_step(step: &str) -> Phase {
        match step {
            "5" => Phase::Build,
            "6" | "8" => Phase::Review,
            "7" => Phase::Publish,
            _ => Phase::Plan,
        }
    }

    /// Time in this phase is lost whole: nothing ran for the run (idle) or it stood in line (queue).
    pub fn all_lost(self) -> bool {
        matches!(self, Phase::Idle | Phase::Queue)
    }
}

#[cfg(test)]
mod tests {
    use super::Phase;

    #[test]
    fn ids_round_trip_and_steps_map() {
        assert!(Phase::ALL.iter().all(|p| Phase::from_id(p.id()) == Some(*p)));
        let got: Vec<_> = ["0", "2b", "4", "5", "6", "7", "8"].map(Phase::of_step).into();
        assert_eq!(got, [Phase::Plan, Phase::Plan, Phase::Plan, Phase::Build, Phase::Review, Phase::Publish, Phase::Review]);
    }
}
