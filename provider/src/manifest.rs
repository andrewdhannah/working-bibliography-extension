//! Working Bibliography — SDK Provider Manifest.
//!
//! Declares the existing extension's capabilities through the SDK contract types.
//! No behavioral changes — this is a governance wrapper, not a rewrite.

use librarian_sdk::manifest::addon_manifest::{AddonManifest, StorageDecl};

/// Build the provider manifest for the Working Bibliography Extension.
pub fn build_manifest() -> AddonManifest {
    AddonManifest {
        addon_id: "working-bibliography-extension".into(),
        display_name: "Working Bibliography Extension".into(),
        version: "0.1.0".into(),
        sdk_version: 1,
        capabilities: vec![
            "working-bibliography".into(),  // single meta-capability
        ],
        storage: Some(StorageDecl { r#type: "sqlite".into() }),
        permissions: vec![
            "filesystem.read".into(),
            "storage.own".into(),
        ],
        publisher: Some("andrewdhannah".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use librarian_sdk::manifest::validation::validate_manifest;

    #[test]
    fn test_manifest_valid() {
        let manifest = build_manifest();
        assert!(validate_manifest(&manifest, 1).is_ok());
    }

    #[test]
    fn test_manifest_has_capabilities() {
        let manifest = build_manifest();
        assert_eq!(manifest.capabilities.len(), 1);
        assert!(manifest.capabilities.contains(&"working-bibliography".into()));
    }

    #[test]
    fn test_manifest_declares_storage() {
        let manifest = build_manifest();
        assert!(manifest.storage.is_some());
        assert_eq!(manifest.storage.unwrap().r#type, "sqlite");
    }
}
