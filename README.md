# hng-stage-2
HNG backend internship stage 2. An improvement of the stage 1 task

# Intelligence Query Engine

## Overview

This project is a backend **Intelligence Query Engine** built for a demographic profile dataset. It exposes REST APIs that allow clients to retrieve and analyze user profiles using structured filters and natural language queries.

The system is designed for **highly controlled, deterministic query processing**, where every request is transformed into validated database filters before execution.

It supports three main capabilities:

- **Advanced querying of profiles** using multiple combinable filters (gender, age, country, probability thresholds)
- **Natural language search**, where plain English queries are parsed into structured constraints
- **Controlled data access patterns** through pagination and sorting to ensure performance and scalability

The architecture prioritizes:
- predictable query behavior
- strict validation rules
- efficient database execution
- zero ambiguity in interpretation

All query processing is rule-based, ensuring consistent outputs for identical inputs without reliance on AI or probabilistic models.

---

## 1. API Endpoints

### Get All Profiles

GET /api/profiles

Supports filtering, sorting, and pagination.

#### Query Parameters
- gender (male | female)
- age_group (child | teenager | adult | senior)
- country_id (ISO 2-letter code)
- min_age (int)
- max_age (int)
- min_gender_probability (float)
- min_country_probability (float)

#### Sorting
- sort_by = age | created_at | gender_probability
- order = asc | desc

#### Pagination
- page (default: 1)
- limit (default: 10, max: 50)

#### Example Request

GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10

---

### Natural Language Search

GET /api/profiles/search

#### Query Parameter
- q = natural language query

#### Example Requests

GET /api/profiles/search?q=young males from nigeria

GET /api/profiles/search?q=adult females above 30 from kenya

GET /api/profiles/search?q=teenagers below 18 from nigeria

#### Parsing Examples

| Input query | Parsed filters |
|------------|----------------|
| young males from nigeria | gender=male, age=16–24, country=nigeria |
| females above 30 | gender=female, min_age=30 |
| adult males from kenya | gender=male, age_group=adult, country=kenya |

---

## 2. Natural Language Parsing Approach

### How parsing works

The parser follows a strict rule-based pipeline:

#### Step 1: Phrase matching (highest priority)
- "from <country>" → country filter
- "above X" → min_age
- "below X" → max_age

#### Step 2: Token matching

**Gender**
- male / males → gender = male
- female / females → gender = female

**Age groups**
- child / teenager / adult / senior → age_group

**Special keyword**
- young → age range 16–24

#### Step 3: Noise removal
Ignored words:
- and
- people

#### Step 4: Strict validation rule

If any unrecognized words remain:

{ "status": "error", "message": "Unable to interpret query" }

---

### Mapping Summary

| Input keyword | Output filter |
|--------------|--------------|
| male/males | gender=male |
| female/females | gender=female |
| teenager(s) | age_group=teenager |
| young | min_age=16, max_age=24 |
| above X | min_age=X |
| below X | max_age=X |
| from nigeria | country_raw=nigeria (validated via DB) |

---

### Country resolution

- "from <country>" is parsed as raw country name
- Validation resolves it using Profile.country_name
- If not found → query is rejected

---

## 3. Limitations

This system is intentionally strict and does not support:

- fuzzy matching or typo correction
- synonyms beyond defined keywords
- natural language variations outside rules
- OR / NOT logic (only AND-based filtering)
- nested or complex grammar
- partial or inferred intent
- ambiguous queries

---

## Known edge cases

- Conflicting filters (e.g. "young above 40") may be rejected
- Only "from <country>" format is supported for country parsing
- Unknown tokens cause full query rejection
- Country matching depends on exact dataset values

---

## Summary

The system is deterministic and rule-based:

- parse → extract structured filters
- validate → enforce correctness via DB and rules
- execute → apply Django ORM filters and pagination
