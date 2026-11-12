# Out-of-sample check of the launch-data hazard (protocol fixed before the data are compiled)

Fixed values (Section VI-B, calibrated only on the FAA 1980–2002 history): λ_T = 0.90 BU⁻¹, c_f = 2 BU per flight, K = 0.15 for a developer that has never launched successfully, K = 0.57 for an experienced developer. Predicted loss probability per attempt, Eq. (18): p = 1 − exp[−λ_T (1 − K)² c_f], i.e. 0.73 (new) and 0.28 (experienced).

Universe: orbital launch attempts worldwide from 1 January 2003 to 31 December 2025 (launch date), from public launch records.

- Group N (new developers): every orbital launch attempt by an organization that, at the time of the attempt, had never placed a payload in orbit with a launch vehicle of its own, up to and including its first success. The organization is the vehicle developer (company or agency); a state agency that previously reached orbit with another vehicle is not new.
- Group E (experienced developers): the first orbital launch attempt of each new launch-vehicle family (new first stage, not a variant or upgrade of an existing vehicle) by a developer that had at least one successful orbital launch of its own vehicle before that attempt.
- Excluded: suborbital tests and flights not intended to reach orbit (e.g. Starship integrated flight tests), air-launch drop tests, flights of existing vehicles under a new operator, and vehicles whose developer cannot be identified from public sources.
- Outcome: failure if the payload did not reach a usable orbit (partial failures count as failures); a pad explosion before liftoff is not an attempt.

Test: observed loss share in each group against the fixed prediction, with exact binomial 90% intervals and the two-sided binomial p-value; the result is reported whatever it is. Ambiguous classifications are listed and the test is repeated with them moved to the other group or excluded (sensitivity).
