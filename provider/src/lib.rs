//! # working-bibliography-provider
//!
//! SDK provider wrapper for the Working Bibliography Extension.
//! Declares existing capabilities through SDK contract types,
//! routes governance through the SDK runtime, produces evidence + receipts.
//!
//! ## Migration Principle
//!
//! The Python extension handles actual domain logic (search, index, storage).
//! This Rust crate provides the governance boundary — manifest, qualification,
//! capability registration, evidence, and receipt generation.
//!
//! No behavioral changes to the existing extension. This is a governance wrapper,
//! not a rewrite.

pub mod manifest;
pub mod handler;
pub mod qualification;

#[cfg(test)]
mod tests {
    use librarian_sdk::runtime::SdkRuntime;
    use crate::manifest::build_manifest;
    use crate::handler::WbHandler;
    use std::collections::HashMap;

    #[test]
    fn test_full_provider_lifecycle() {
        let mut runtime = SdkRuntime::new(1);

        // 1. Register
        runtime.register(build_manifest(), Box::new(WbHandler)).unwrap();

        // 2. Qualify
        let qual = runtime.qualify("working-bibliography-extension").unwrap();
        assert!(qual.passed);

        // 3. Activate
        runtime.activate("working-bibliography-extension").unwrap();

        // 4. Execute each capability
        let caps = vec!["artifact.read", "artifact.register", "knowledge.search",
                        "knowledge.retrieve", "provenance.read"];

        for cap in caps {
            let mut params = HashMap::new();
            params.insert("capability".into(), cap.to_string());
            params.insert("query".into(), "test".to_string());

            let report = runtime.execute(
                "working-bibliography-extension",
                "working-bibliography",  // meta-handler
                "test-entity",
                params,
            ).unwrap();

            assert!(!report.summary.is_empty());
            assert!(report.evidence_id.starts_with("evt-"));
            assert!(report.receipt_id.starts_with("rec-"));
        }
    }

    #[test]
    fn test_unknown_capability_rejected() {
        let mut runtime = SdkRuntime::new(1);
        runtime.register(build_manifest(), Box::new(WbHandler)).unwrap();
        runtime.qualify("working-bibliography-extension").unwrap();
        runtime.activate("working-bibliography-extension").unwrap();

        let mut params = HashMap::new();
        params.insert("capability".into(), "nonexistent".into());
        let result = runtime.execute(
            "working-bibliography-extension",
            "working-bibliography",
            "test",
            params,
        );
        assert!(result.is_err());
    }
}
