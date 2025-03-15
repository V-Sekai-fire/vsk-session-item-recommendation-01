### 1. **Dense Vectors**

- **Fields**:
  - `godot_scene_input` (VARCHAR): Raw text godot engine scene (UTF-8).
  - `xmp_jsonld_input` (VARCHAR): Unicode jsonld xmp text (UTF-8).
  - `image_input` (VARCHAR): RGBA pixel data (e.g., base64-encoded PNG).
  - `audio_input` (VARCHAR): Serialized mel spectrogram (e.g., base64 string).
  - `mesh_input` (STRUCT<  
     `meshlets` STRUCT<  
     `vertices` FLOAT[3][], _-- 3D coordinates for vertices local to this meshlet_  
     `triangles` INT[3][] _-- Indices referencing local vertices (≤126 triangles)_
    > [] _-- Array of meshlets (e.g., 2 meshlets for 252 triangles)_  
    > )

  **Example**:

  ```python
  # Meshlet 0
  vertices = [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0], ...]  # Local vertices
  triangles = [[0, 1, 2], [1, 2, 3], ...]              # Up to 126 triangles
  ```

### 2. **Dense**

- **Fields**:
  - `user_id` (UUID): Unique identifier.
  - `display_name` (VARCHAR): Human-readable name (e.g., `"Forest Scene"`).
  - `slug` (VARCHAR): URL-friendly ID (e.g., `"forest-scene-1"`).

### 3. **Sparse**

- **Fields**:
  - `node_types` (MAP(VARCHAR, INT)): Counts of node types (e.g., `{"Camera": 2, "Light": 5}`).
  - `script_languages` (MAP(VARCHAR, INT)): Frequency of scripting languages (e.g., `{"GLSL": 3, "Python": 1}`).

### 4. **MultiSparse**

- **Fields**:
  - `shaders` (VARCHAR[]): Array of shader file paths (e.g., `["phong.vert", "toon.frag"]`).
