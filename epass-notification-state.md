# Telangana ePASS Notification State

Last updated: 2026-07-29 00:27:56 IST

This file documents how we compute the "Amount Deposited" value extracted from ePASS notification pages.

Rule (updated)

- Amount Deposited must be taken only from columns that have a bank remitted date. If multiple columns have a bank remitted date, sum the corresponding amount values and use that sum. If none of the columns has a bank remitted date, set Amount Deposited to NULL.

SQL examples

1) If you have two pairs (remitted_date_1, amount_1) and (remitted_date_2, amount_2):

```sql
CASE
  WHEN remitted_date_1 IS NULL AND remitted_date_2 IS NULL THEN NULL
  ELSE
    COALESCE(CASE WHEN remitted_date_1 IS NOT NULL THEN COALESCE(amount_1, 0) ELSE 0 END, 0)
    + COALESCE(CASE WHEN remitted_date_2 IS NOT NULL THEN COALESCE(amount_2, 0) ELSE 0 END, 0)
END AS amount_deposited
```

2) Generic approach for N pairs (pseudocode / SQL construction):

```sql
-- Replace remitted_date_i and amount_i with your actual column names
CASE
  WHEN (
    remitted_date_1 IS NULL
    AND remitted_date_2 IS NULL
    -- AND remitted_date_3 IS NULL ... for all i=1..N
  ) THEN NULL
  ELSE (
    CASE WHEN remitted_date_1 IS NOT NULL THEN COALESCE(amount_1, 0) ELSE 0 END
    + CASE WHEN remitted_date_2 IS NOT NULL THEN COALESCE(amount_2, 0) ELSE 0 END
    -- + CASE WHEN remitted_date_3 IS NOT NULL THEN COALESCE(amount_3, 0) ELSE 0 END
    -- ... for all i=1..N
  )
END AS amount_deposited
```

Notes

- Use COALESCE to handle NULL amount cells so that NULL amounts are treated as 0 when summing.
- The CASE wrap ensures you get NULL only when no remitted date exists; if remitted dates exist but the amounts sum to 0, the result will be 0 (not NULL).

Existing example state (unchanged):

```json
{
  "202111856079|2021-22": {
    "bank_remitted_date_present": true,
    "explicit_103000_shown": true,
    "last_observed_total_or_summed_sanctioned_amount": 103000.0,
    "amount_deposited_from_govt_to_college": 103000.0,
    "last_successful_check": "2026-07-29T00:27:10.187093+05:30",
    "reported_conditions": [
      "103000_released",
      "above_35000"
    ]
  },
  "202211856079|2022-23": {
    "bank_remitted_date_present": false,
    "explicit_103000_shown": false,
    "last_observed_total_or_summed_sanctioned_amount": 35000.0,
    "amount_deposited_from_govt_to_college": null,
    "last_successful_check": "2026-07-29T00:27:31.424765+05:30",
    "reported_conditions": []
  },
  "202311856079|2023-24": {
    "bank_remitted_date_present": true,
    "explicit_103000_shown": false,
    "last_observed_total_or_summed_sanctioned_amount": 35000.0,
    "amount_deposited_from_govt_to_college": 35000.0,
    "last_successful_check": "2026-07-29T00:27:44.027605+05:30",
    "reported_conditions": []
  },
  "202411856079|2024-25": {
    "bank_remitted_date_present": false,
    "explicit_103000_shown": false,
    "last_observed_total_or_summed_sanctioned_amount": 35000.0,
    "amount_deposited_from_govt_to_college": null,
    "last_successful_check": "2026-07-29T00:27:56.146601+05:30",
    "reported_conditions": []
  }
}
```
