# Differences between the AI and ML models for 20 APIs

The below table outlines the violations that were reported by the AI model. In the current analysis of 20 API specs, the AI model found a total of 11 violations for the rule "Plural noun", whereas the ML model reported 8 violations.

| API | Path | Result |
|-----|------|----------------|
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/batch | Arguably correct, although a hard one to decide due to the word "data". |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/chart | Arguably correct, although a hard one to decide due to the word "data". |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/first | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/last | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/previous | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/feeds/{feed_key}/data/retain | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/groups/{group_key}/add | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/groups/{group_key}/data | This shouldn't have been reported, "data" could have treated as singular here |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/groups/{group_key}/remove | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/{type}/{type_id}/acl | Correct |
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/{type}/{type_id}/acl/{id} | Correct |

The below table summarizes the potential false positives identified by the AI model.
| API | Path | Result |
|-----|------|----------------|
| https://api.apis.guru/v2/specs/adafruit.com/2.0.0/swagger.json | /{username}/groups/{group_key}/data | This shouldn't have been reported, "data" could have treated as singular here |

From the results above, we can say that in 11 reported violations, the AI model had only 1 false-positive. This puts the precision at 90.9 %.