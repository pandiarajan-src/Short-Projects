# Instructor notes - traps planted in the sample files

Keep this file to yourself; it is not inside the zip.

## 1. TidyBot
- `report.pdf` clashes with an existing `Documents/report.pdf` -> must get a numeric suffix, not overwrite.
- `download (1)` has no extension but is really a PDF (starts with `%PDF`) -> agent should peek.
- `notes` and `README` have no extension; `untitled.txt` is a recipe.
- `desktop.ini` is a Windows system file -> best left alone.
- Set 2: `photo.JPG` clashes with an existing `Images/photo.JPG`; uppercase extensions (`.PDF`, `.JPG`, `.TXT`);
  a non-ASCII name (`Résumé - Tamil Selvi.pdf`); a double extension (`archive.tar.gz`); an Office lock file (`~$draft.docx`, really text).

## 2. SpendSense
- Ambiguous rows: `UPI/RAJESH K/...`, `POS 4532 STORE 112`, `NEFT TRANSFER REF ...`, `ATM WITHDRAWAL` -> should go to Other with a reason.
- Credits: salary and `REFUND AMAZON PAY INDIA` are positive. A good report does not count refunds as spending.
- Rent (Rs 15,000) is the single largest debit each month.

## 3. MinuteMan
Standup - expected action items (6):
1. Karthik - check staging server logs, update channel - by noon today (26 Oct)
2. Meena - finish edit-profile form - by Wednesday
3. Meena - re-export app icon at higher resolutions - by Friday
4. Divya - run full regression on test build, share report - tomorrow
5. Priya - prepare demo slide deck - before Thursday demo
6. Arun - send two login-screen screenshots - Wednesday evening
Must NOT appear: analytics library upgrade ("maybe someone should..."), dark-mode colours (parked).

Planning meeting - expected action items (6):
1. Sneha - final hi-fi mockups - Tue 3 Nov
2. Anitha - pricing page in staging - Fri 6 Nov
3. Vikram - contact-form email endpoint - Wed 4 Nov
4. Anitha (NOT Vikram - reassigned) - create three test accounts for Joseph - today (29 Oct)
5. Joseph - test plan for pricing page + contact form - Mon 2 Nov
6. Rahul - send sprint summary to leadership - tomorrow morning
Must NOT appear: blog migration (dropped), font licence check (no owner), currency switcher (out of scope).

## 4. SnapNamer
- `notes.txt`, `desktop.ini`, `readme.md`, `Thumbs.db` are not images -> skip.
- Set 2: two near-identical pie charts (September vs October) -> names must stay unique and mention the month.
- `IMG_3003.jpg` is a blurry abstract image -> a good agent picks a modest name like `blurry-abstract-colours.jpg` rather than inventing a subject.
- Uppercase `.PNG` extension must be preserved.

## 5. DigestBot
- No fixed answers; check links work, no duplicate stories, summaries paraphrased, cost printed.

## 6. StudyCards
- Photosynthesis notes: section 7 "Recap" repeats facts from sections 2-4 -> tempts duplicate cards, which `save_cards` should reject.
- Line numbers: cards should cite the original section line, not the recap line.
- HTTP notes: section 7 "Quick review" repeats earlier facts the same way.
