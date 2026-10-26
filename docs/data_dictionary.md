# Data Dictionary

## `mart_verifications`

One row per identity-verification attempt, denormalized with the requesting user's organization and signup details so downstream queries never need a join.

| Column | Type | Description | Tests |
| --- | --- | --- | --- |
| verification_id | INTEGER | Unique identifier for the verification attempt. | not_null, unique |
| user_id | INTEGER | The user who attempted verification. | not_null |
| email_domain | TEXT | Domain portion of the user's email address. | not_null |
| organization | TEXT | The organization that requested the verification. | not_null |
| method | TEXT | Verification method used. | not_null, accepted_values:[document_scan,selfie_match,sms_otp,knowledge_based] |
| status | TEXT | Outcome of the verification attempt. | not_null, accepted_values:[verified,failed,pending] |
| created_at | TEXT | Date the verification attempt was made (ISO 8601). | not_null |
| signup_date | TEXT | Date the user originally signed up (ISO 8601). | not_null |
