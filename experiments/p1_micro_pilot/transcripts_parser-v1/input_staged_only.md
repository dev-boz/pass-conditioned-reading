# P1 transcript — arm: **input_staged_only**

- doc: `govreport-00055` (8456 tokens) · K=6 · V=512
- model: Qwen2.5-7B-Instruct Q4_K_M via llama.cpp CPU · temp=0.0 · seed=42
- views: staged · demands: full_detail · config `e33c1f27858db9a5` · 2026-06-12

## Pass 1/6 — demand: `full_detail`

**View:** slice 8456 tok → view 483 tok (ratio 17.507×) · **gen wall-clock:** 80.3s · **usage:** 911+501 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 1 of 6

CURRENT INTEGRATION STATE:
(empty — no entries yet)

VIEW OF THE SOURCE (this pass):
The division and the 93 U.S. DOJ also has criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions. Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF. Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements. Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements. From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations. From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. The U.S. U.S. DOJ U.S. DOJ had not brought any criminal cases against financial institutions for violations of FCPA.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
ADD END: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
ADD END: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
ADD END: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
ADD END: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
ADD END: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
ADD END: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
ADD END: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.
ADD END: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
ADD END: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
ADD END: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
ADD END: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
ADD END: The U.S. DOJ had not brought any criminal cases against financial institutions for violations of FCPA.
```

### Parsed edit ops — 12/12 valid (validity 1.00), 12 applied

```json
[
 {
  "op": "ADD",
  "anchor": "END",
  "text": "The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including for the covered violations\u2014into Treasury\u2019s General Fund accounts."
 },
 {
  "op": "ADD",
  "anchor": "END",
  "text": "The U.S. DOJ had not brought any criminal cases against financial institutions for violations of FCPA."
 }
]
```

### State after pass (459 tok)

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
S12: The U.S. DOJ had not brought any criminal cases against financial institutions for violations of FCPA.
```

## Pass 2/6 — demand: `full_detail`

**View:** slice 4823 tok → view 487 tok (ratio 9.903×) · **gen wall-clock:** 117.0s · **usage:** 1417+383 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 2 of 6

CURRENT INTEGRATION STATE:
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
S12: The U.S. DOJ had not brought any criminal cases against financial institutions for violations of FCPA.

VIEW OF THE SOURCE (this pass):
Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF. Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements. Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements. From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig. From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations. From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
REPLACE S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
ADD S3: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations.
ADD S4: OFAC has collected about $299 million out of the $301 million it assessed.
REPLACE S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
REPLACE S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
REPLACE S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
REPLACE S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
REPLACE S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
```

### Parsed edit ops — 8/8 valid (validity 1.00), 8 applied

```json
[
 {
  "op": "REPLACE",
  "id": "S2",
  "text": "Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements."
 },
 {
  "op": "ADD",
  "anchor": "S3",
  "text": "As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations."
 },
 {
  "op": "ADD",
  "anchor": "S4",
  "text": "OFAC has collected about $299 million out of the $301 million it assessed."
 },
 {
  "op": "REPLACE",
  "id": "S7",
  "text": "From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million."
 },
 {
  "op": "REPLACE",
  "id": "S9",
  "text": "From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations."
 },
 {
  "op": "REPLACE",
  "id": "S10",
  "text": "From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts."
 },
 {
  "op": "REPLACE",
  "id": "S11",
  "text": "FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including for the covered violations\u2014into Treasury\u2019s General Fund accounts."
 },
 {
  "op": "REPLACE",
  "id": "S12",
  "text": "Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF."
 }
]
```

### State after pass (583 tok)

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations.
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S14: OFAC has collected about $299 million out of the $301 million it assessed.
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
```

## Pass 3/6 — demand: `full_detail`

**View:** slice 2717 tok → view 493 tok (ratio 5.511×) · **gen wall-clock:** 173.3s · **usage:** 1522+700 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 3 of 6

CURRENT INTEGRATION STATE:
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations.
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S14: OFAC has collected about $299 million out of the $301 million it assessed.
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.

VIEW OF THE SOURCE (this pass):
The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
ADD END: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.

REPLACE S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)

REPLACE S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)

REPLACE S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
```

### Parsed edit ops — 4/4 valid (validity 1.00), 4 applied

```json
[
 {
  "op": "ADD",
  "anchor": "END",
  "text": "The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including for the covered violations\u2014into Treasury\u2019s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury\u2019s General Fund. Once Treasury\u2019s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ\u2019s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury\u2019s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S."
 },
 {
  "op": "REPLACE",
  "id": "S13",
  "text": "As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)"
 },
 {
  "op": "REPLACE",
  "id": "S14",
  "text": "OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury\u2019s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)"
 },
 {
  "op": "REPLACE",
  "id": "S11",
  "text": "FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including"
 }
]
```

### State after pass (1144 tok)

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.
```

## Pass 4/6 — demand: `full_detail`

**View:** slice 1583 tok → view 490 tok (ratio 3.231×) · **gen wall-clock:** 208.6s · **usage:** 2142+700 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 4 of 6

CURRENT INTEGRATION STATE:
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.

VIEW OF THE SOURCE (this pass):
From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations.The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
REPLACE S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.

ADD S16: As of December 2015, $1.2 million had not been collected in the cases we reviewed.
ADD S17: DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million.
ADD S18: From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations.
ADD S19: SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million
```

### Parsed edit ops — 1/5 valid (validity 0.20), 1 applied

```json
[
 {
  "op": "REPLACE",
  "id": "S4",
  "text": "From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC\u2019s penalties ranged from $25,000 to $10 million\u2014which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ\u2019s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig."
 }
]
```

**Invalid op lines:**

```text
ADD S16: As of December 2015, $1.2 million had not been collected in the cases we reviewed.
ADD S17: DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million.
ADD S18: From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCP
ADD S19: SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million
```

### State after pass (1572 tok)

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.
```

## Pass 5/6 — demand: `full_detail`

**View:** slice 896 tok → view 498 tok (ratio 1.799×) · **gen wall-clock:** 194.3s · **usage:** 2584+512 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 5 of 6

CURRENT INTEGRATION STATE:
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.

VIEW OF THE SOURCE (this pass):
To respond to our first objective, we identified and analyzed these agencies’ data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury’s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC’s website, we applied Treasury’s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ’s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC’s website (see table 3 for a list of these cases). We obtained data from DOJ’s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ’s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
ADD END: To respond to our first objective, we identified and analyzed these agencies’ data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury’s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC’s website, we applied Treasury’s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ’s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC’s website (see table 3 for a list of these cases). We obtained data from DOJ’s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ’s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ.
```

### Parsed edit ops — 1/1 valid (validity 1.00), 1 applied

```json
[
 {
  "op": "ADD",
  "anchor": "END",
  "text": "To respond to our first objective, we identified and analyzed these agencies\u2019 data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury\u2019s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC\u2019s website, we applied Treasury\u2019s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ\u2019s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC\u2019s website (see table 3 for a list of these cases). We obtained data from DOJ\u2019s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ\u2019s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ."
 }
]
```

### State after pass (2073 tok [over state budget])

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.
S16: To respond to our first objective, we identified and analyzed these agencies’ data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury’s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC’s website, we applied Treasury’s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ’s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC’s website (see table 3 for a list of these cases). We obtained data from DOJ’s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ’s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ.
```

## Pass 6/6 — demand: `full_detail`

**View:** slice 509 tok → view 509 tok (ratio 1.0×) · **gen wall-clock:** 265.3s · **usage:** 3119+700 tok

<details><summary>Prompt (user message)</summary>

```text
TASK: Produce a comprehensive analytical brief of this report: its scope, the problems it identifies, its key findings with supporting figures, and its recommendations.

SCHEDULE POSITION: pass 6 of 6

CURRENT INTEGRATION STATE:
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under the Justice Asset Forfeiture Program, a DOJ investigative agency seizes an asset (funds in the cases we reviewed), and the asset is entered into DOJ’s Consolidated Asset Tracking System. The asset is then transferred to the U.S. The U.S. Once the forfeiture is finalized, the seizing agency or the U.S. U.S. Similarly, the asset forfeiture process for the Treasury Forfeiture Program involves a Department of Homeland Security or Treasury investigative agency seizing the asset (funds, in the cases we reviewed). Once forfeiture is final, the seizing agency subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF. DOJ U.S.
S16: To respond to our first objective, we identified and analyzed these agencies’ data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury’s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC’s website, we applied Treasury’s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ’s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC’s website (see table 3 for a list of these cases). We obtained data from DOJ’s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ’s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ.

VIEW OF THE SOURCE (this pass):
Of the $301 million, OFAC has collected about $299 million (see fig. 3). OFAC’s enforcement guidelines provide the legal framework for analyzing apparent violations. Some of the factors which determine the size of a civil money penalty include the sanctions program at issue and the number of apparent violations and their value. For example, OFAC assessed Clearstream Banking a $152 million penalty because it made securities transfers for the central bank of a sanctioned country. DOJ, along with participating Treasury offices and other law enforcement partners, assessed and enforced criminal and civil forfeitures and fines totaling about $5.7 billion for the federal government for sanctions programs violations. This amount was the result of eight forfeitures that also included two fines. Of the $5.7 billion collected for sanctions programs violations, most of this amount was collected from one financial institution—BNP Paribas. In total, BNP Paribas was assessed an $8.8 billion forfeiture and a $140 million criminal fine in 2014 for willfully conspiring to commit violations of various sanctions laws and regulations. BNP Paribas pleaded guilty to moving more than $8.8 billion through the U.S. financial system on behalf of sanctioned entities from 2004 to 2012. Of the $8.8 billion forfeited, $3.8 billion was collected by Treasury’s Executive Office for Asset Forfeiture, with the remainder apportioned among participating state and local agencies. In addition to BNP Paribas, DOJ and OFAC assessed fines and forfeitures against other financial institutions for similar violations, including processing transactions in violation of the International Emergency Economic Powers Act, OFAC regulations, and the Trading with the Enemy Act. From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations. The Federal Reserve assessed its largest penalty for $508 million against BNP Paribas for having unsafe and unsound practices that failed to prevent the concealing of payment information of financial institutions subject to OFAC regulations. It was assessed as part of a global settlement with DOJ for concealing payment information of a financial institution subject to OFAC regulations. Federal Reserve officials stated that the remaining assessed penalties related to OFAC regulations were largely for similar unsafe and unsound practices. FinCEN and financial regulators have processes in place for receiving penalty payments from financial institutions—including for penalties assessed for the covered violations—and for depositing these payments.

OUTPUT DEMAND FOR THIS PASS:
Produce the most complete, detailed integration of this view's content into the state that you can: full substantive coverage including exact figures, dates, names, and references where the view provides them. Full detail is expected at every pass of this schedule. Use any operations needed. Keep the state within about 1800 tokens.

Respond with edit operations only.

```
</details>

### Raw model output

```text
ADD END: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
REPLACE S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
REPLACE S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
REPLACE S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
REPLACE S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
REPLACE S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
REPLACE S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under
```

### Parsed edit ops — 7/7 valid (validity 1.00), 7 applied

```json
[
 {
  "op": "ADD",
  "anchor": "END",
  "text": "OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury\u2019s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)"
 },
 {
  "op": "REPLACE",
  "id": "S14",
  "text": "OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury\u2019s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)"
 },
 {
  "op": "REPLACE",
  "id": "S9",
  "text": "From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations."
 },
 {
  "op": "REPLACE",
  "id": "S10",
  "text": "From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts."
 },
 {
  "op": "REPLACE",
  "id": "S11",
  "text": "FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including for the covered violations\u2014into Treasury\u2019s General Fund accounts."
 },
 {
  "op": "REPLACE",
  "id": "S12",
  "text": "Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF."
 },
 {
  "op": "REPLACE",
  "id": "S15",
  "text": "The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions\u2014including for the covered violations\u2014into Treasury\u2019s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury\u2019s General Fund. Once Treasury\u2019s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under"
 }
]
```

### State after pass (2020 tok [over state budget])

```text
S1: The division and the U.S. DOJ also have criminal enforcement authority. Treasury, DOJ, and federal banking regulators all have roles in implementing U.S. sanctions programs requirements relevant to financial institutions.
S2: Since 2009, financial institutions have been assessed about $12 billion in fines, penalties, and forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions program requirements.
S3: Specifically, from January 2009 through December 2015, federal agencies assessed about $5.2 billion for BSA violations, $27 million for FCPA violations, and about $6.8 billion for violations of U.S. sanctions program requirements.
S13: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. (SEC had deposited all of them into a Treasury General Fund receipt account)
S4: From January 2009 to December 2015, DOJ, FinCEN, and federal financial regulators (the Federal Reserve, FDIC, OCC, and SEC), assessed about $5.2 billion and collected about $5.1 billion in penalties, fines, and forfeitures for various BSA violations. Financial regulators assessed a total of about $1.4 billion in penalties for BSA violations for which they were responsible for collecting, and collected almost all of this amount (see fig. Of the $1.4 billion, one penalty (assessed by OCC) accounted for almost 35 percent ($500 million). Financial regulators assess penalties for BSA violations both independently and concurrently with FinCEN. Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions. SEC’s penalties ranged from $25,000 to $10 million—which included a $4.2 million disgorgement. As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed. In addition, FinCEN assessed about $108 million in penalties that it was responsible for collecting. Based on our analysis, almost all of the $108 million was assessed in 2015 of which $9.5 million has been collected as of December 2015. Almost all of this amount resulted from forfeitures, while about $1 million was from fines. As of December 2015, $1.2 million had not been collected in the cases we reviewed. DOJ’s forfeitures ranged from about $240,000 to $1.7 billion, and six of the forfeitures were at least $100 million. From January 2009 through December 2015, SEC collected approximately $27 million in penalties and disgorgements from two financial institutions for FCPA violations. SEC assessed $10.3 million in penalties, $13.6 million in disgorgements, and $3.3 million in interest combined for the FCPA violations. From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million. Of the $301 million, OFAC has collected about $299 million (see fig.
S14: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
S5: Out of the $1.4 billion assessed, $651 million was assessed concurrently with FinCEN to 13 different financial institutions.
S6: As of December 2015, SEC had collected about $9.4 million of the $16 million it has assessed.
S7: From January 2009 through December 2015, OFAC independently assessed $301 million in penalties against financial institutions for sanctions programs violations. The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S8: The $301 million OFAC assessed was comprised of 47 penalties, with penalty amounts ranging from about $8,700 to $152 million.
S9: From January 2009 through December 2015, the Federal Reserve independently assessed and collected about $837 million in penalties from six financial institutions for U.S. sanctions programs violations.
S10: From January 2009 through December 2015, about $2.7 billion was collected from financial institutions for the covered violations and deposited into Treasury General Fund accounts.
S11: FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts.
S12: Treasury and DOJ maintain funds and accounts for fines, penalties, and forfeitures that are collected. Treasury administers and maintains the Treasury General Fund and TFF.
S15: The remaining funds from these cases are subject to general rescissions to the AFF and TFF or may be used for program or other law enforcement expenses. FinCEN and financial regulators deposit collections of penalties assessed against financial institutions—including for the covered violations—into Treasury’s General Fund accounts. (see fig. FinCEN deposits the penalty payments it receives in accounts in Treasury’s General Fund. Once Treasury’s BFS receives payments for FinCEN- and OFAC-assessed penalties, BFS staff deposits the payments into the appropriate Treasury General Fund accounts. For collections we reviewed from January 2009 to December 2015 for BSA and FCPA violations, SEC had deposited all of them into a Treasury General Fund receipt account. When the Office of Financial Management receives a payment for a penalty from a financial institution, it compares the amount with these notifications. Federal Reserve officials explained that when they send the penalty to Treasury, they typically e-mail Treasury officials to verify that they have received the payment. According to officials, to keep track of what is collected and sent to the Treasury General Fund, FRBR retains statements that document both the collection and transfer of the penalty to a Treasury General Fund receipt account. Once a quarter, FDIC sends penalty payments it receives to a Treasury General Fund receipt account. Treasury Office of Management officials explained that the Treasury General Fund has a general receipt account that receives all of the penalties that regulators and Treasury agencies collect for BSA, FCPA, and sanctions violations. Figure 5 shows the processes that govern the seizure and forfeiture of assets for the Justice Asset Forfeiture Program and the Treasury Forfeiture Program. The Justice Asset Forfeiture Program and the Treasury Forfeiture Program follow similar forfeiture processes. Under
S16: To respond to our first objective, we identified and analyzed these agencies’ data on enforcement actions taken against financial institutions that resulted in fines, penalties, or forfeitures for violations of BSA/AML, FCPA, and U.S. sanctions programs requirements. Specifically, we analyzed publicly available data from January 2009 through December 2015 on penalties assessed against financial institutions by the Federal Reserve, FDIC, OCC, SEC, and the Financial Crimes Enforcement Network (FinCEN), a bureau within Treasury, for violations of BSA/AML requirements. NCUA officials we spoke with explained that they had not assessed any penalties against financial institutions for violations of BSA/AML requirements from January 2009 through December 2015. FDIC and SEC provided us with a list of enforcement actions they took for BSA/AML violations since 2009, as we were not able to identify all of their actions through their publicly available data. We also reviewed Federal Reserve data on penalties for violations of U.S. sanctions programs requirements and data that SEC provided on FCPA violations. In addition, we reviewed enforcement actions listed on Treasury’s Office of Foreign Assets Control (OFAC) website to identify penalties assessed against financial institutions for violations of U.S. sanctions programs requirements enforced by OFAC. To identify enforcement actions taken against financial institutions from the actions listed on OFAC’s website, we applied Treasury’s definition of financial institutions, which covers regulated entities in the financial industry. To identify criminal cases against financial institutions for violations of BSA and sanctions-related requirements, we reviewed press releases from DOJ’s Asset Forfeiture and Money Laundering Section, associated court documents, and enforcement actions taken against financial institutions from the actions listed on OFAC’s website (see table 3 for a list of these cases). We obtained data from DOJ’s Consolidated Asset Tracking System to determine the amounts forfeited for these cases, and verified any Treasury-related data in DOJ’s system by obtaining information from the Treasury Executive Office for Asset Forfeiture. DOJ had not brought any criminal cases against financial institutions for violations of FCPA. We assessed the reliability of the data we used in this report by reviewing prior GAO assessments of these data, interviewing knowledgeable agency officials, and reviewing relevant documentation, such as agency enforcement orders for the assessments. We also assessed the reliability of the DOJ data fields we reported on by reviewing prior GAO and DOJ evaluations of these data and interviewing knowledgeable officials from DOJ.
S17: OFAC has collected about $299 million out of the $301 million it assessed. (OFAC has collected about $299 million out of the $301 million it assessed, and once the forfeiture is finalized, the seizing agency or the U.S. subsequently requests that Treasury’s Executive Office for Asset Forfeiture staff transfer the asset from the Treasury Suspense Account to the TFF)
```
