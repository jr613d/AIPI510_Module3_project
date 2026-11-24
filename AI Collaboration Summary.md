# AI Collaboration Summary

I built this project with AI coding assistants. This page is the short version of how that worked. If you want every decision, every mistake, and every check, it's all in the full [collaboration log](collaboration.md).

## At a Glance

| | |
| --- | --- |
| **My role** | I made the project decisions, reviewed every step, and merged every pull request. |
| **The AI's role** | The assistants proposed options, wrote the code and tests, ran the checks, and explained what they were doing as they went. |
| **The team** | One AI coding assistant for the first few steps, then Claude Code running as two agents in parallel: one on the back end (API, Docker, deployment) and one on the front end and documentation. |
| **The result** | 12 pull requests, 106 automated tests, a live API on Google Cloud Run, a live Streamlit app, and public experiment tracking in Weights & Biases. |

## How We Worked Together

**One step at a time.** Every step got its own branch and its own pull request. The AI explained its plan, paused when there was a decision to make, showed me what changed and how it was checked, and only committed after I reviewed it. I merged every pull request myself.

**I kept a hand on the wheel.** I set up the cloud bucket, installed Docker, and ran every cloud deployment command myself. The AI wrote the commands and explained each one before I ran it. When something was written for people, like the ethics section, I chose the points and the AI helped me shape them.

**Two agents, no collisions.** Once the work split, each agent worked in its own copy of the repository, on its own branch, with its own files. They both built against an API contract I approved: what goes into a prediction request, what comes back, and how errors look. Any change to that contract came back to me.

**Honest records.** Every step went into the collaboration log, including the AI's mistakes and how they got fixed.

## The Rules of Engagement (AGENTS.md)

`AGENTS.md` is the instruction file the AI reads before it touches the repository. Here's what it told the AI.

**Do:**

- Treat this as my project. I decide; the AI implements, tests, and explains.
- Explain each step, and pause for my decisions and questions.
- Work one agreed step at a time, each on its own branch, starting from the latest `main`.
- Summarize the changes and checks before every commit, and let me review and merge.
- Record the AI's help honestly in the collaboration log.
- Pull training data from the cloud, verify it with a checksum, and record exactly which data was used.

**Don't:**

- Don't jump ahead to future steps or change the plan without talking to me.
- Don't commit data files, virtual environments, or credentials.
- Don't alter the raw data, use customer IDs as model inputs, or fit preprocessing before the data is split.
- Don't touch the test set until the model and threshold are final.
- Don't oversell what a model trained on fictional data can do.

## The Steps

| Step | What we built | What I decided |
| --- | --- | --- |
| 1. Setup and ingestion | Verified download and cleaning of the dataset | Customer churn as the problem; keep every row; ROC AUC as the main metric |
| 2. Cloud storage | Dataset in Google Cloud Storage | Set up the bucket myself |
| 3. Training | Logistic regression pipeline run from `config.yaml` | Leave out zero-tenure customers; start with eight inputs; Python 3.13 |
| 4. Experiment tracking | Every training run recorded in Weights & Biases | Track online by default |
| 4b. Model selection | 8 experiments, a threshold comparison, one test | Keep the simple model; set the threshold at 35%; test exactly once |
| 5. API | FastAPI `/predict` endpoint | Strict input checks; no predictions outside the training ranges; split the work between two agents |
| 6. Docker | One image that trains, serves, and tests | Build the model into the image; never store credentials in it |
| 6b. Reproducibility | Public data file and W&B project | Anyone can retrain without my logins |
| 7. Deployment | Public API on Google Cloud Run | Command line only; I ran every command; limit it to one instance to control cost |
| 8. Front end | Streamlit app with a "what if?" explorer | Sliders limited to the training ranges |
| 9. Final review | Ethics and limitations, README restructure | Choose the ethics points myself; keep it concise and easy to grade |

## My Reflection

It was a fantastic learning experience, because this is why I got into this course: to get hands-on experience building things in collaboration with AI and to get a depth of understanding (so that I understand how the pieces fit together and how they are all intended to function to complement a production pipeline), while not having to put hands to keyboard to write Python code or troubleshoot code.

I felt like I was able to quarterback an AI agent team of two. I kept them going at a pace that kept me in the loop and understanding what they were doing at every step, while they made a lot of recommendations that, honestly, were good and I didn't really have to deviate too much from.

There were some interesting points of communication back through the READMEs, through the documentation, and through the ethics and limitations discussions. I can tell, as soon as the agent is writing something for a human, that my view and my voice are going to be better than just letting the agent write it. In terms of Python and code and other things like that, it's so much better than me, so much better than I will ever be.

I still have a lot more to learn about Docker, Google Cloud, and production ML pipelines. I was intrigued by the full suite of resources available on Google Cloud and through the Weights & Biases platform, and I now want to go explore more about what these are and can do.

One of my big concerns is about security and understanding how the choices that are made at the setup phase for these systems have downstream implications for security and cost, particularly as I'm building APIs with connections to models in cloud storage. I have accountability for the costs incurred there.

I needed to make some things public to satisfy the project requirements, but left to my own devices, I would experiment in private.

## The AI's Take, in Brief

I asked the AI to reflect on its side of the process. The short version:

- **What helped:** turning my decisions into tested code, laying out the trade-offs before I chose, and running two agents in parallel against a contract I approved.
- **What went wrong:** early on, the first assistant built too much, too fast, until I slowed it down. Later, one agent's cleanup shut down a test server I was running, and its first ethics draft was long and didn't sound like me. Smaller bugs were caught by testing.
- **What I changed:** in its words, my questions (who belongs in the model, when to touch the test set, how to enforce the limits) shaped the project more than any code did, and my rewrite of the ethics section made it better.
- **Next time:** ask for a writing sample before drafting anything for people, agree on shared contracts before working in parallel, and make the cost and security consequences visible at setup.
