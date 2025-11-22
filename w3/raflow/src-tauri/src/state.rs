use tracing::info;

#[derive(Clone, Default)]
pub struct AppState {}

impl AppState {
    pub fn new() -> Self {
        info!("Initializing state");
        Self {}
    }
}
