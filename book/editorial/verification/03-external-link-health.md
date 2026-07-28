# External link health

Date: 2026-07-28

This pass audits the external HTTP(S) links written directly into the manuscript. It is a dated network observation, not part of the byte-reproducible build: remote availability, redirects, bot defenses, and rate limits can change independently of this repository.

## Method and policy

`verify-external-links.py` extracts unique HTTP(S) URLs from the 252 manuscript records and checks them with bounded concurrency, redirects enabled, a 30-second timeout, and a descriptive user agent. It is intentionally separate from `verify-book.py` so a clean local build does not depend on live third-party services.

The checker uses these dispositions:

- `200–399`: healthy, with the final redirect destination retained in the JSON report;
- `404` or `410`: hard failure and a nonzero exit;
- malformed URL: hard failure and a nonzero exit;
- access controls and rate limits (`401`, `403`, `405`, `406`, `418`, `425`, `429`, `451`): restricted and requiring review, but not evidence that the cited resource is dead;
- other client errors, server errors, and transport errors: reported for review, but not silently converted into dead-link verdicts.

A future hard failure must be repaired or given an explicit, dated exception that records why the source remains necessary and what stable archive or recovery route was checked. No exceptions are required at this baseline.

## Result

Command:

```text
python3 verify-external-links.py --timeout 30 --workers 6
```

The audit found:

- **45 unique URLs across 38 domains**;
- **39 healthy responses**;
- **6 restricted responses**;
- **0 other client errors**;
- **0 server errors**;
- **0 transport errors**;
- **0 hard failures**;
- **0 malformed URLs**.

The six restricted results all returned `403`:

- `https://doi.org/10.1002/acp.70021`
- `https://philarchive.org/rec/LERTAF`
- `https://www.armed-services.senate.gov/imo/media/doc/full_transcript-04-28-2026.pdf`
- `https://www.esd.whs.mil/Portals/54/Documents/FOID/Reading%20Room/DARPA/22-FRO-0457_SARS-COV-2_Orgins_Investigation_w_US_Govt_Prog_Undisclosed_Doc_Analysis_2021.pdf`
- `https://www.oecd.org/en/publications/society-at-a-glance-2024_918d8db3-en/full-report/fertility_748a5055.html`
- `https://www.unhcr.org/about-unhcr/overview/1951-refugee-convention`

These are access-policy results, not dead-link findings. The DOI redirect reaches its Wiley destination before access is denied; the other five remain at the cited route.

One soft redirect required manual review: the ODNI press-release URL currently lands on the ODNI newsroom rather than preserving a dedicated response body. The exact official URL remains indexed as the cited press release, and the accompanying ODNI document index resolves to the agency archive. The citation is therefore retained, with the redirect recorded as a future recheck item rather than treated as a clean content-preserving redirect.

An initial shorter run produced one transient timeout; the 30-second bounded run resolved it successfully. No manuscript URL changed in this pass.

## Disposition

External-link verification now has a repeatable, opt-in checker and a passing dated baseline. It establishes reachability and records redirect/access behavior; it does not establish that an external source proves the manuscript's interpretation of it.
