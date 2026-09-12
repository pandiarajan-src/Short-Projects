## Purpose

Fetches a newsletter URL over HTTP(S) and extracts clean main-article text plus candidate concept images with metadata, stripping structural boilerplate mechanically without judging promotional intent.

## ADDED Requirements

### Requirement: URL scheme validation
The system SHALL only accept `http://` and `https://` URLs as input, rejecting any other scheme before making a network request.

#### Scenario: Rejects non-http(s) URL
- **WHEN** the user supplies a URL with a scheme other than http or https (e.g., `file://`, `ftp://`)
- **THEN** the system SHALL exit with a non-zero status and an error message identifying the invalid scheme, without attempting to fetch it

### Requirement: Fetch newsletter content
The system SHALL fetch the HTML content at the given URL over HTTP(S) with an explicit network timeout, and SHALL report a clear, actionable error (with non-zero exit code) if the request fails, times out, or returns a non-success HTTP status.

#### Scenario: Successful fetch
- **WHEN** the URL responds with HTTP 200 and HTML content within the timeout
- **THEN** the system SHALL proceed to content extraction with the returned HTML

#### Scenario: Network failure or timeout
- **WHEN** the request times out or the connection fails
- **THEN** the system SHALL exit with a non-zero status and an error message describing the network failure, without proceeding to AI processing

#### Scenario: Non-success HTTP status
- **WHEN** the server responds with a 4xx or 5xx status code
- **THEN** the system SHALL exit with a non-zero status and an error message including the returned status code

### Requirement: Strip structural boilerplate mechanically
The system SHALL remove structural boilerplate elements from the fetched HTML — navigation menus, footers, social-share icons, unsubscribe/legal blocks, and tracking pixels (e.g., 1x1 images) — using mechanical/structural rules only, without judging whether remaining content is promotional.

#### Scenario: Boilerplate removed
- **WHEN** the fetched HTML contains a footer with unsubscribe links and social icons
- **THEN** the extracted output SHALL NOT include text or images sourced from that footer region

### Requirement: Extract main article text
The system SHALL extract the main readable article text from the stripped HTML, preserving reading order and paragraph structure.

#### Scenario: Text extracted in reading order
- **WHEN** the HTML contains an article body with multiple paragraphs and headings
- **THEN** the extracted text SHALL preserve the original paragraph and heading order

### Requirement: Fail on empty extraction
The system SHALL treat an empty or near-empty extracted text result as an error rather than proceeding to send negligible content to an AI provider.

#### Scenario: Extraction yields no usable text
- **WHEN** the stripped HTML contains no substantive article text (e.g., a paywall or bot-blocked page)
- **THEN** the system SHALL exit with a non-zero status and an error message indicating no extractable content was found, without calling the AI provider

### Requirement: Extract candidate images with metadata
The system SHALL identify every image remaining within the extracted main-content region as a "candidate image" and record, for each, its alt text, immediate surrounding paragraph text, and reading-order position — without classifying it as an advertisement or a concept image at this stage.

#### Scenario: Candidate image recorded with metadata
- **WHEN** an image appears within the extracted article body with alt text and adjacent paragraph text
- **THEN** the system SHALL record that image as a candidate with its alt text, surrounding text, and position, deferring any ad-vs-concept judgment to the AI provider integration stage

### Requirement: Download candidate image bytes and assign stable IDs
The system SHALL download the binary content of every candidate image and assign each a stable placeholder identifier unique within the run, used to refer to the image in later stages.

#### Scenario: Candidate image downloaded and assigned an ID
- **WHEN** a candidate image is identified in the extracted content
- **THEN** the system SHALL download its bytes and assign it a placeholder ID (e.g., `IMAGE_1`) that is included alongside its metadata

#### Scenario: Image download failure does not abort the run
- **WHEN** a candidate image's bytes fail to download (e.g., broken link, timeout)
- **THEN** the system SHALL exclude that image from the candidate set, log a warning, and continue processing the remaining content
