# Agent Lab - Sample Input Files

Sample inputs for the six Claude Agent SDK starter assignments. Each folder matches one assignment in the handout.
Every assignment has at least two inputs: build against the first, then check your agent still works on the second.
Some files contain tricky cases on purpose. Your agent should handle them sensibly.

All names, companies, phone numbers and amounts are made up.

## How to use

Copy the folder for your assignment into your `agent-lab` project. Unzip the zip files first:

```powershell
Expand-Archive .\01-tidybot\sample-downloads.zip -DestinationPath .
Expand-Archive .\04-snapnamer\sample-images.zip -DestinationPath .
```

TidyBot and SnapNamer move or rename files. Keep the original zip so you can unzip a fresh copy after every run.

## What's inside

| Folder | Assignment | Files |
| --- | --- | --- |
| `01-tidybot` | 1. TidyBot | `sample-downloads.zip` (about 30 mixed files), `sample-downloads-2.zip` (a second, messier folder) |
| `02-spendsense` | 2. SpendSense | `statement-sample.csv` (September 2026), `statement-sample-2.csv` (October 2026, for the stretch goal) |
| `03-minuteman` | 3. MinuteMan | `standup-transcript.txt` (short), `planning-meeting-transcript.txt` (longer, with changes of plan) |
| `04-snapnamer` | 4. SnapNamer | `sample-images.zip` (12 images), `sample-images-2.zip` (8 images) |
| `05-digestbot` | 5. DigestBot | `topics.txt` (topics to try; DigestBot reads the live web) |
| `06-studycards` | 6. StudyCards | `notes-photosynthesis.md`, `notes-http-basics.txt` |

## Notes

- **Statement CSVs:** columns are `date,description,amount`. Amounts are in Indian rupees. Negative = money spent, positive = money received.
- **Installers in TidyBot:** the installer files are small placeholders, not real programs. Windows `.exe` and `.msi` files are left out because email filters block them.
- **Images and placeholders** were generated for this exercise; none show real people.
