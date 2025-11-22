# **PromptVault System Design Specification v1.1**

## **I. Introduction**

### **Purpose**

This document provides a comprehensive system design specification for the "PromptVault" desktop application, version 1.1. The design details the architecture, data flows, core data structures, and key operational sequences required to implement the application according to the defined requirements.

### **Scope Recap**

PromptVault is envisioned as a cross-platform desktop application enabling users to efficiently manage AI prompts. Key functionalities include local-first storage and search using DuckDB, AI-powered prompt polishing and metadata generation, optional cloud synchronization for sharing public prompts, and integrated analytics for usage insights. The system leverages a modern technology stack including Tauri (Rust/React) for the client, DuckDB for local persistence, Axum (Rust) for the backend API, PostgreSQL for user data, and AWS services (Kinesis, ClickHouse) for the analytics pipeline.

### **Audience**

This specification is intended for experienced software architects and engineers involved in the development of PromptVault. It assumes familiarity with the technologies involved and focuses on providing detailed technical design decisions and justifications.

## **II. System Architecture Overview**

### **High-Level Component Diagram Description**

The PromptVault system comprises several interconnected components, balancing local-first operation with cloud-based services for enhanced functionality. The core components are:

1. **PromptVault Client:** A Tauri application consisting of a Rust backend for core logic and a React frontend (using TailwindCSS and Shadcn UI) for the user interface. This client runs locally on the user's desktop (Windows, macOS, Linux).  
2. **Local DuckDB Database:** An embedded database instance managed by the Tauri Rust backend, responsible for storing all prompt data, configurations, and associated indexes (FTS, Vector) locally.  
3. **External AI Services:** Third-party APIs (e.g., OpenAI) accessed by the Tauri backend for features like prompt polishing, metadata generation, and potentially generating new prompts. API keys are managed securely.  
4. **PromptVault Backend API:** A cloud-hosted API built with Axum/Rust on AWS. It handles authentication, synchronization of public prompts, and ingestion of analytics data.  
5. **User Database:** A PostgreSQL database hosted on AWS RDS, storing user account information, authentication details, and potentially metadata related to shared prompts.  
6. **Analytics Pipeline:** An AWS-based pipeline consisting of Kinesis Data Streams for ingestion, a processing layer (Lambda or Kinesis Data Analytics), and ClickHouse as the data warehouse for storing and querying analytics events.  
7. **Cloud Storage (AWS S3):** Primarily for potential future use (e.g., storing packaged prompt bundles if that sync method were chosen) or other static assets. Minimal usage is anticipated with the recommended API-based sync.  
8. **Authentication Providers:** External identity providers like Google (Gmail) and GitHub, integrated via OAuth2 flows.

This architecture emphasizes local data ownership and performance via DuckDB, while leveraging cloud services for collaboration (sync), user identity (auth), and operational insights (analytics). The Tauri Rust backend serves as the central hub for coordinating local operations and interactions with external services.

### **Technology Stack Summary**

The technology stack is chosen to meet the requirements for performance, cross-platform compatibility, and scalability:

* **Client:** Tauri (Rust v2.x backend, latest stable), React (v18+), Tailwind CSS (v3+), Shadcn UI (latest stable)  
* **Local Database:** DuckDB (latest stable) via duckdb-rs crate  
* **Local Embeddings:** fastembed-rs (or compatible Rust library) with a selected ONNX model  
* **Client Async Runtime:** Tokio (latest stable)  
* **Server:** Rust (stable toolchain), Axum (latest stable), Tokio  
* **AI Integration:** async-openai crate or alternative Rust LLM SDKs  
* **Cloud SDK:** AWS SDK for Rust (Kinesis, S3, potentially others)  
* **User Database:** PostgreSQL (v15+) on AWS RDS  
* **Analytics Pipeline:** AWS Kinesis Data Streams, AWS Lambda/Kinesis Data Analytics (TBD), ClickHouse (latest stable)  
* **Infrastructure:** AWS  
* **Schema Definition:** Protocol Buffers (Proto3) for analytics events

Key justifications include Tauri for creating native desktop applications from web technologies with a Rust backend, Rust for its performance and safety characteristics in both client and server components, DuckDB for its high-performance embedded analytical capabilities including vector search 1, Axum for building efficient and scalable web services in Rust, and PostgreSQL for its robust, relational user data management capabilities.3

### **Overall Data Flow Description**

The primary data flows within the PromptVault system illustrate the interaction between local and cloud components:

1. **Local Prompt Management:** User interacts with the React UI \-\> Actions are sent to the Tauri Rust backend \-\> Tauri backend interacts with the local DuckDB instance for saving, editing (pre-upload), and retrieving prompts. Embeddings are calculated in the background upon saving.  
2. **Local Search:** User enters a query in the React UI \-\> Query sent to Tauri backend \-\> Tauri backend executes a hybrid search (FTS, Vector, Tag) against DuckDB \-\> Ranked results returned to UI for display.  
3. **AI Assistance:** User triggers an AI action (Polish, Metadata, Generate) in the UI \-\> Request (including prompt content or search query) sent to Tauri backend \-\> Tauri backend calls the configured external AI API \-\> Response processed by Tauri backend \-\> Results (polished text, metadata, generated prompt) returned to UI.  
4. **Authentication:** User initiates login via UI \-\> Tauri backend coordinates OAuth flow with the chosen provider (e.g., Google, GitHub) via system browser \-\> Auth code received by Tauri backend \-\> Code sent to Backend API \-\> Backend API verifies code, interacts with User DB (PostgreSQL), returns session info/user ID to Tauri backend \-\> Client stores session info.  
5. **Upload Synchronization:** Tauri backend periodically checks local DuckDB for unsaved public prompts \-\> Batches eligible prompts \-\> Sends batch to Backend API (/prompts/upload) \-\> Backend API validates and stores prompts (e.g., in PostgreSQL) \-\> Backend API confirms successful uploads \-\> Tauri backend updates uploaded\_at status in local DuckDB.  
6. **Download Synchronization:** Tauri backend periodically requests new public prompts from Backend API (/prompts/sync) using the last sync timestamp \-\> Backend API queries shared store (PostgreSQL) and returns new prompts from other users \-\> Tauri backend receives prompts, calculates embeddings, and inserts them into local DuckDB with source='synced'.  
7. **Analytics Tracking:** User actions or system events occur in the client \-\> Tauri backend generates Proto3 event messages \-\> Events are batched and queued persistently \-\> Tauri backend periodically sends batches to Backend API (/analytics/ingest) \-\> Backend API validates and forwards events to AWS Kinesis \-\> Events flow through the processing layer into ClickHouse.

These flows demonstrate the Tauri Rust backend's role as the primary orchestrator, managing local data, interfacing with external services, and ensuring reliable data synchronization and analytics transmission.

## **III. Client Application Design (Tauri/React)**

### **Component Structure Overview (React/Shadcn UI/TailwindCSS)**

The frontend will be structured using modern React principles and components. Key components include:

* MainWindow: The main application container, managing the overall layout and tab switching.  
* EditViewTab: Contains the UI elements for creating, viewing, and editing prompts, including input fields for content, synopsis, tags, AI assistance buttons, and the privacy checkbox.  
* SearchViewTab: Houses the search input, search results display area, and controls for handling empty search results (including the "Generate Prompt" feature).  
* SearchBar: A dedicated component within SearchViewTab for the search input, potentially incorporating autocomplete suggestions.  
* SearchResultsList: Displays the list of prompts matching the search query, handling item expansion, copy actions, and visual distinction between local/private and synced/public prompts.  
* PromptEditor: The core component within EditViewTab containing the main text area for prompt content and associated controls.  
* SettingsPanel: A separate view or modal for configuring application settings like the global hotkey, AI model preferences, sync intervals, and API keys.

Shadcn UI will be leveraged for building the user interface, providing accessible and composable components (like buttons, input fields, tabs, text areas, dialogs) that can be easily styled using Tailwind CSS utility classes. This approach accelerates UI development while ensuring a consistent and modern look and feel.

### **UI Tabs and Default View Logic**

The application utilizes a two-tab interface within the MainWindow:

1. **Edit/View Tab:** Facilitates prompt creation and modification (subject to immutability rules).  
2. **Search Tab:** Enables users to search their stored prompts.

As per the requirements, the application will default to opening the **Search Tab** upon activation via the global hotkey. This prioritizes the quick retrieval use case. Tab switching will be handled within the MainWindow component, updating the displayed content based on the active tab state.

### **Global Hotkey Activation and Configuration**

Tauri's built-in global shortcut functionality will be used to activate the application window from anywhere in the operating system.

* **Default Hotkey:** CmdOrCtrl+Shift+P will be pre-configured.  
* **Configuration:** Users must be able to change this hotkey via the SettingsPanel. The configured hotkey string will be stored persistently in the local app\_settings table within DuckDB. The Tauri backend will read this setting on startup and register the corresponding global shortcut.  
* **Conflict Handling:** The UI should provide clear feedback if the chosen hotkey fails to register (e.g., due to conflicts with other applications). Error handling within the Tauri Rust backend will manage registration failures reported by the operating system.

### **State Management Approach (React)**

A suitable state management solution is required for the React frontend to manage UI state, application settings, search queries, results, editor content, and communication status with the backend/AI services. Options include:

* **Zustand or Jotai:** Lightweight, atom-based state management libraries offering simplicity and performance, suitable for applications of this complexity.  
* **React Context API:** Could be used for simpler global state (like theme or settings), but might become cumbersome for more complex, frequently changing state like search results or editor content.

The chosen library (Zustand) will manage the frontend's state. Changes in state (e.g., submitting a search query, saving a prompt) will trigger commands sent to the Tauri Rust backend using Tauri's invoke mechanism. Conversely, events or data pushed from the Tauri backend (e.g., search results ready, sync completed) will update the frontend state via Tauri's event system (emit, listen).

### **Tauri Backend (Rust) Responsibilities**

The Tauri Rust backend is central to the application's architecture, handling all logic that should not reside in the frontend JavaScript context. Its key responsibilities include:

* **Database Interaction:** All CRUD operations and queries against the local DuckDB instance, including complex hybrid search execution and index management.  
* **AI Service Integration:** Securely making API calls to external AI services (OpenAI, etc.) for polishing, metadata generation, and prompt generation. Manages API keys obtained from secure storage.  
* **Embedding Calculation:** Performing text embedding generation using the fastembed-rs library in background threads (via Tokio) to avoid blocking the main thread.  
* **Synchronization Logic:** Implementing the upload and download synchronization protocols, interacting with the backend API.  
* **Analytics:** Generating, batching, queuing, and transmitting analytics events (Proto3 format) to the backend ingestion endpoint.  
* **Persistent Queues:** Managing persistent queues (e.g., using rusqlite or file-based storage) for ensuring reliable upload, download, and analytics transmission across application restarts and network interruptions.  
* **Filesystem Access:** Handling any necessary interactions with the local filesystem (e.g., for database file location, potentially importing/exporting prompts).  
* **Global Hotkey Management:** Registering and handling the global activation hotkey.

Separating this logic into the Rust backend enhances performance (leveraging Rust's speed and concurrency), security (keeping API keys and sensitive logic out of the frontend), and reliability.

## **IV. Local Data Management & Search (DuckDB)**

### **Core Data Table Design**

The local data persistence relies on an embedded DuckDB database. Two primary tables are defined:

1\. prompts Table Schema:  
This table stores the core prompt data.

| Column Name | Type | Constraints/Defaults | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PRIMARY KEY | Unique identifier for the prompt. |
| content | TEXT | NOT NULL | The main text of the prompt. |
| synopsis | TEXT |  | A brief summary, potentially AI-generated. |
| tags | TEXT |  | Array of keyword tags. Using native array type for efficient querying.5 |
| score | INTEGER | CHECK (score \>= 0 AND score \<= 100), NULLABLE | AI-generated quality score (0-100). |
| vector | FLOAT\[N\] | NULLABLE | Embedding vector (fixed-size float array, N=dimension). Native type.1 |
| owner\_id | UUID | NOT NULL | Identifier of the user who owns the prompt (local UUID initially). |
| is\_private | BOOLEAN | NOT NULL, DEFAULT TRUE | If true, prompt is local-only and never synced. |
| uploaded\_at | TIMESTAMP | NULLABLE, DEFAULT NULL | Timestamp of the first successful upload confirmation. Null if never uploaded. |
| source | TEXT | NOT NULL, DEFAULT 'local', CHECK (source IN ('local', 'synced')) | Indicates if the prompt originated locally or was downloaded via sync. |
| created\_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT\_TIMESTAMP | Timestamp of initial creation. |
| updated\_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT\_TIMESTAMP | Timestamp of last local modification *before* first upload. Static after upload. |

Rationale for vector type: Storing embeddings as a fixed-size FLOAT array (FLOAT\[N\]) aligns directly with DuckDB's ARRAY type and the usage patterns shown in the Vector Similarity Search (VSS) extension documentation.1 This native representation is expected to offer better integration and potentially higher performance for vector operations compared to storing as an opaque BLOB, leveraging DuckDB's columnar processing capabilities.5 The dimension N will depend on the chosen embedding model (e.g., 1024 for multilingual-e5-large).  
Rationale for tags type: Using DuckDB's native TEXT array type allows for direct querying and indexing capabilities on tags, which is generally more efficient and convenient than storing tags as a JSON string and parsing it during queries.  
2\. app\_settings Table (Key-Value Store):  
This table provides a simple key-value store for application configuration and state.

| Column Name | Type | Constraints/Defaults | Description |
| :---- | :---- | :---- | :---- |
| key | TEXT | PRIMARY KEY | Unique key for the setting. |
| value | JSON |  | Value of the setting (stored as JSON). |

*Example Keys:* local\_user\_id, last\_successful\_download\_timestamp, hotkey\_config, ai\_polish\_model\_endpoint, ai\_polish\_model\_name, ai\_meta\_model\_endpoint, ai\_meta\_model\_name, sync\_upload\_interval\_minutes, sync\_download\_interval\_minutes, analytics\_interval\_seconds, ai\_api\_key\_placeholder (key itself stored in keychain).

### **Embedding Generation**

* **Selected Model:** intfloat/multilingual-e5-large-instruct.  
  * *Justification:* This model demonstrates top-tier performance in multilingual benchmarks (MMTEB), surpassing many larger models while having only 560 million parameters.6 Its instruction-following capabilities are beneficial, and it supports various languages, aligning with the goal of managing diverse prompts. It balances performance, resource footprint (model size, memory usage), and multilingual capability effectively for a desktop application.6 While not explicitly listed in the fastembed-rs documentation snippets 9, fastembed generally focuses on ONNX models, and multilingual-e5-large is available in ONNX format, suggesting high compatibility likelihood. Verification during implementation is necessary.  
  * *Fallback Model:* If multilingual-e5-large-instruct proves incompatible or problematic, BAAI/bge-small-en-v1.5 (384 dimensions) is a well-supported default in fastembed-rs 9, offering good English performance and lower resource usage, though sacrificing multilingual capability.  
* **Library:** fastembed-rs.9 This Rust library is chosen for its performance, leveraging ONNX runtime for efficient CPU/GPU inference and Hugging Face tokenizers.9 It supports quantization and parallel batch processing, making it suitable for fast local embedding generation.  
* **Process:** Embedding calculation will be triggered asynchronously (using Tokio) by the Tauri Rust backend whenever a prompt's content is saved or updated (before its first upload). The content text will be passed to the fastembed-rs model. The resulting embedding vector (as Vec\<f32\>) will be stored in the vector column of the prompts table. Errors during embedding generation (e.g., model loading failure, tokenization issues) must be logged, and the vector field should remain NULL or unchanged. The process must run in the background to avoid blocking the UI.

### **Vector Indexing (DuckDB VSS Extension)**

* **Strategy:** HNSW (Hierarchical Navigable Small Worlds) index will be implemented using DuckDB's vss extension.1  
  * *Justification:* HNSW generally provides superior search accuracy (recall) compared to IVFFlat, particularly in dynamic environments where data is frequently added.10 While HNSW has higher memory usage and potentially longer build times than IVFFlat 10, its faster query speed and resilience to updates make it more suitable for the interactive search experience required by PromptVault. DuckDB's official vector search extension implements HNSW, indicating it's the recommended approach within this ecosystem.2  
* **Configuration:** The index will be created on the vector column of the prompts table.  
  **Table: HNSW Parameter Recommendations**

| Parameter | Recommended Value/Setting | Justification & Notes | Snippet Refs |
| :---- | :---- | :---- | :---- |
| Index Type | HNSW | Provided by DuckDB vss extension; offers good accuracy/speed trade-off for ANN search. | 1 |
| SQL Syntax | CREATE INDEX idx\_prompt\_vector ON prompts USING HNSW (vector) WITH (...) | Standard syntax for creating HNSW index in DuckDB VSS. | 1 |
| metric | 'cosine' | Measures similarity based on angle, suitable for normalized text embeddings. Alternatives: 'l2sq' (Euclidean), 'ip' (Inner Product). Corresponds to array\_cosine\_distance. | 1 |
| m | 16 (Default) | Max connections per layer during build. Higher \= denser graph, better recall, slower build, more memory. Start with default, tune based on recall/performance tests. | 11 |
| ef\_construction | 64 (Default) | Candidate list size during build. Higher \= better index quality, significantly slower build. Start with default, tune if build time permits and recall needs improvement. | 11 |
| ef\_search | 64 \- 128 (Runtime PRAGMA) | Candidate list size during search. Higher \= better recall, slower query. Set via PRAGMA hnsw\_ef\_search=X;. Requires empirical tuning based on desired balance between search speed and accuracy. | 11 |
| Persistence | **Option 1 (Safer MVP):** In-memory build on app start. **Option 2 (Experimental):** Enable persistence (SET hnsw\_enable\_experimental\_persistence \= true;) | DuckDB HNSW persistence is experimental (\< v0.10.3), lacks proper WAL recovery, risking corruption on crash.2 In-memory rebuild is safer initially. If enabling persistence, document risks and manual recovery steps. Monitor DuckDB updates for stable persistence. | 2 |

* **Querying:** Vector similarity search will use functions accelerated by the HNSW index, such as ORDER BY array\_cosine\_distance(vector,?::FLOAT\[N\]) LIMIT M.1

### **Full-Text Search (FTS \- DuckDB FTS Extension)**

* **Strategy:** Utilize DuckDB's built-in FTS extension, which provides capabilities similar to SQLite's FTS5, to index the content and synopsis columns for efficient keyword searching.12  
* **Configuration:** An FTS index will be created using the PRAGMA create\_fts\_index command.  
  * PRAGMA create\_fts\_index('prompts\_fts\_idx', 'prompts', 'id', 'content', 'synopsis', stemmer='porter', stopwords='english', overwrite=1); (Example syntax adapted from 12)  
  * **stemmer**: 'porter'.12 The Porter stemming algorithm is a standard choice for reducing English words to their root form, improving recall (e.g., "running" matches "run"). Other language stemmers are available if needed.12  
  * **stopwords**: 'english'.12 Uses a built-in list of common English words (like "the", "a", "is") that are ignored during indexing and searching, generally improving relevance and reducing index size. Can be set to 'none' if required.  
  * **ignore**: Default (\\\\.|\[^a-z\])+.12 This ignores punctuation and non-lowercase alphabetic characters. May need tuning if specific symbols within prompts should be searchable.  
  * **strip\_accents**: TRUE (Default: 1).12 Converts characters like 'é' to 'e', broadening matches.  
  * **lower**: TRUE (Default: 1).12 Ensures case-insensitive searching.  
* **Querying:** Searches will be performed using the match\_bm25(id\_column, query\_string, \[fields='content,synopsis'\]) function.12 This function implements the Okapi BM25 ranking algorithm, a standard and effective method for scoring document relevance in FTS. The default parameters (k1=1.2, b=0.75) are generally good starting points but can be tuned if necessary.12

### **Hybrid Search Implementation**

* **Goal:** Combine the strengths of keyword matching (FTS), semantic understanding (Vector Search), and explicit categorization (Tag Search) to provide the most relevant search results.  
* **Algorithm:**  
  1. **Input:** User provides a search query string.  
  2. **Tag Search:** Execute an exact match query against the tags array column in the prompts table: SELECT id FROM prompts WHERE list\_contains(tags,?) for each tag derived from the query (if applicable, or based on query parsing). Assign a rank of 1 to all matching IDs from this step. (Alternatively, treat tags as a filter applied *after* FTS/Vector search if exact tag matching is a primary filter). *Initial approach: Treat as separate ranked list for RRF.*  
  3. **FTS Search:** Execute SELECT id, score FROM fts\_main\_prompts\_fts\_idx WHERE match\_bm25(id,?, fields := 'content,synopsis') ORDER BY score DESC LIMIT N; (using the index created by the PRAGMA). Extract the top N results (id, bm25\_score) and their ranks (1 to N).  
  4. **Vector Search:** Calculate the embedding vector for the user's query string using the same fastembed-rs model. Execute SELECT id, array\_cosine\_distance(vector,?::FLOAT\[N\]) as dist FROM prompts ORDER BY dist ASC LIMIT M;. Extract the top M results (id, distance) and their ranks (1 to M). Note: array\_cosine\_distance returns smaller values for more similar vectors, hence ASC order.  
  5. **Result Fusion (RRF):** Combine the ranked lists of IDs from the Tag, FTS, and Vector searches using Reciprocal Rank Fusion (RRF).  
     * Collect all unique prompt ids found across the three searches.  
     * For each unique id, calculate its RRF score: ScoreRRF​(id)=∑search∈{Tag,FTS,Vector}​k+ranksearch​(id)1​  
     * Where ranksearch​(id) is the rank of the prompt id in the results list for that specific search type (assign a large rank or ignore if the ID is not present in a list).  
     * Use the constant k=60, a commonly recommended value that prevents scores from being overly dominated by top ranks and allows lower-ranked items to contribute meaningfully.15  
     * Sort the unique IDs in descending order based on their final ScoreRRF​.  
  6. **Final Retrieval:** Fetch the full prompt details (synopsis, tags, etc.) from the prompts table for the top-ranked IDs based on the RRF score.  
  7. **Output:** Display the final ranked list to the user.  
* This RRF approach effectively merges results from different paradigms (lexical, semantic, explicit tags) without needing complex score normalization, leveraging the relative rankings from each method.15

### **Search Autocomplete**

* **Strategy:** Implement custom autocomplete logic within the Tauri Rust backend, querying the local DuckDB database directly. DuckDB's built-in SQL autocomplete extension (sql\_auto\_complete) is designed for completing SQL syntax (keywords, table/column names) and is not suitable for suggesting search terms based on prompt content.19  
* **Suggestion Sources:** The autocomplete feature will draw suggestions from multiple relevant fields to provide helpful hints:  
  1. **Matching Tags:** Query distinct tags that start with the user's input: SELECT DISTINCT unnest(tags) as tag FROM prompts WHERE tag LIKE? | | '%' LIMIT 5;  
  2. **Matching Synopses (Prefix):** Query distinct synopses that start with the user's input: SELECT DISTINCT synopsis FROM prompts WHERE synopsis ILIKE? | | '%' LIMIT 5; (Using ILIKE for case-insensitivity).  
  3. **Past Search Queries:** Maintain a small, local history of recent search terms (e.g., in a separate search\_history table or potentially serialized in app\_settings). Query this history: SELECT query FROM search\_history WHERE query LIKE? | | '%' ORDER BY last\_used\_ts DESC LIMIT 3;  
* **Implementation:** The Tauri Rust backend will receive the partial query input from the React frontend. It will execute the above queries (or similar) against DuckDB concurrently. The results from these queries will be combined, deduplicated, potentially ranked (e.g., prioritizing tags and history), and the top suggestions returned to the frontend component responsible for displaying the autocomplete dropdown. This needs to be highly performant to feel instantaneous to the user.

## **V. Prompt Lifecycle & AI Integration**

### **Core Data Structures (Rust/TypeScript)**

To ensure type safety and clear data contracts between the Rust backend (Tauri) and the TypeScript frontend (React), corresponding data structures will be defined:

* **Rust (Tauri Backend \- src-tauri/src/models.rs or similar):**  
  Rust  
  use chrono::{DateTime, Utc};  
  use serde::{Deserialize, Serialize};  
  use uuid::Uuid;

  \#  
  pub enum PromptSource {  
      Local,  
      Synced,  
  }

  \#  
  pub struct Prompt {  
      pub id: Uuid,  
      pub content: String,  
      pub synopsis: Option\<String\>,  
      pub tags: Option\<Vec\<String\>\>,  
      pub score: Option\<i32\>, // Representing INTEGER 0-100  
      // vector: Vec\<f32\> \- Handled separately, not always needed for serialization  
      pub owner\_id: Uuid,  
      pub is\_private: bool,  
      pub uploaded\_at: Option\<DateTime\<Utc\>\>,  
      pub source: String, // "local" or "synced"  
      pub created\_at: DateTime\<Utc\>,  
      pub updated\_at: DateTime\<Utc\>,  
  }

  \#\[derive(Deserialize, Debug)\]  
  pub struct MetadataResponse {  
     pub synopsis: String,  
     \#\[serde(default)\] // Handle cases where AI might omit tags  
     pub tags: Vec\<String\>,  
     pub score: i32, // Assuming AI returns integer 0-100  
  }

  // Add structs for AI Polish request/response if needed

* **TypeScript (React Frontend \- src/types/prompt.ts or similar):**  
  TypeScript  
  export type PromptSource \= 'local' | 'synced';

  export interface Prompt {  
    id: string; // UUID as string  
    content: string;  
    synopsis?: string | null;  
    tags?: string | null;  
    score?: number | null; // 0-100  
    // vector not typically needed in frontend display logic  
    ownerId: string; // UUID as string  
    isPrivate: boolean;  
    uploadedAt?: string | null; // ISO 8601 timestamp string  
    source: PromptSource;  
    createdAt: string; // ISO 8601 timestamp string  
    updatedAt: string; // ISO 8601 timestamp string  
  }

  export interface MetadataResponse {  
    synopsis: string;  
    tags: string;  
    score: number; // 0-100  
  }

  // Add interfaces for AI Polish request/response if needed

These structures define the shape of prompt data as it moves between the database, the Rust backend, and the React frontend.

### **Editing Workflow and Immutability Enforcement**

The application must strictly enforce the immutability rule for prompts once they have been successfully uploaded or if they were downloaded from the cloud.

1. **Creating New Prompts:** Users create prompts in the Edit/View Tab. Upon saving, the data is inserted into the local DuckDB (source='local', uploaded\_at=NULL), and background embedding calculation is triggered.  
2. **Editing Local-Only Prompts:** If a user selects a prompt where uploaded\_at IS NULL and source \= 'local', the Edit/View Tab allows full editing of content, synopsis, tags, score, and is\_private. Saving updates the local record, sets the updated\_at timestamp, and triggers embedding recalculation if content changed.  
3. **Viewing/Interacting with Immutable Prompts:** If a user selects a prompt where uploaded\_at IS NOT NULL or source \= 'synced', the application enters a read-only mode for that prompt.  
   * **UI Enforcement:** The React components in the Edit/View Tab MUST disable input fields for content, synopsis, tags, the score display (if editable), and the is\_private checkbox. The "Save" button should be disabled or hidden.  
   * **Backend Enforcement:** While UI enforcement is primary, the Tauri Rust backend should ideally include checks to reject any attempts to update immutable fields for such prompts, providing an additional layer of safety.  
   * **Available Actions:** Actions like "Copy Content" remain available for immutable prompts.  
   * **updated\_at:** This timestamp MUST NOT be modified after the initial upload.

This strict enforcement simplifies the synchronization logic significantly by eliminating the possibility of conflicting edits between the local version and the (potentially shared) cloud version after the initial upload.

### **AI Feature Implementation**

AI features enhance the core prompt management experience. They will be implemented in the Tauri Rust backend to centralize logic and protect API keys.

* **"Polish Prompt":**  
  * **Model:** Configurable via app\_settings, defaulting to a capable model like GPT-4o for high-quality refinement.  
  * **Polishing Strategies:** The application will offer specific refinement options beyond a generic "polish" request. Users can select a strategy via a dropdown or similar UI element:  
    * Grammar & Clarity: Focus on correcting errors and improving readability.  
    * Conciseness: Aim to shorten the prompt while retaining the core intent.  
    * Keyword Optimization: Analyze and potentially add/modify keywords relevant to the prompt's purpose, aiding retrieval or AI interpretation.  
    * Style Adaptation: Adjust the tone (e.g., Formal, Casual, Technical).  
    * Target-Specific Tuning: Provide options tailored to common prompt targets (e.g., "Optimize for Mermaid syntax", "Refine for stable diffusion image generation", "Structure for code generation"). Each target would use a specific meta-prompt instructing the AI.  
  * **UI Interaction:** When polishing is complete, the UI should present a side-by-side comparison (diff view) of the original and polished prompt content. Users must have explicit actions: "Accept" (replace original content), "Reject" (discard polished version), or potentially "Edit Polished" (allow manual refinement of the AI suggestion before accepting). Clear loading indicators during the AI call and error messages on failure are essential. The async-openai crate or a similar robust Rust SDK will handle the API interaction.  
* **"Generate Metadata":**  
  * **Model:** Configurable, defaulting to a cost-effective and fast model optimized for structured output, such as GPT-4o-mini or a similar alternative.  
  * **Instruction Prompt:** A carefully crafted prompt is crucial for reliable JSON output. The following prompt aims to achieve this:  
    Plaintext  
    Analyze the following prompt content. Generate a concise, one-sentence synopsis (maximum 15 words), 3-5 relevant keyword tags (as a JSON array of strings), and a quality score (as a JSON integer between 0 and 100\) based on clarity, completeness, and potential effectiveness.

    Respond ONLY with a single, valid JSON object containing the keys "synopsis", "tags", and "score". Do not include any explanations, markdown formatting, or any text before or after the JSON object.

    Example format: {"synopsis": "A concise summary.", "tags": \["tag1", "tag2", "tag3"\], "score": 85}

    Prompt Content:  
    """  
    {prompt\_content\_here}  
    """

    JSON Response:

  * **Error Handling & Retries:** The Tauri backend must handle potential API errors (network issues, timeouts, rate limits) and invalid responses (non-JSON output, missing fields). Implement a retry mechanism (e.g., up to 2 retries with exponential backoff). If the response is not valid JSON after retries, log the failure details (including the raw response if possible) locally for debugging and notify the user. On successful parsing of the JSON, populate the corresponding synopsis, tags, and score fields in the UI/local state.  
* **Empty Search "Generate Prompt":**  
  * **Model:** Use the same powerful model configured for "Polish Prompt" (e.g., GPT-4o, configurable) to ensure high-quality generated prompts relevant to the user's search intent.  
  * **Execution Location:** Generation will be handled by the **Tauri Rust backend**. This approach is preferred over client-side JavaScript execution primarily for security (API keys remain server-side/Rust-side) and better control over the prompting logic.  
  * **Process Flow:**  
    1. User performs a search that yields no results.  
    2. The UI displays a message and presents the original search query in a text area alongside a "Generate Prompt" button.  
    3. User clicks "Generate Prompt".  
    4. The search query string is sent from the React frontend to the Tauri Rust backend.  
    5. The Tauri backend constructs an appropriate instruction for the AI model (e.g., "Based on the following user request, generate a detailed and effective AI prompt: '{search\_query}'").  
    6. The backend calls the configured AI API using the secure API key.  
    7. The AI response (the generated prompt content) is received by the backend.  
    8. The backend sends the generated content back to the React frontend.  
    9. The frontend automatically switches to the Edit/View Tab and populates the main content text area with the received prompt, allowing the user to review, refine, and save it.

## **VI. Authentication & User Management**

### **OAuth Provider Integration**

PromptVault will support user authentication via established third-party OAuth2 providers to streamline the sign-up/sign-in process.

* **Supported Providers:**  
  * **Gmail (Google OAuth2):** Standard integration using the OAuth 2.0 protocol.  
  * **GitHub (OAuth2):** Standard integration using the OAuth 2.0 protocol.  
* **WeChat Integration:** Investigating WeChat login for desktop applications reveals significant complexities. Standard OAuth flows are less common, often requiring integration with the WeChat Open Platform, potentially involving QR code scanning mechanisms managed server-side and polled client-side, or platform-specific SDKs. Given the high implementation effort and uncertainty, **WeChat integration is recommended to be deferred** until post-MVP, allowing focus on core functionality and standard OAuth providers first.  
* **Authentication Flow (Desktop):**  
  1. Client (UI) initiates the login flow for the selected provider.  
  2. Tauri backend triggers the opening of the system's default web browser (or a secure embedded web view if necessary, though external browser is often preferred for user trust) navigating to the provider's OAuth authorization URL.  
  3. User authenticates with the provider (Google/GitHub) and grants permission.  
  4. The provider redirects the browser back to a pre-registered redirect\_uri (e.g., http://localhost:{port}/oauth/callback) that the Tauri application is listening on. The redirect includes an authorization code.  
  5. The Tauri backend captures the authorization code from the incoming request on the local listener.  
  6. Tauri backend sends this authorization code to the PromptVault Backend API (/auth/callback/{provider}).  
  7. Backend API securely exchanges the code (along with client ID/secret) with the OAuth provider for an access token and refresh token.  
  8. Backend API uses the access token to fetch the user's profile information (e.g., email, user ID) from the provider.  
  9. Backend API finds or creates a corresponding user record in the User Database (PostgreSQL), potentially performing the ID migration logic (see below).  
  10. Backend API generates a session token (e.g., JWT) for the PromptVault application and returns it, along with the definitive user\_id, to the Tauri client.  
  11. Tauri client securely stores the session token and uses it for subsequent authenticated API calls. User state in the UI is updated to reflect login.

### **User ID Handling & Migration**

A critical aspect is associating prompts created locally *before* the user authenticates with their cloud account, especially handling cases where a user might use the app on multiple devices before signing in.

1. **Pre-Authentication:** On the very first launch of the application on a device, the Tauri backend generates a unique, persistent UUID (let's call it local\_user\_id). This UUID is stored locally (e.g., in the app\_settings table). All prompts created before the first successful authentication (source='local') will have their owner\_id column set to this local\_user\_id.  
2. **First Authentication (Registration):** When the user authenticates successfully for the *first time* on a device, the Tauri client sends not only the OAuth authorization code/token information but also its persistent local\_user\_id to the backend registration endpoint (e.g., /auth/register or as part of the callback handling).  
3. **Backend Registration/Migration Logic:** The backend API performs the following steps atomically:  
   * Retrieves the user's unique identifier from the OAuth provider (e.g., Google ID, GitHub ID).  
   * Checks if a user already exists in the users table associated with this *provider identifier*.  
   * **Case A: New User (Provider ID not found):**  
     * Check if the local\_user\_id sent by the client already exists as a user\_id in the users table (this indicates the user registered on *another* device first using the *same* initial local\_user\_id, which is highly unlikely but possible if the ID generation wasn't perfectly unique or if the user manually copied the local DB). If it exists, treat as Case B.  
     * If local\_user\_id does *not* exist, create a new record in the users table using the local\_user\_id as the primary user\_id. Link the OAuth provider identifier to this new user record. Return the local\_user\_id to the client as the definitive user\_id.  
   * **Case B: Existing User (Provider ID found):**  
     * This means the user has previously authenticated (possibly on another device). Retrieve the existing user\_id associated with this provider ID from the users table.  
     * Return this *existing* user\_id to the client. Do *not* use the local\_user\_id sent by the client in this case.  
4. **Client-Side Migration (Post-Registration):**  
   * The Tauri client receives the definitive user\_id from the backend API response.  
   * It compares the received user\_id with its stored local\_user\_id.  
   * **If the IDs are different:** This signifies that the user already had an account, and the local data needs to be re-associated. The client MUST perform a one-time, atomic update on the local DuckDB:  
     SQL  
     UPDATE prompts  
     SET owner\_id \= 'server\_provided\_user\_id' \-- Parameterized query  
     WHERE owner\_id \= 'current\_local\_user\_id' \-- Parameterized query  
       AND source \= 'local';

   * After the successful database update, the client MUST update its stored persistent identifier (the value associated with local\_user\_id in app\_settings) to the server\_provided\_user\_id.  
   * This entire client-side update process must be robust against interruptions.

This mechanism ensures that regardless of the order in which devices are registered, all locally created prompts (source='local') eventually get associated with the single, correct server-side user account identified by the OAuth provider. The backend acts as the source of truth for the final user\_id.

### **User Database Selection**

* **Decision:** PostgreSQL (hosted on AWS RDS).  
* **Justification:** The choice between PostgreSQL and DynamoDB for storing user account information involves evaluating trade-offs based on the specific needs of PromptVault's authentication and potential future user management features.  
  **Table: PostgreSQL vs. DynamoDB for PromptVault User Management**

| Feature | PostgreSQL (on RDS) | DynamoDB | Decision Rationale for PromptVault | Snippet Refs |
| :---- | :---- | :---- | :---- | :---- |
| **Data Model** | Relational (Tables, Schemas, Relationships) | NoSQL (Key-Value, Document), Schema-less | Relational model simplifies linking OAuth identities to a single user account and potential future features (e.g., teams, sharing permissions). | 3 |
| **Query Language** | SQL (Rich, Standardized) | Proprietary API, PartiQL (Limited SQL) | SQL's UPDATE statement simplifies the owner\_id migration logic on the client compared to potentially complex read/write operations in DynamoDB. Complex queries might be needed for future user management features. | 3 |
| **Scalability** | Vertical Scaling, Read Replicas, Manual Sharding. RDS simplifies scaling but less elastic than DynamoDB. | Automatic Horizontal Scaling, Serverless, Near-infinite scale. | User authentication data volume/traffic is unlikely to exceed RDS capabilities in the foreseeable future. DynamoDB's massive scale is likely overkill initially. | 3 |
| **Consistency** | Strong ACID Compliance by default. | Eventually Consistent Reads (default), Strongly Consistent Reads (option), Limited ACID Transactions. | Strong consistency is generally preferred for user account data and authentication state. | 3 |
| **Operational Cost** | Requires instance management (even with RDS), backups, patching (managed by RDS but still overhead). Predictable cost. | Fully Managed, Serverless, Pay-per-request (On-Demand) or Provisioned. Potentially lower idle cost, but cost can be harder to predict. | RDS reduces operational burden compared to self-hosting Postgres. While DynamoDB is lower ops, the development complexity (single-table design, migration logic) offsets this benefit for this use case. | 3 |
| **Flexibility** | High: Complex queries, joins, triggers, extensions (PostGIS, FTS). | Moderate: Optimized for key-based access; complex queries require GSI/LSI design or client-side logic. | PostgreSQL offers greater flexibility for unforeseen future requirements involving user relationships or complex queries. | 3 |
| **Ecosystem/Tools** | Mature, extensive tooling and ORM support. | Good AWS integration, but requires specific SDKs/tooling; ORM support less common for optimized patterns (single-table). | Easier integration with standard backend frameworks and libraries using SQL. | 3 |

\*Conclusion:\* While DynamoDB offers superior serverless scalability and potentially lower operational overhead \[24, 27\], PostgreSQL (managed via AWS RDS) provides better support for the required data relationships (user-to-provider links), simplifies the critical \`owner\_id\` migration logic with standard SQL \`UPDATE\`, offers stronger consistency guarantees, and provides greater flexibility for future feature development involving user data.\[3, 4, 28\] The scalability needs for user metadata are well within the capabilities of RDS. Therefore, PostgreSQL is the recommended choice.

* **Backend Schema (users table in PostgreSQL):**  
  SQL  
  CREATE TABLE users (  
      user\_id UUID PRIMARY KEY,  
      email TEXT UNIQUE, \-- Store primary email if available, nullable  
      created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT\_TIMESTAMP,  
      last\_login\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT\_TIMESTAMP  
      \-- Add other user profile fields as needed (e.g., name, avatar\_url)  
  );

  CREATE TABLE user\_authentications (  
      provider\_id TEXT NOT NULL, \-- e.g., 'google', 'github'  
      provider\_user\_id TEXT NOT NULL, \-- The unique ID from the provider  
      user\_id UUID NOT NULL REFERENCES users(user\_id) ON DELETE CASCADE,  
      \-- Store provider-specific tokens securely if needed (e.g., encrypted refresh token)  
      \-- access\_token TEXT,  
      \-- refresh\_token TEXT,  
      \-- token\_expires\_at TIMESTAMP WITH TIME ZONE,  
      created\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT\_TIMESTAMP,  
      updated\_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT\_TIMESTAMP,  
      PRIMARY KEY (provider\_id, provider\_user\_id),  
      UNIQUE (user\_id, provider\_id) \-- Ensure a user links only one account per provider  
  );

  \-- Index for faster lookup by provider details  
  CREATE INDEX idx\_user\_auth\_provider ON user\_authentications (provider\_id, provider\_user\_id);  
  \-- Index for finding authentications for a given user  
  CREATE INDEX idx\_user\_auth\_user ON user\_authentications (user\_id);  
  This schema separates core user profile information from authentication provider details, allowing a user to link multiple providers to the same users record.

## **VII. Cloud Synchronization**

### **Sync Strategy**

* **Decision:** API-based Synchronization.  
* **Justification:** The requirement is to synchronize public prompts (is\_private=false) between users via the cloud. Two primary approaches were considered: API-based sync and pre-built package downloads.  
  **Table: Sync Strategy Comparison (API vs. Packages)**

| Feature | API-based Sync (Recommended) | Pre-built Packages (Alternative) | Rationale for API Sync |
| :---- | :---- | :---- | :---- |
| **Data Freshness** | Near real-time (limited by sync interval). Clients get updates relatively quickly. | Stale (depends on package generation frequency \- hourly/daily). Users see older data. | For potentially rapidly shared or updated prompts, freshness is important for collaboration and relevance. API sync provides much lower latency for updates. |
| **Bandwidth Usage** | Efficient for frequent, small updates (only transfers new/changed data since last sync). | Potentially wasteful if packages are large and users only need a few updates. Efficient if downloading large historical batches. | Assuming frequent use and incremental updates, transferring only deltas via API is likely more bandwidth-efficient overall. |
| **Server Logic** | Relatively simpler: Query database for records newer than a timestamp. | Complex: Requires robust process to generate packages per time window, manage package storage (S3), handle consistency. | Implementing efficient database queries is generally less complex than building and maintaining a reliable package generation and management pipeline. |
| **Client Logic** | More complex: Manage last\_sync\_timestamp, handle batches, process individual records. | Simpler download action, but complex state tracking needed to know which packages have been processed. | While client logic is slightly more involved with API sync, managing a timestamp is arguably less complex than tracking processed package identifiers and handling potential overlaps or missing packages. Persistent queues are needed in both cases for reliability. |
| **Server Load** | Direct load on API server and database for each sync request. | Offloads download serving to S3, but significant load during package generation. | API load can be managed with standard scaling techniques (horizontal scaling of Axum instances, database optimization/read replicas). Package generation load can be significant and bursty. |
| **Implementation Risk** | Lower risk, relies on standard API patterns. | Higher risk due to complexity of package generation, state management, and potential for data inconsistencies. | The API-based approach leverages well-understood patterns and presents fewer complex failure modes compared to package generation and state tracking. |

\*Conclusion:\* The API-based synchronization approach is recommended due to its superior data freshness, generally simpler server logic, and potentially better bandwidth efficiency for incremental updates, despite slightly more complex client-side state management (timestamp vs. package tracking). The benefits outweigh the advantages of offloading downloads offered by the package approach for this specific use case.

### **Upload Process (Client \-\> Server)**

This process uploads locally created prompts marked as public (is\_private=false) that haven't been uploaded yet (uploaded\_at IS NULL).

1. **Trigger:** A periodic timer within the Tauri Rust backend (e.g., every 10 minutes, configurable in app\_settings).  
2. **Identify Candidates:** Query the local DuckDB: SELECT id FROM prompts WHERE is\_private \= false AND uploaded\_at IS NULL;  
3. **Persistent Upload Queue:** Add the retrieved ids to a persistent queue managed by the Tauri backend. This queue ensures that uploads are retried if the application closes or loses network connectivity before completion. A simple SQLite table or file-based queue can be used.  
4. **Batch Processing:** Periodically (or immediately after adding items), the backend process dequeues a batch of prompt ids from the queue (e.g., 10-50 IDs).  
5. **Retrieve Full Data:** For the dequeued IDs, retrieve the full prompt data required for upload (content, synopsis, tags, score, etc.) from DuckDB.  
6. **API Request:** Send the batch of prompt data in the request body of an authenticated HTTPS POST request to the backend API endpoint (e.g., /prompts/upload).  
7. **Backend API Handling (/prompts/upload):**  
   * Receives the batch of prompts.  
   * Authenticates the request using the user's session token.  
   * Validates each prompt in the batch.  
   * For each valid prompt, insert it into the shared prompt storage (e.g., a public\_prompts table in PostgreSQL), associating it with the authenticated owner\_id. Handle potential conflicts (e.g., if the same prompt ID was somehow uploaded previously).  
   * Return an HTTP 2xx response containing a list of the ids that were successfully processed and saved.  
8. **Client Confirmation & Update:**  
   * Upon receiving a successful response from the backend API, the Tauri client parses the list of successfully uploaded ids.  
   * For each confirmed id, the client updates the local DuckDB record: UPDATE prompts SET uploaded\_at \= CURRENT\_TIMESTAMP WHERE id \=?; (parameterized).  
   * Remove the successfully processed ids from the persistent upload queue.  
   * If the API request fails or returns an error, the IDs remain in the queue for a later retry attempt. Handle partial successes correctly (update/remove only the confirmed IDs).

### **Download Process (Server \-\> Client)**

This process downloads new public prompts created by *other* users since the client's last successful sync.

1. **Trigger:** A periodic timer within the Tauri Rust backend (e.g., every 30 minutes, configurable in app\_settings).  
2. **Get Last Timestamp:** Read the last\_successful\_download\_timestamp value from the local app\_settings table in DuckDB. If null (first sync), use a default value (e.g., the application's installation time or a known epoch).  
3. **API Request:** Send an authenticated HTTPS GET request to the backend API endpoint (e.g., /prompts/sync?since={timestamp\_iso8601}\&limit=100). Include the timestamp in ISO 8601 format. Use pagination (limit, potentially cursor) if the response could be large.  
4. **Backend API Handling (/prompts/sync):**  
   * Authenticates the request.  
   * Parses the since timestamp.  
   * Queries the shared prompt storage (e.g., public\_prompts table) for prompts where is\_private \= false, created\_at \> since\_timestamp, AND owner\_id\!= authenticated\_user\_id.  
   * Orders results by created\_at. Applies pagination limits.  
   * Returns an HTTP 200 response containing a list (batch) of matching prompt objects and the server's current timestamp (or the timestamp of the latest record returned) to be used as the next since value by the client.  
5. **Client Processing & Persistent Queue:**  
   * Upon receiving a successful response, the Tauri client adds the received prompt objects to a persistent *download processing queue*. This ensures downloaded prompts are processed even if the app restarts.  
   * A separate background task processes items from this queue one by one (or in small batches):  
     * For each downloaded prompt:  
       * Check if the prompt id already exists in the local DuckDB. If it exists (e.g., due to clock skew or retry logic), skip processing or log a warning.  
       * Insert the prompt data into the local prompts table. Crucially, set:  
         * source \= 'synced'  
         * is\_private \= false  
         * uploaded\_at \= server\_provided\_created\_at (Set uploaded\_at to the prompt's creation time from the server. This prevents the downloaded prompt from being re-uploaded and enforces immutability locally).  
         * Populate id, content, synopsis, tags, score, owner\_id, created\_at, updated\_at from the downloaded data.  
       * Trigger background calculation of the text embedding for the content of the newly inserted prompt and update the vector column.  
       * Once the prompt is successfully inserted and its embedding is calculated (or queued for calculation), remove it from the download processing queue.  
6. **Timestamp Update:** After *all* prompts in the received batch have been successfully processed (i.e., removed from the download processing queue), update the last\_successful\_download\_timestamp in the local app\_settings table to the server timestamp provided in the API response. This ensures that the next sync request starts from the correct point. If processing fails mid-batch, the timestamp should not be updated, ensuring failed items are re-fetched on the next cycle.

## **VIII. Analytics Pipeline**

### **Event Definition Strategy**

* **Schema:** Protocol Buffers (Proto3) will be used to define the structure of analytics events. This provides a language-neutral, platform-neutral, extensible mechanism for serializing structured data, ensuring schema consistency and efficient transmission.  
* **Core Structure:** A common structure will be used for all events, potentially including a flexible payload for event-specific properties.  
  Protocol Buffers  
  syntax \= "proto3";

  import "google/protobuf/timestamp.proto";  
  import "google/protobuf/struct.proto"; // For flexible key-value properties

  // Represents a single analytics event  
  message AnalyticsEvent {  
    string event\_id \= 1;                 // Unique UUID generated client-side for each event instance  
    string event\_name \= 2;               // CamelCase name of the event (e.g., "PromptSaved")  
    google.protobuf.Timestamp event\_time \= 3; // Accurate client-side timestamp (UTC) of when the event occurred  
    string user\_id \= 4;                  // Server-assigned user ID (if authenticated, otherwise empty/null)  
    string client\_id \= 5;                // Persistent anonymous client UUID (generated on first launch)  
    string session\_id \= 6;               // UUID for the current application session (regenerated on each launch)  
    string client\_version \= 7;           // Application version (e.g., "1.1.0")  
    string os\_type \= 8;                  // Operating system (e.g., "windows", "macos", "linux")  
    string os\_version \= 9;               // OS version string  
    google.protobuf.Struct properties \= 10; // Event-specific properties as key-value pairs  
  }

  // Represents a batch of events sent from the client  
  message AnalyticsBatch {  
    repeated AnalyticsEvent events \= 1;  
    google.protobuf.Timestamp sent\_at\_time \= 2; // Client-side timestamp when the batch was sent  
  }  
  Using google.protobuf.Struct for properties allows flexibility in adding event-specific data without constantly changing the main schema. Keys within properties should follow a consistent naming convention (e.g., snake\_case).  
* **Key Events & Properties:** The initial list of events to track includes (but is not limited to):  
  * AppLaunched: (No specific properties beyond base event data)  
  * AppClosed: session\_duration\_ms  
  * HotkeyTriggered:  
  * TabSwitched: target\_tab ('search'/'edit')  
  * PromptSaved: is\_private (bool), source ('local'/'synced' \- though saving synced shouldn't happen), content\_length (int), tags\_count (int), metadata\_source ('manual'/'ai')  
  * PromptCopied: prompt\_id (string), source ('local'/'synced')  
  * SearchPerformed: term\_length (int), result\_count\_initial (int \- before RRF), result\_count\_final (int \- after RRF), fts\_result\_count (int), vector\_result\_count (int), tag\_result\_count (int), search\_duration\_ms (int)  
  * SearchResultClicked: prompt\_id (string), rank (int), source ('local'/'synced')  
  * AIPolishRequested: prompt\_id (string), content\_length (int), strategy (string \- e.g., 'conciseness')  
  * AIPolishCompleted: prompt\_id (string), duration\_ms (int), model\_used (string), success (bool), error\_message (string, if\!success)  
  * AIGenerateMetaRequested: prompt\_id (string), content\_length (int)  
  * AIGenerateMetaCompleted: prompt\_id (string), duration\_ms (int), model\_used (string), retry\_count (int), success (bool), error\_message (string, if\!success)  
  * AIGeneratePromptRequested: search\_term\_length (int)  
  * AIGeneratePromptCompleted: duration\_ms (int), model\_used (string), success (bool), error\_message (string, if\!success)  
  * SyncStarted: type ('upload'/'download')  
  * SyncCompleted: type ('upload'/'download'), item\_count (int), duration\_ms (int)  
  * SyncFailed: type ('upload'/'download'), error\_details (string)  
  * AuthInitiated: provider ('google'/'github')  
  * AuthSuccess: provider ('google'/'github'), is\_new\_user (bool)  
  * AuthFailed: provider ('google'/'github'), error\_details (string)  
  * (This list requires refinement based on specific metrics needed for analysis).

### **Client-Side Implementation (Tauri Rust Backend)**

1. **Event Triggering:** Instrument the relevant Rust code paths within the Tauri backend to create instances of the AnalyticsEvent protobuf message when significant actions occur. Populate all fields, including event\_name, timestamps, IDs (client\_id, session\_id, user\_id if available), environment info (client\_version, os\_type), and event-specific properties.  
2. **Batching:** Accumulate generated AnalyticsEvent messages in an in-memory buffer (e.g., a Vec\<AnalyticsEvent\>).  
3. **Persistent Queue:** When the in-memory buffer reaches a certain size (e.g., 50 events) or a time threshold is met (e.g., 15 seconds), package the events into an AnalyticsBatch message. Serialize this batch message into its binary protobuf format. Store the serialized binary data in a dedicated persistent queue (separate from sync queues, e.g., using rusqlite or file storage). This ensures events generated offline or during network outages are not lost.  
4. **Transmission:** A separate background task periodically attempts to send batches from the persistent queue.  
   * Dequeue one serialized AnalyticsBatch.  
   * Send it via an HTTPS POST request to the backend analytics ingestion endpoint (e.g., /analytics/ingest) with Content-Type: application/protobuf.  
   * If the request is successful (e.g., HTTP 200 OK), remove the batch from the persistent queue.  
   * If the request fails (network error, server error), keep the batch in the queue to be retried later (implement appropriate backoff strategy).

### **Backend Implementation (Axum)**

1. **Ingestion Endpoint (/analytics/ingest):** Create an Axum handler that accepts POST requests with Content-Type: application/protobuf.  
2. **Deserialization & Validation:** Read the request body. Use a Rust protobuf library (like prost) to deserialize the binary data into the AnalyticsBatch structure. Perform basic validation: check if the batch contains events, if required fields within events are present (e.g., event\_name, event\_time, client\_id). Reject invalid batches with an appropriate HTTP error code (e.g., 400 Bad Request).  
3. **Forwarding to Kinesis:** For each valid AnalyticsEvent within the batch:  
   * Serialize the individual AnalyticsEvent back into its binary protobuf format (or keep it as a Rust struct if the processing layer handles structs).  
   * Use the AWS SDK for Rust to put the event record onto the configured AWS Kinesis Data Stream. The partitionKey could be the client\_id or user\_id to ensure related events are processed in order within a shard (if needed).  
   * Handle potential errors from Kinesis (e.g., ProvisionedThroughputExceededException) using appropriate retry logic with backoff, as recommended by AWS SDK best practices.  
4. **Response:** Return an HTTP 200 OK or 202 Accepted response to the client upon successful receipt and queuing of the batch to Kinesis.

### **Downstream Processing (AWS)**

1. **AWS Kinesis Data Stream:** Acts as a highly scalable, durable buffer for the incoming stream of raw analytics events. Decouples the ingestion endpoint from the processing and storage layers.  
2. **Processing Layer:**  
   * **Option A (AWS Lambda):** Configure a Lambda function triggered by the Kinesis stream. The Lambda function receives batches of records, deserializes the AnalyticsEvent protobufs, performs transformations (e.g., parsing the properties Struct into specific columns, potentially enriching events with geo-IP lookup based on the source IP of the ingest request if captured by API Gateway/Load Balancer), filters unwanted events, and prepares data for loading into the data warehouse.  
   * **Option B (Kinesis Data Analytics):** Use Kinesis Data Analytics for SQL or Flink applications for more complex real-time stream processing, aggregations, or anomaly detection directly on the stream before loading. Lambda is often sufficient for basic ETL.  
3. **Data Warehouse (ClickHouse):** Load the processed and transformed event data from the processing layer into a ClickHouse database. ClickHouse is well-suited for analytics workloads due to its columnar storage, fast aggregation capabilities, and SQL interface. Design a ClickHouse table schema optimized for time-series event data, potentially partitioning by date and using appropriate data types and compression codecs. Common columns would include event\_timestamp, event\_name, user\_id, client\_id, session\_id, client\_version, os\_type, and flattened columns derived from the properties struct.  
4. **Visualization & Analysis:** Use a business intelligence tool (e.g., Grafana, Tableau, Metabase) or build a custom internal web dashboard to connect to ClickHouse. This dashboard will query the aggregated data to visualize key metrics such as Daily/Monthly Active Users (DAU/MAU), feature adoption rates (e.g., AI polish usage, sync adoption), user retention cohorts, search effectiveness, performance monitoring (API latencies, error rates), and conversion funnels (e.g., search \-\> generate \-\> save).

This standard serverless analytics pipeline provides robustness, scalability, and the analytical power needed to understand user behavior and application performance.

## **IX. Core Flow Sequence Diagrams**

The following sections describe the sequence of interactions for key application workflows. These descriptions correspond to UML sequence diagrams that would visually detail the message exchanges between components.

**1\. User Saves New Public Prompt:**

* **Actors:** User, React UI, Tauri Rust Backend, DuckDB, Upload Queue  
* **Sequence:**  
  1. User fills prompt details (content, synopsis, tags) in EditViewTab (React UI) and unchecks "Keep Private".  
  2. User clicks "Save".  
  3. React UI sends SavePrompt command with prompt data to Tauri Rust Backend.  
  4. Tauri Backend validates data.  
  5. Tauri Backend generates a new UUID for the prompt id.  
  6. Tauri Backend executes INSERT INTO prompts (...) VALUES (...) in DuckDB, setting is\_private=false, uploaded\_at=NULL, source='local'.  
  7. Tauri Backend triggers asynchronous embedding calculation for the new prompt's content.  
  8. Tauri Backend adds the new prompt id to the persistent Upload Queue.  
  9. (Optional/Background) Embedding calculation completes and updates the vector column in DuckDB.  
  10. Tauri Backend sends SaveSuccess event back to React UI.  
  11. React UI clears the editor or navigates away, potentially showing a success notification.

**2\. User Performs Hybrid Search:**

* **Actors:** User, React UI, Tauri Rust Backend, DuckDB (including FTS/VSS extensions)  
* **Sequence:**  
  1. User types a query into SearchBar (React UI) and presses Enter/clicks Search.  
  2. React UI sends PerformSearch command with the query string to Tauri Rust Backend.  
  3. Tauri Backend initiates the hybrid search algorithm:  
     * **(Parallel/Sequential):** Executes Tag Search query against DuckDB (list\_contains). Gets ranked list 1 (IDs).  
     * **(Parallel/Sequential):** Executes FTS query against DuckDB FTS index (match\_bm25). Gets ranked list 2 (IDs, BM25 scores).  
     * **(Parallel/Sequential):** Calculates query embedding. Executes Vector Search query against DuckDB VSS index (array\_cosine\_distance). Gets ranked list 3 (IDs, distances).  
  4. Tauri Backend performs Reciprocal Rank Fusion (RRF) on the three ranked lists to get a final sorted list of unique prompt IDs.  
  5. Tauri Backend retrieves full prompt data (synopsis, tags, score, source) for the top N IDs from the final ranked list via a SELECT... WHERE id IN (...) query against DuckDB.  
  6. Tauri Backend sends SearchResults event containing the ordered list of prompt data back to React UI.  
  7. React UI (SearchResultsList) renders the results, distinguishing between local/private and synced prompts.

**3\. User Authenticates (First Time \- ID Migration Scenario):**

* **Actors:** User, React UI, Tauri Rust Backend, System Browser, OAuth Provider, Backend API, User DB (PostgreSQL)  
* **Sequence:**  
  1. User clicks "Login with Google/GitHub" in React UI.  
  2. React UI sends InitiateAuth command to Tauri Rust Backend.  
  3. Tauri Backend starts a local HTTP listener for the callback.  
  4. Tauri Backend opens the System Browser directing the user to the OAuth Provider's authorization URL.  
  5. User authenticates with Provider and grants permissions.  
  6. Provider redirects Browser to localhost:port/callback with an authorization code.  
  7. Tauri Backend's listener receives the code.  
  8. Tauri Backend retrieves its persistent local\_user\_id from app\_settings.  
  9. Tauri Backend sends the code and local\_user\_id to the Backend API endpoint (/auth/callback/{provider}).  
  10. Backend API exchanges code for tokens with OAuth Provider.  
  11. Backend API fetches user profile (e.g., provider ID) from Provider.  
  12. Backend API checks User DB: Finds an *existing* user linked to this provider ID (meaning user registered on another device first). Retrieves the existing server\_user\_id.  
  13. Backend API generates a session token and returns the server\_user\_id (which is *different* from the local\_user\_id sent by the client) and session token to Tauri Backend.  
  14. Tauri Backend receives the response. It detects server\_user\_id\!= local\_user\_id.  
  15. Tauri Backend executes UPDATE prompts SET owner\_id \=? WHERE owner\_id \=? AND source \= 'local' in local DuckDB, using server\_user\_id and local\_user\_id.  
  16. Tauri Backend updates the local\_user\_id value in app\_settings to server\_user\_id.  
  17. Tauri Backend securely stores the received session token.  
  18. Tauri Backend sends AuthSuccess event (with user info) back to React UI.  
  19. React UI updates to logged-in state.

**4\. Client Initiates Upload Sync Cycle:**

* **Actors:** Tauri Rust Backend (Timer), Upload Queue, DuckDB, Backend API, Shared Prompt Store (PostgreSQL)  
* **Sequence:**  
  1. Periodic Timer triggers the upload sync task in Tauri Backend.  
  2. Tauri Backend checks the persistent Upload Queue for pending prompt IDs.  
  3. If queue is not empty, dequeue a batch of IDs.  
  4. Tauri Backend retrieves full data for the batch IDs from DuckDB.  
  5. Tauri Backend sends batch data via authenticated POST to Backend API (/prompts/upload).  
  6. Backend API validates data, authenticates user, and inserts/updates prompts in the Shared Prompt Store (PostgreSQL).  
  7. Backend API returns a list of successfully processed prompt IDs.  
  8. Tauri Backend receives the success response.  
  9. For each confirmed ID, Tauri Backend executes UPDATE prompts SET uploaded\_at \= CURRENT\_TIMESTAMP WHERE id \=? in DuckDB.  
  10. Tauri Backend removes the confirmed IDs from the persistent Upload Queue.  
  11. (If errors or partial success, unconfirmed IDs remain in queue for retry).

**5\. Client Initiates Download Sync Cycle:**

* **Actors:** Tauri Rust Backend (Timer), DuckDB (app\_settings), Backend API, Shared Prompt Store (PostgreSQL), Download Processing Queue  
* **Sequence:**  
  1. Periodic Timer triggers the download sync task in Tauri Backend.  
  2. Tauri Backend reads last\_successful\_download\_timestamp from app\_settings.  
  3. Tauri Backend sends authenticated GET request to Backend API (/prompts/sync?since={timestamp}).  
  4. Backend API queries Shared Prompt Store (PostgreSQL) for public prompts from other users created after since.  
  5. Backend API returns a batch of prompt objects and the server's current timestamp.  
  6. Tauri Backend receives the batch and adds each prompt object to the persistent Download Processing Queue.  
  7. A background task processes items from the Download Processing Queue:  
     * Dequeue a prompt object.  
     * Check if ID exists locally; if so, skip.  
     * Insert prompt into local DuckDB (source='synced', uploaded\_at=created\_at).  
     * Trigger asynchronous embedding calculation for the new prompt.  
     * Remove item from queue upon successful insertion.  
  8. Once the entire batch from the API response is processed (queue related to this batch is empty), Tauri Backend updates last\_successful\_download\_timestamp in app\_settings with the timestamp received from the server.

## **X. Non-Functional Requirements Implementation**

* **Performance:**  
  * **Client:** Tauri's Rust backend ensures computationally intensive tasks (search, embeddings, sync logic) are performant. React frontend leverages virtual DOM for efficient UI updates. Native UI components via Tauri provide responsiveness. Target \<100ms for UI interactions.  
  * **Local Search:** DuckDB's vectorized execution engine, combined with HNSW vector indexes 1 and FTS indexes 12, is designed for fast analytical queries. Hybrid search (RRF) is performed efficiently in Rust. Target \<500ms for typical local searches.  
  * **AI Features:** Latency depends on external AI APIs. Clear loading states and asynchronous execution (Tokio) in the Tauri backend prevent UI blocking.  
  * **Sync/Analytics:** Batching of requests and asynchronous processing minimize performance impact.  
  * **Backend:** Axum/Rust provides a high-performance foundation for the API. PostgreSQL on RDS can be tuned and scaled. ClickHouse is optimized for fast analytics queries.  
* **Security:**  
  * **Communication:** All client-server communication MUST use HTTPS.  
  * **Authentication:** Backend API endpoints MUST be protected by robust authentication (session tokens/JWT) and authorization checks. OAuth flows use standard secure practices.  
  * **Input Validation:** Rigorous input validation MUST be performed at API boundaries (Tauri backend, Axum backend) to prevent injection attacks and malformed data issues.  
  * **Rate Limiting:** Implement rate limiting on public-facing backend API endpoints (auth, sync, analytics ingest) to prevent abuse.  
  * **AI API Key Security:** User-provided AI API keys MUST NOT be stored in plaintext in DuckDB or configuration files. They should be stored securely using the operating system's credential manager (keychain on macOS, Credential Manager on Windows, Secret Service/Keyring on Linux). Tauri plugins/crates like tauri-plugin-stronghold or platform-specific crates (keyring-rs) should be used by the Tauri Rust backend to access these credentials securely. *This addresses a key security research area.*  
  * **Local Database:** Access to the DuckDB file should be protected by standard file system permissions. Consider encryption-at-rest for the DuckDB file if highly sensitive prompts are anticipated (DuckDB supports this via extensions).  
  * **Dependencies:** Regularly scan dependencies (Rust crates via cargo audit, npm packages via npm audit) for known vulnerabilities.  
* **Scalability:**  
  * **Backend API (Axum):** Designed as stateless services suitable for horizontal scaling behind a load balancer on AWS (e.g., using ECS or EKS).  
  * **User Database (PostgreSQL on RDS):** Can be scaled vertically (larger instance types) or horizontally for reads using read replicas. RDS simplifies scaling operations.3  
  * **Analytics Pipeline:** AWS Kinesis, Lambda, and ClickHouse are all designed for high throughput and horizontal scalability.24  
  * **Client:** Scalability is less of a concern than individual instance performance. DuckDB scales well with local data volume up to available RAM/disk limits.  
* **Reliability:**  
  * **Sync & Analytics:** Persistent queues in the Tauri Rust backend ensure that upload, download processing, and analytics event transmission are resilient to network interruptions and application restarts.  
  * **Database Operations:** Critical local database operations (like the user ID migration) should be performed atomically or within transactions where possible to prevent inconsistent states. DuckDB supports transactions.22  
  * **Error Handling:** Graceful handling of errors from external APIs (AI, backend) and internal operations is required, providing informative feedback to the user where appropriate and logging details for debugging. Retry mechanisms should be implemented for transient network failures.  
  * **HNSW Persistence:** The experimental nature of DuckDB HNSW persistence 2 requires careful handling. The recommended approach is in-memory index rebuilding on startup for the MVP to ensure reliability, migrating to persistent indexes only when DuckDB offers stable support or if the experimental risks are deemed acceptable and managed.  
* **Maintainability:**  
  * **Code Quality:** Adhere to idiomatic Rust and React/TypeScript best practices, including clear module structures, meaningful naming, comments for complex logic, and documentation (e.g., using rustdoc, JSDoc/TSDoc).  
  * **Testing:** Implement a comprehensive testing strategy:  
    * Unit tests for individual functions/modules (Rust and TypeScript).  
    * Integration tests for interactions between components (e.g., Tauri backend \<-\> DuckDB, React \<-\> Tauri backend).  
    * Potential end-to-end tests for critical user flows (using tools like Playwright with Tauri driver).  
  * **Schema Management:** Use Proto3 for analytics schemas allows for backward-compatible evolution.1 Database schema migrations for DuckDB and PostgreSQL need a defined strategy (e.g., using tools like sqlx-cli for Postgres, manual SQL scripts for DuckDB).  
* **Usability:**  
  * **Interface:** Design should be intuitive, leveraging familiar patterns from desktop applications and the chosen UI library (Shadcn UI). Follow platform conventions where possible (e.g., menu bar integration, standard shortcuts).  
  * **Discoverability:** The global hotkey and core features (search, edit, AI assistance) should be easily discoverable. Onboarding tips or a brief tutorial might be considered.  
  * **Feedback:** Provide clear visual feedback for all operations: loading states for AI calls and sync, success messages, informative error messages. Search results should clearly indicate the source ('local'/'synced') and privacy status.

## **XI. Conclusion**

### **Summary of Key Design Choices**

This design specification outlines a robust architecture for PromptVault, balancing local-first performance with cloud-enabled features. Key decisions include:

* **Local Storage:** Utilizing DuckDB for its embedded nature, performance, and integrated support for FTS and HNSW-based vector search.1  
* **Hybrid Search:** Implementing Reciprocal Rank Fusion (RRF) to effectively combine results from tag, FTS, and vector searches.15  
* **Embeddings:** Selecting intfloat/multilingual-e5-large-instruct for its state-of-the-art multilingual performance and reasonable resource footprint, generated locally via fastembed-rs.6  
* **User Management:** Choosing PostgreSQL on AWS RDS for its relational capabilities, SQL flexibility (beneficial for ID migration), and strong consistency, managed via RDS to reduce operational overhead.3  
* **Synchronization:** Adopting an API-based sync mechanism for better data freshness compared to package-based approaches.  
* **AI Integration:** Performing AI operations (polish, metadata, generation) via the secure Tauri Rust backend, offering specific polishing strategies and robust JSON handling for metadata.  
* **Analytics:** Implementing a scalable pipeline using Proto3, persistent client-side queuing, and AWS Kinesis/Lambda/ClickHouse.  
* **Security:** Prioritizing secure API key storage using OS credential managers.

### **Trade-offs**

The design acknowledges inherent trade-offs:

* **PostgreSQL vs. DynamoDB:** Opting for PostgreSQL provides flexibility and easier complex operations at the cost of higher operational overhead compared to the serverless nature of DynamoDB.3  
* **HNSW vs. IVFFlat:** Choosing HNSW prioritizes search accuracy and update resilience over potentially faster build times and lower memory usage of IVFFlat.10 The experimental persistence of HNSW in current DuckDB versions also presents a reliability trade-off.2  
* **API Sync vs. Packages:** Selecting API sync favors data freshness and potentially simpler server logic over the server offloading benefits of package downloads.

### **Future Considerations**

While this design provides a comprehensive foundation, future iterations could explore:

* **Advanced Search:** Implementing more sophisticated ranking algorithms, potentially incorporating user feedback or personalized relevance tuning. Weighting different components (FTS, vector, tags) within RRF.  
* **WeChat Authentication:** Re-evaluating the feasibility and complexity of WeChat login integration.  
* **Enhanced AI Features:** Adding more diverse prompt polishing strategies, supporting different AI models/providers dynamically, or integrating AI for query understanding.  
* **Collaboration Features:** Expanding beyond simple public prompt sharing to include teams, commenting, or versioning (which would necessitate rethinking the immutability rule).  
* **DuckDB Evolution:** Monitoring DuckDB releases for stable HNSW index persistence and leveraging new features as they become available.  
* **Offline AI Models:** Investigating the feasibility of using smaller, local AI models for certain tasks (like basic metadata tagging or simple polishing) to reduce reliance on external APIs and enable offline functionality.

#### **Works cited**

1. Vector Similarity Search Extension \- DuckDB, accessed May 3, 2025, [https://duckdb.org/docs/stable/extensions/vss.html](https://duckdb.org/docs/stable/extensions/vss.html)  
2. Vector Similarity Search in DuckDB, accessed May 3, 2025, [https://duckdb.org/2024/05/03/vector-similarity-search-vss.html](https://duckdb.org/2024/05/03/vector-similarity-search-vss.html)  
3. DynamoDB vs PostgreSQL: A Concise Comparison \- Bytebase, accessed May 3, 2025, [https://www.bytebase.com/blog/dynamodb-vs-postgres/](https://www.bytebase.com/blog/dynamodb-vs-postgres/)  
4. PostgreSQL vs DynamoDB \- Sprinkle Data, accessed May 3, 2025, [https://www.sprinkledata.com/blogs/postgresql-vs-dynamodb](https://www.sprinkledata.com/blogs/postgresql-vs-dynamodb)  
5. Vectors \- DuckDB, accessed May 3, 2025, [https://duckdb.org/docs/clients/c/vector.html](https://duckdb.org/docs/clients/c/vector.html)  
6. MMTEB: Massive Multilingual Text Embedding Benchmark \- arXiv, accessed May 3, 2025, [https://arxiv.org/html/2502.13595v1](https://arxiv.org/html/2502.13595v1)  
7. MMTEB: Massive Multilingual Text Embedding Benchmark \- OpenReview, accessed May 3, 2025, [https://openreview.net/forum?id=zl3pfz4VCV](https://openreview.net/forum?id=zl3pfz4VCV)  
8. Top embedding models for RAG | Modal Blog, accessed May 3, 2025, [https://modal.com/blog/embedding-models-article](https://modal.com/blog/embedding-models-article)  
9. fastembed \- Rust Package Registry \- Crates.io, accessed May 3, 2025, [https://crates.io/crates/fastembed/3.2.0](https://crates.io/crates/fastembed/3.2.0)  
10. Vector Search Demystified: A Guide to pgvector, IVFFlat, and HNSW \- DEV Community, accessed May 3, 2025, [https://dev.to/cubesoft/vector-search-demystified-a-guide-to-pgvector-ivfflat-and-hnsw-36hf](https://dev.to/cubesoft/vector-search-demystified-a-guide-to-pgvector-ivfflat-and-hnsw-36hf)  
11. Vector Indexes in Postgres using pgvector: IVFFlat vs HNSW \- Tembo, accessed May 3, 2025, [https://tembo.io/blog/vector-indexes-in-pgvector](https://tembo.io/blog/vector-indexes-in-pgvector)  
12. Full-Text Search Extension \- DuckDB, accessed May 3, 2025, [https://duckdb.org/docs/stable/extensions/full\_text\_search.html](https://duckdb.org/docs/stable/extensions/full_text_search.html)  
13. SQLite FTS5 Extension, accessed May 3, 2025, [https://sqlite.org/fts5.html](https://sqlite.org/fts5.html)  
14. SQLite FTS5 Extension \- Hwaci, accessed May 3, 2025, [https://www.hwaci.com/sw/sqlite/fts5.html](https://www.hwaci.com/sw/sqlite/fts5.html)  
15. Hybrid search in Spanner: combine full-text and vector search | Google Cloud Blog, accessed May 3, 2025, [https://cloud.google.com/blog/topics/developers-practitioners/hybrid-search-in-spanner-combine-full-text-and-vector-search](https://cloud.google.com/blog/topics/developers-practitioners/hybrid-search-in-spanner-combine-full-text-and-vector-search)  
16. Relevance scoring in hybrid search using Reciprocal Rank Fusion (RRF) \- Learn Microsoft, accessed May 3, 2025, [https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)  
17. Hybrid Search Explained | Weaviate, accessed May 3, 2025, [https://weaviate.io/blog/hybrid-search-explained](https://weaviate.io/blog/hybrid-search-explained)  
18. About hybrid search | Vertex AI | Google Cloud, accessed May 3, 2025, [https://cloud.google.com/vertex-ai/docs/vector-search/about-hybrid-search](https://cloud.google.com/vertex-ai/docs/vector-search/about-hybrid-search)  
19. Autocomplete \- DuckDB, accessed May 3, 2025, [https://duckdb.org/docs/stable/clients/cli/autocomplete.html](https://duckdb.org/docs/stable/clients/cli/autocomplete.html)  
20. AutoComplete Extension \- DuckDB, accessed May 3, 2025, [https://duckdb.org/docs/stable/extensions/autocomplete.html](https://duckdb.org/docs/stable/extensions/autocomplete.html)  
21. Overview of DuckDB Internals, accessed May 3, 2025, [https://duckdb.org/docs/stable/internals/overview.html](https://duckdb.org/docs/stable/internals/overview.html)  
22. Docs \- DuckDB Database Management in VS Code \- DBCode, accessed May 3, 2025, [https://dbcode.io/docs/supported-databases/duckdb](https://dbcode.io/docs/supported-databases/duckdb)  
23. Postgres vs. DynamoDB: Which Database to Choose \- TestDriven.io, accessed May 3, 2025, [https://testdriven.io/blog/postgres-vs-dynamodb/](https://testdriven.io/blog/postgres-vs-dynamodb/)  
24. Is anyone using aws dynamoDB for a large database?, accessed May 3, 2025, [https://repost.aws/questions/QU28AAR6FsRmmvgq5ozFQ6Sw/is-anyone-using-aws-dynamodb-for-a-large-database](https://repost.aws/questions/QU28AAR6FsRmmvgq5ozFQ6Sw/is-anyone-using-aws-dynamodb-for-a-large-database)  
25. Compare AWS DynamoDB vs PostgreSQL \- InfluxDB, accessed May 3, 2025, [https://www.influxdata.com/comparison/dynamodb-vs-postgres/](https://www.influxdata.com/comparison/dynamodb-vs-postgres/)  
26. Compare AWS DynamoDB vs PostgreSQL, accessed May 3, 2025, [https://beta.influxstaging.com/comparison/dynamodb-vs-postgres/](https://beta.influxstaging.com/comparison/dynamodb-vs-postgres/)  
27. PostgreSQL vs DynamoDB: Understanding Key Differences \- w3resource, accessed May 3, 2025, [https://www.w3resource.com/PostgreSQL/snippets/postgresql-vs-dynamodb.php](https://www.w3resource.com/PostgreSQL/snippets/postgresql-vs-dynamodb.php)  
28. DynamoDB vs PostgreSQL \- Key Differences \- Airbyte, accessed May 3, 2025, [https://airbyte.com/data-engineering-resources/dynamodb-vs-postgres](https://airbyte.com/data-engineering-resources/dynamodb-vs-postgres)