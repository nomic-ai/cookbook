# Federal Register Job

Uploads data daily from the U.S. Federal Register API to the `nomic/federal_register` Nomic Atlas dataset.

This script can be deployed and scheduled using either Modal (recommended) or GitHub Actions.

## Method 1: Modal

Uses `process_data_modal.py` to run the job as a [Modal](https://modal.com/) scheduled function.

**Setup:**

1.  Install Modal CLI: `pip install modal`
2.  Create Modal Secret (replace `<your_api_key_here>`):

```bash
modal secret create nomic-api-key NOMIC_API_KEY=<your_api_key_here>
```

3. Deploy the script:
```bash
modal deploy --name daily_process_data_modal process_data_modal.py
```

Deploying the script automatically enables the schedule.

## Method 2: GitHub Actions

Uses a GitHub Actions workflow to run the `process_data.py` script (or a modified version) on a schedule.

**Setup:**

1.  **Move Workflow File:** Copy or move the workflow YAML file (`federal_register_job.yml`) to the `.github/workflows/` directory in the root of your repository. **It must be in this specific directory for GitHub Actions to recognize it.**
2.  **Configure Secret:** Add your Nomic API key as a repository secret named `NOMIC_API_KEY` in your GitHub repository's Settings -> Secrets and variables -> Actions.
3.  **Commit & Push:** Commit the workflow file in the `.github/workflows/` directory and push it to your `main` (or default) branch.
