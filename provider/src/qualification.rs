//! Working Bibliography — Provider Qualification.
//!
//! Validates the Working Bibliography provider against all 4 qualification gates.
//! Uses the SDK's ProviderQualification adapter.

use librarian_sdk::qualification::ProviderQualification;
use librarian_sdk::runtime::SdkRuntime;

use crate::manifest::build_manifest;

/// Run full qualification against the Working Bibliography provider manifest.
pub fn qualify_provider(runtime: &mut SdkRuntime) {
    let manifest = build_manifest();
    runtime.register(manifest, Box::new(crate::handler::WbHandler)).unwrap();
    let result = runtime.qualify("working-bibliography-extension").unwrap();
    assert!(result.passed, "Qualification must pass for valid provider");
    assert!(result.evidence_id.is_some(), "Qualification must produce evidence");
    assert!(result.receipt_id.is_some(), "Qualification must produce receipt");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_qualification_passes() {
        let mut runtime = SdkRuntime::new(1);
        let manifest = build_manifest();
        runtime.register(manifest, Box::new(crate::handler::WbHandler)).unwrap();
        let result = runtime.qualify("working-bibliography-extension").unwrap();
        assert!(result.passed, "Working Bibliography qualification should pass");
        assert_eq!(result.checks.len(), 4, "All 4 qualification gates must run");
    }

    #[test]
    fn test_qualification_evidence_produced() {
        let mut runtime = SdkRuntime::new(1);
        let manifest = build_manifest();
        runtime.register(manifest, Box::new(crate::handler::WbHandler)).unwrap();
        let result = runtime.qualify("working-bibliography-extension").unwrap();
        assert!(result.evidence_id.is_some(), "Qualification must emit evidence");
        assert!(result.receipt_id.is_some(), "Qualification must emit receipt");
    }

    #[test]
    fn test_all_qualification_gates_pass() {
        use librarian_sdk::runtime::SdkRuntime;
        let mut runtime = SdkRuntime::new(1);
        let manifest = build_manifest();
        runtime.register(manifest, Box::new(crate::handler::WbHandler)).unwrap();
        let result = runtime.qualify("working-bibliography-extension").unwrap();
        for check in &result.checks {
            assert!(check.passed, "Gate '{}' failed: {}", check.name, check.detail);
        }
    }
}
