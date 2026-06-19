# GitHub Push — Step-by-Step

**OmniTreasury AI — UiPath AgentHack 2026 Submission**

---

## Prerequisites

- Git installed (`git --version`)
- GitHub account at **github.com**
- GitHub CLI (optional but easier): `gh --version`

---

## Step 1 — Create the GitHub repository

### Option A — GitHub CLI (fastest)

```bash
gh auth login          # follow the browser prompt once
gh repo create OmniTreasury_AI --public --description "Autonomous Treasury Control Tower — UiPath AgentHack 2026"
```

### Option B — GitHub web UI

1. Go to **github.com/new**
2. Repository name: `OmniTreasury_AI`
3. Description: `Autonomous Treasury Control Tower — UiPath AgentHack 2026`
4. Visibility: **Public**
5. Leave "Initialize this repository" **unchecked** (we already have commits)
6. Click **Create repository**

---

## Step 2 — Link local repo to GitHub

```bash
cd "C:\Users\WALTON\Desktop\OmniTreasury_AI"

# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/OmniTreasury_AI.git
```

---

## Step 3 — Rename branch to main (GitHub default)

```bash
git branch -M main
```

---

## Step 4 — Add screenshots (if ready)

If you have taken screenshots and saved them to the `screenshots/` folder:

```bash
git add screenshots/
git commit -m "Add AgentHack demo screenshots"
```

If not, skip this step — you can push screenshots as a separate commit later.

---

## Step 5 — Push to GitHub

```bash
git push -u origin main
```

You will be prompted for your GitHub username + a **Personal Access Token** (PAT).
If you do not have a PAT: **github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token** — scope: `repo`.

---

## Step 6 — Verify the push

```bash
gh repo view --web
# Opens https://github.com/YOUR_GITHUB_USERNAME/OmniTreasury_AI in the browser
```

Confirm:
- README.md renders correctly with the UiPath live agent proof section
- `src/`, `tests/`, `scripts/` folders are visible
- Screenshot table renders (images show after step 4)

---

## Step 7 — Copy the repo URL for Devpost

```
https://github.com/YOUR_GITHUB_USERNAME/OmniTreasury_AI
```

Paste this into the **GitHub repository** field on your Devpost submission page.

---

## Full Command Sequence (copy-paste ready)

```bash
cd "C:\Users\WALTON\Desktop\OmniTreasury_AI"
gh auth login
gh repo create OmniTreasury_AI --public --description "Autonomous Treasury Control Tower — UiPath AgentHack 2026"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/OmniTreasury_AI.git
git branch -M main
git push -u origin main
```

---

## After Pushing — Optional Cleanup

Tag the release for the submission:

```bash
git tag -a v1.0.0 -m "UiPath AgentHack 2026 submission"
git push origin v1.0.0
```

Add the tag to the GitHub Release page: **Releases → Draft a new release → Tag: v1.0.0 → Publish**.

---

*OmniTreasury AI — GitHub Push Guide — UiPath AgentHack 2026*
