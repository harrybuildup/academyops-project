# Requirements Document

## Introduction

WP-08 adds stateless lead intent classification and reply automation to the AcademyOps API.
When a staff member or automated system receives a free-text message from a lead, they POST
that message to a new endpoint. The system classifies the message into one of five intent
categories, recommends the next pipeline stage, and returns a templated reply — all without
touching the database or requiring any new table.

This work package extends the existing FastAPI + PostgreSQL + SQLAlchemy stack and integrates
cleanly with the lead pipeline stages (`New → Contacted → Qualified → Demo → Enrolled / Lost`)
already defined in `LeadStage`.

---

## Glossary

- **Classifier**: The component responsible for mapping an inbound message text to an intent label.
- **Intent**: A discrete category that describes the purpose or sentiment of a lead's message. Valid values: `fees`, `timing`, `eligibility`, `not-interested`, `other`.
- **Intent_Response**: The Pydantic response schema containing `intent`, `suggested_stage`, and `reply` fields.
- **Message_Endpoint**: The new API endpoint `POST /api/v1/leads/{id}/message`.
- **Reply_Template**: A pre-defined text template selected by the Classifier to respond to a specific intent.
- **Suggested_Stage**: The `LeadStage` value the Classifier recommends transitioning the lead to, based on detected intent.
- **Evaluation_Set**: A labelled dataset of (message, expected_intent) pairs used to measure Classifier accuracy.
- **Accuracy_Script**: A runnable Python script or pytest module that measures Classifier accuracy against the Evaluation_Set.

---

## Requirements

### Requirement 1: Accept an Inbound Message for a Lead

**User Story:** As a sales team member, I want to submit a lead's inbound message via the API, so that the system can analyse it and guide my next action.

#### Acceptance Criteria

1. WHEN a `POST /api/v1/leads/{id}/message` request is received with a valid JSON body containing a non-empty `message` field, THE Message_Endpoint SHALL return HTTP 200 with an `Intent_Response` body.
2. WHEN a `POST /api/v1/leads/{id}/message` request is received and the `id` path parameter does not correspond to an existing lead, THE Message_Endpoint SHALL return HTTP 404 with a JSON body containing an `"error"` key.
3. WHEN a `POST /api/v1/leads/{id}/message` request is received with a missing `message` field or an empty string value for `message`, THE Message_Endpoint SHALL return HTTP 400 with a JSON body containing an `"error"` key.
4. THE Message_Endpoint SHALL NOT modify any database record or create any new database rows when processing a message request.

---

### Requirement 2: Classify Message Intent

**User Story:** As a sales team member, I want every inbound message automatically classified into a known intent category, so that I can understand what the lead is asking without reading every message manually.

#### Acceptance Criteria

1. WHEN the Classifier receives a message text, THE Classifier SHALL return exactly one intent label drawn from the set `{"fees", "timing", "eligibility", "not-interested", "other"}`.
2. THE Classifier SHALL assign the `fees` intent WHEN the message text refers to cost, price, payment, or financial terms.
3. THE Classifier SHALL assign the `timing` intent WHEN the message text refers to schedule, dates, start times, course duration, or availability.
4. THE Classifier SHALL assign the `eligibility` intent WHEN the message text refers to prerequisites, qualifications, entry requirements, or suitability for a course.
5. THE Classifier SHALL assign the `not-interested` intent WHEN the message text expresses disinterest, withdrawal, cancellation, or a request to stop contact.
6. THE Classifier SHALL assign the `other` intent WHEN the message text does not clearly match any of the `fees`, `timing`, `eligibility`, or `not-interested` categories.
7. THE Classifier SHALL return a result for every non-empty message string without raising an unhandled exception.

---

### Requirement 3: Suggest Next Pipeline Stage and Templated Reply

**User Story:** As a sales team member, I want the system to recommend what stage to move the lead to and provide a ready-to-send reply, so that I can respond quickly and consistently.

#### Acceptance Criteria

1. WHEN the Classifier returns an intent, THE Classifier SHALL also return a `suggested_stage` value that is a valid `LeadStage` member (`New`, `Contacted`, `Qualified`, `Demo`, `Enrolled`, or `Lost`).
2. WHEN the detected intent is `fees`, THE Classifier SHALL suggest the `Qualified` stage and return the fees Reply_Template.
3. WHEN the detected intent is `timing`, THE Classifier SHALL suggest the `Qualified` stage and return the timing Reply_Template.
4. WHEN the detected intent is `eligibility`, THE Classifier SHALL suggest the `Qualified` stage and return the eligibility Reply_Template.
5. WHEN the detected intent is `not-interested`, THE Classifier SHALL suggest the `Lost` stage and return the not-interested Reply_Template.
6. WHEN the detected intent is `other`, THE Classifier SHALL suggest the `Contacted` stage and return the other Reply_Template.
7. THE Classifier SHALL return a non-empty string for the `reply` field for every valid intent label.

---

### Requirement 4: Validate Request and Return Structured Errors

**User Story:** As an API consumer, I want clear error responses when I send malformed requests, so that I can diagnose integration problems quickly.

#### Acceptance Criteria

1. WHEN the `id` path parameter in `POST /api/v1/leads/{id}/message` does not correspond to a lead in the database, THE Message_Endpoint SHALL return HTTP 404 and a JSON error body consistent with the existing `LeadNotFoundError` handler pattern used by the application.
2. WHEN the request body is absent or the `message` field is absent, THE Message_Endpoint SHALL return HTTP 400 with a JSON body containing an `"error"` key describing the validation failure.
3. WHEN the `message` field is present but contains only whitespace characters, THE Message_Endpoint SHALL return HTTP 400 with a JSON body containing an `"error"` key.
4. THE Message_Endpoint SHALL return HTTP 404 before performing intent classification WHEN the lead does not exist, so that no classification work is performed for non-existent leads.

---

### Requirement 5: Measure Classifier Accuracy Against a Labelled Evaluation Set

**User Story:** As a technical lead, I want an accuracy measurement script that runs against a labelled evaluation set, so that I can verify the Classifier meets quality expectations and detect regressions.

#### Acceptance Criteria

1. THE Accuracy_Script SHALL execute without requiring network access, a running database, or any external service.
2. WHEN the Accuracy_Script is executed, THE Accuracy_Script SHALL compare each message in the Evaluation_Set against the Classifier output and compute the percentage of correct intent predictions.
3. THE Accuracy_Script SHALL print or log the overall accuracy percentage and, for each incorrect prediction, the message text, the expected intent, and the actual intent returned by the Classifier.
4. THE Accuracy_Script SHALL exit with a non-zero status code WHEN the measured accuracy falls below 80%.
5. THE Evaluation_Set SHALL contain a minimum of 25 labelled examples distributed across all five intent categories (`fees`, `timing`, `eligibility`, `not-interested`, `other`).
