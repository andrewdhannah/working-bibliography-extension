//! Working Bibliography — SDK Capability Handler.
//!
//! Routes capability invocations through the SDK runtime.
//! The Python extension handles actual domain logic — this handler
//! provides the governance boundary and evidence trail.

use librarian_sdk::execution::{CapabilityHandler, ExecutionContext, HandlerOutput};

/// Handler for the Working Bibliography Extension.
///
/// Each capability maps to the existing Python extension's MCP tools.
/// The handler produces evidence + receipts through the SDK governance client.
pub struct WbHandler;

impl CapabilityHandler for WbHandler {
    fn capability_id(&self) -> &str {
        "working-bibliography" // meta-handler for all WB capabilities
    }

    fn execute(&self, context: ExecutionContext) -> Result<HandlerOutput, String> {
        let capability = context.params.get("capability").map(|s| s.as_str()).unwrap_or("unknown");

        match capability {
            "artifact.read" => handle_artifact_read(&context),
            "artifact.register" => handle_artifact_register(&context),
            "knowledge.search" => handle_knowledge_search(&context),
            "knowledge.retrieve" => handle_knowledge_retrieve(&context),
            "provenance.read" => handle_provenance_read(&context),
            other => Err(format!("Unknown capability: {}", other)),
        }
    }
}

fn handle_artifact_read(context: &ExecutionContext) -> Result<HandlerOutput, String> {
    // In production, delegates to Python MCP tool wb_get_artifact
    let artifact_id = context.params.get("artifact_id").cloned().unwrap_or_default();
    context.governance.emit_evidence("Artifact read", serde_json::json!({
        "capability": "artifact.read", "artifact_id": artifact_id
    }));
    Ok(HandlerOutput {
        summary: format!("Read artifact: {}", artifact_id),
        payload: Some(serde_json::json!({"artifact_id": artifact_id})),
    })
}

fn handle_artifact_register(context: &ExecutionContext) -> Result<HandlerOutput, String> {
    let source = context.params.get("source").cloned().unwrap_or_default();
    context.governance.emit_evidence("Artifact registered", serde_json::json!({
        "capability": "artifact.register", "source": source
    }));
    Ok(HandlerOutput {
        summary: format!("Registered artifact from: {}", source),
        payload: None,
    })
}

fn handle_knowledge_search(context: &ExecutionContext) -> Result<HandlerOutput, String> {
    let query = context.params.get("query").cloned().unwrap_or_default();
    context.governance.emit_evidence("Knowledge search", serde_json::json!({
        "capability": "knowledge.search", "query": query
    }));
    Ok(HandlerOutput {
        summary: format!("Searched: {}", query),
        payload: Some(serde_json::json!({"results": []})),
    })
}

fn handle_knowledge_retrieve(context: &ExecutionContext) -> Result<HandlerOutput, String> {
    let source_id = context.params.get("source_id").cloned().unwrap_or_default();
    context.governance.emit_evidence("Source retrieved", serde_json::json!({
        "capability": "knowledge.retrieve", "source_id": source_id
    }));
    Ok(HandlerOutput {
        summary: format!("Retrieved source: {}", source_id),
        payload: None,
    })
}

fn handle_provenance_read(context: &ExecutionContext) -> Result<HandlerOutput, String> {
    let receipt_id = context.params.get("receipt_id").cloned().unwrap_or_default();
    context.governance.emit_evidence("Provenance read", serde_json::json!({
        "capability": "provenance.read", "receipt_id": receipt_id
    }));
    Ok(HandlerOutput {
        summary: format!("Read provenance: {}", receipt_id),
        payload: None,
    })
}
