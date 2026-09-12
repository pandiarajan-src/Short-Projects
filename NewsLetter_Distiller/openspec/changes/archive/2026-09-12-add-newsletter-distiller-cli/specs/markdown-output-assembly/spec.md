## Purpose

Turns the AI's markdown response — which references images only by placeholder ID — into a final, self-contained markdown digest with correctly linked local image files.

## ADDED Requirements

### Requirement: Resolve image placeholders to local files
The system SHALL replace every image placeholder ID referenced in the AI's markdown output with a markdown image link pointing to the corresponding downloaded image file's local relative path.

#### Scenario: Placeholder resolved to local asset
- **WHEN** the AI's markdown output contains `![alt text](IMAGE_2)`
- **THEN** the final written markdown SHALL contain a markdown image link to the local relative path of the asset downloaded for `IMAGE_2`

### Requirement: Validate every referenced placeholder is known
The system SHALL validate that every image placeholder ID referenced in the AI's output corresponds to an image that was actually downloaded during extraction, and SHALL treat an unresolved reference as an error rather than silently dropping or leaving it unresolved in the output.

#### Scenario: AI references an unknown placeholder ID
- **WHEN** the AI's markdown output references a placeholder ID that does not match any downloaded candidate image
- **THEN** the system SHALL exit with a non-zero status and an error identifying the invalid reference, without writing a final markdown file containing a broken placeholder

### Requirement: Write self-contained output folder
The system SHALL write the final markdown file and the local copies of every image it references into a dedicated output folder named after a slug derived from the newsletter's title, such that the folder is portable and viewable offline without depending on the original newsletter's URLs.

#### Scenario: Output folder created
- **WHEN** distillation completes successfully for a newsletter titled "Driving the Build Is Now An Essential AI Engineering Skill"
- **THEN** the system SHALL write `output/<slug>/<slug>.md` and the referenced images under `output/<slug>/assets/`, where `<slug>` is derived from the title

### Requirement: Validate output location before AI call
The system SHALL verify that the target output directory is writable before making the (potentially costly) AI API request, so that a permissions failure is reported before, not after, an AI call has been made.

#### Scenario: Output directory not writable
- **WHEN** the resolved output directory cannot be created or written to
- **THEN** the system SHALL exit with a non-zero status and an error identifying the output path problem, without making the AI API request

### Requirement: Avoid overwriting existing output without warning
The system SHALL NOT silently overwrite an existing output folder for the same slug; it SHALL either fail with a clear message or require an explicit confirmation/flag to overwrite.

#### Scenario: Output folder already exists
- **WHEN** `output/<slug>/` already exists from a prior run
- **THEN** the system SHALL exit with a non-zero status and a message indicating the existing path, unless the user has explicitly passed an overwrite option
