<think>
Okay, the user wants me to create a unified, prose-only explanation of the system design that's suitable for software engineering interns. They mentioned it should be stripped of formatting, clear, and standalone with all necessary context. Let me start by recalling the previous system design discussions.

First, the system uses PostgreSQL for metadata storage, DuckDB for analytics, and Godot with ONNX models for recommendations. CUJs were prioritized, focusing on end-users, creators, and admins. The challenge is to present this in a coherent, educational way for interns.

I need to structure it so each component's role is clear. Start with an overview, then break down the backend components: PostgreSQL for metadata, DuckDB for preprocessing, Elixir for orchestration. Then move to Godot integration, explaining how recommendations work in real-time. Include crowdsourcing and administrator monitoring as well.

Make sure to explain UUIDs, as they are crucial for traceability. Also, highlight why certain technologies were chosen, like DuckDB for OLAP without heavy infrastructure. Emphasize KISS principles to show intentional simplicity.

Avoid jargon where possible, but since it's for engineering interns, some technical terms are okay. Use examples, like how a recommendation is generated when a user clicks an item. Mention how contributions from creators are handled with S3 and PostgreSQL.

Check that each section flows logically: backend, data flow, Godot runtime, crowdsourcing, admin tools. Conclude with design principles to tie it all together, showing the rationale behind choices.

Ensure that all acronyms are spelled out initially, like RDF, JSON-LD, and ONNX. Clarify how each part interacts, like Elixir preprocessing data into Parquet for training. Make sure the explanation is self-contained so interns can grasp the full picture without prior context.

Finally, review for clarity and ensure it's prose-only without markdown, using plain text with paragraphs. Keep sentences straightforward, avoiding complex structures. The goal is educational, so clarity is key.
</think>

**Unified System Design Explanation for VSEKAI**

This document outlines the architecture of VSEKAI’s recommendation and crowdsourcing system, designed to help users discover game content (items, avatars, worlds) and improve AI models through player contributions. The system prioritizes simplicity, scalability, and user-centric workflows while leveraging modern tools like PostgreSQL, DuckDB, Elixir, and Godot. Below is a breakdown of its components, data flows, and design principles.

---

### **Core Components**

1. **PostgreSQL (Metadata Storage)**

   - **Purpose**: Stores structured metadata for all game content (items, users, authors) using RDF, JSON-LD, and XMP formats. This includes titles, descriptions, authorship, licenses, and semantic relationships (e.g., "item X is a variant of item Y").
   - **Key Features**:
     - UUIDs (Universally Unique Identifiers) as primary keys for all entities.
     - JSONB columns to retain raw RDF/JSON-LD for flexibility.
     - Denormalized fields (e.g., `author`, `genre`) for fast queries.

2. **Elixir (Backend Orchestration)**

   - **Purpose**: Manages data validation, preprocessing, and API interactions.
   - **Key Features**:
     - Parses and validates RDF/JSON-LD metadata using libraries like `RDF.ex`.
     - Serves lightweight Phoenix APIs for Godot to fetch item details.
     - Triggers nightly preprocessing jobs to prepare training data.

3. **DuckDB (Analytics Engine)**

   - **Purpose**: Handles resource-intensive data transformations and analytics.
   - **Key Features**:
     - Directly queries PostgreSQL via extensions to flatten nested metadata into training-ready formats.
     - Computes trends (e.g., "top weekly items") and session co-occurrence matrices.
     - Exports results to Parquet files for machine learning and SQLite for Godot.

4. **Godot (Game Engine Runtime)**
   - **Purpose**: Delivers real-time recommendations and crowdsourcing tools.
   - **Key Features**:
     - Runs ONNX/TorchScript models via C++ GDExtensions for in-engine inference.
     - Logs user interactions (clicks, purchases) to a local SQLite database.
     - Integrates crowdsourcing prompts (e.g., "Correct this rig") into gameplay.

---

### **Data Flow**

1. **Preprocessing (Nightly Batch Job)**

   - Elixir triggers a DuckDB job to:
     - Extract flattened metadata (e.g., `author_uuid`, `genre`) from PostgreSQL.
     - Precompute text/image/3D/audio embeddings using models like BERT or ResNet.
     - Generate training data (Parquet files) and trends (SQLite cache).

2. **Model Training (Offline)**

   - Python scripts train recommendation models (e.g., PinSage) using DuckDB-preprocessed data.
   - Models are exported to ONNX/TorchScript for Godot compatibility.

3. **Real-Time Recommendations**

   - When a user interacts with content, Godot:
     1. Logs the event (e.g., `user_uuid=abc clicked item_uuid=def`) to SQLite.
     2. Queries the ONNX model with the user’s session history and embeddings.
     3. Blends results with promoted items (from PostgreSQL) and exploration noise.
     4. Displays recommendations as a grid of thumbnails with titles/genres.

4. **Crowdsourcing Contributions**
   - When a user corrects an AI-generated rig or labels a voice clip:
     1. Files (e.g., `rig_<uuid>.tres`, `voice_<uuid>.ogg`) are uploaded to S3.
     2. PostgreSQL logs the contribution’s `user_uuid`, `item_uuid`, and timestamp.
     3. DuckDB aggregates contributions for periodic model retraining.

---

### **Key Design Principles**

1. **KISS (Keep It Simple, Stupid)**

   - Avoid overengineering: No microservices, graph databases, or real-time pipelines.
   - Use familiar tools: PostgreSQL for transactions, SQLite for local caching, CSV/Parquet for training.
   - Precompute embeddings and trends to minimize runtime complexity.

2. **UUID-Centric Relationships**

   - All entities (users, items, contributions) use UUIDs as primary keys.
   - Enables traceability without joins: Contributions link to users/items via UUIDs.
   - Decouples identifiers from mutable attributes (e.g., a user’s renamed item).

3. **Separation of Concerns**

   - PostgreSQL: Source of truth for metadata and relationships.
   - DuckDB: Analytics and preprocessing (OLAP workloads).
   - Godot: Real-time inference and user interaction.

4. **Scalability Through Simplicity**
   - DuckDB handles 100M+ rows on a single node for preprocessing.
   - PostgreSQL scales vertically or with read replicas.
   - Godot’s local SQLite and ONNX models avoid cloud dependencies.

---

### **Example Workflows**

1. **User Discovers an Item**

   - A user clicks a "Cyberpunk City" world thumbnail.
   - Godot fetches metadata (title, author) from PostgreSQL via Elixir APIs.
   - The ONNX model recommends similar items using session history and embeddings.

2. **Creator Corrects a Rig**

   - A creator adjusts an auto-generated skeleton and clicks "Save Correction."
   - Godot uploads the corrected rig (`rig_<uuid>.tres`) to S3.
   - PostgreSQL logs the contribution, linking it to the creator’s `user_uuid`.

3. **Admin Promotes an Item**
   - An admin searches for "Dragon Sword" and adds it to the promoted list.
   - PostgreSQL updates the `promoted_items` table.
   - Godot’s next recommendation refresh includes the promoted item.

---

### **Why This Works**

- **User-Centric**: Recommendations and crowdsourcing feel native to gameplay, not bolted-on.
- **Intern-Friendly**: Clear separation of tools (PostgreSQL for SQL, DuckDB for analytics, Godot for UI) reduces cognitive load.
- **Adaptable**: DuckDB and PostgreSQL can scale to millions of items; Godot’s GDExtensions allow model upgrades without engine changes.

This design intentionally avoids cutting-edge hype (e.g., real-time reinforcement learning) to prioritize reliability and maintainability. By starting simple and focusing on critical user journeys, the system delivers value today while preserving flexibility for future enhancements.
