# Self-Healing Docs - Quick Start

This guide shows how to add Self-Healing Docs to a GitHub repository.

## Prerequisites

Before setting up the action, make sure:

* Your repository uses GitHub Actions.
* Your code is written in one of the supported languages:

  * C++
  * Go
  * Java
  * JavaScript
  * Python
  * Rust
  * TypeScript
  * TSX
* You have permission to configure repository secrets and Actions settings.
* You have a Gemini API key.

## 1. Create the workflow

Create this file:

```text
.github/workflows/self-healing-docs.yml
```

Copy the following workflow into the file:

```yaml
name: Self-Healing Docs

on:
  pull_request:
    types: [closed]

permissions:
  contents: write
  pull-requests: write

jobs:
  self-healing-docs:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Run Self-Healing Docs
        uses: krishnagp97/self-healing-doc@v1
        with:
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
          github-token: ${{ github.token }}
```

> Important: The actions/checkout@v4 step is required because Self-Healing Docs needs access to the repository's Git history to compare the code before and after the merged pull request.

## 2. Add the Gemini API key

Self-Healing Docs uses Gemini to review whether the affected documentation needs to be updated.

Go to:

**Settings → Secrets and variables → Actions**

Click **New repository secret** and create:

```text
Name:
GEMINI_API_KEY
```

Paste your Gemini API key as the secret value.

The workflow uses the secret here:

```yaml
gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
```

> **Important:** Never add your Gemini API key directly to the workflow file or commit it to your repository.

## 3. Configure GitHub Actions permissions

Go to:

**Settings → Actions → General**

Under **Workflow permissions**, select:

**Read and write permissions**

If available, enable:

**Allow GitHub Actions to create and approve pull requests**

Click **Save**.

These permissions allow the action to create documentation branches, push changes, create pull requests, and comment on the original pull request.

## 4. Test the action

1. Make a code change that should affect existing documentation.
2. Push the change to a branch.
3. Open a pull request.
4. Merge the pull request.
5. Open the **Actions** tab to view the workflow run.

If the documentation needs an update, Self-Healing Docs will create a separate documentation pull request.

If no update is needed, no documentation pull request is created.
