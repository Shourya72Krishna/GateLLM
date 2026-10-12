# GateLLM: Project Idea and Plan

*A clear explanation of what the project is, why it matters, and how to build it step by step. No code in this file. No earlier reading needed.*

---

## 1. The project in one minute

**GateLLM is a small server that sits between your apps and AI models (like ChatGPT or Llama). Its job is to make AI cheaper and more reliable without making answers worse.**

Think of a **smart receptionist** in front of a team of experts:

- A visitor asks a question.
- The receptionist first checks a notebook: *"Has someone asked this before?"* If yes, they read out the saved answer. It is **free and instant**.
- If not, they decide: *"Is this easy or hard?"* Easy questions go to a junior expert (a **cheap** AI model). Hard questions go to a senior expert (a **strong, expensive** AI model).
- If an expert is not available, they ask another one.
- They write down what every question cost and how long it took, so you can see how much money was saved.

GateLLM is exactly this receptionist, written as software.

---

## 2. The problem it solves

Every time an app asks an AI model a question, two things happen: it **costs money** and it **takes time**. Companies that use AI a lot waste both in two ways.

**Waste 1: Asking the same thing again and again.**
"What is a hash map?" and "Can you explain hash maps?" mean the same thing. Without a gateway, you pay for the answer twice.

**Waste 2: Using an expensive model for easy questions.**
"What is the capital of France?" does not need the most powerful (and most expensive) model. A small model answers it just as well.

**Result:** big AI bills and slow apps. GateLLM attacks both problems.

---

## 3. How one request travels through GateLLM

```
 Your app sends a question
          │
          ▼
 ┌──────────────────────────────────────────────────┐
 │                    GateLLM                       │
 │                                                  │
 │  1. Is the caller allowed?  (API key check)      │
 │  2. Is the caller sending too many requests?     │
 │  3. Was this exact question asked before?  ──────┼─► Yes: return saved answer
 │  4. Was a question with the same MEANING         │
 │     asked before?  ──────────────────────────────┼─► Yes: return saved answer
 │  5. Router: is this question easy or hard?       │
 │        easy ──► cheap model                      │
 │        hard ──► strong model                     │
 │     (if a model fails, try the other one)        │
 │  6. Save the answer for next time                │
 │  7. Write down cost and time                     │
 └──────────────────────────────────────────────────┘
          │
          ▼
 Answer goes back to your app (and a dashboard shows the savings)
```

### Five example requests and what happens to each

| What the user asks | What GateLLM does | Why |
|---|---|---|
| "What is a hash map?" (first time) | Cheap model answers. Answer is saved. | Easy question |
| "What is a hash map?" (again) | Returns saved answer. Cost: zero. | Exact same question |
| "Can you explain hash maps?" | Returns saved answer if the meaning is close enough. | Same meaning, different words |
| "Implement an LRU cache and explain the trade-offs" | Strong model answers. | Hard coding question |
| "What is the latest news today?" | Always asks a model. Never saved. | The answer changes every day |

---

## 4. The main parts, explained simply

### 4.1 Exact cache
**What:** A notebook of past questions and answers. If the new question is *word for word* the same, return the saved answer.
**Why:** Simple, fast, and always safe.
**Tool used:** Redis (a very fast memory database).

### 4.2 Semantic cache (the smarter notebook)
**What:** People ask the same thing in different words. The semantic cache catches this by comparing **meaning**, not words.
**How:** A small AI model turns every question into a list of numbers that represents its meaning (this is called an *embedding*). Questions with similar meaning get similar numbers. GateLLM looks up the closest saved question. If it is close enough, it reuses the answer.
**The danger:** Some questions look alike but mean different things, like *"reverse a string"* and *"reverse a list"*. Reusing the wrong answer is a **false hit**. A setting called the **threshold** controls how strict the match must be.
**Our solution:** We do not guess the threshold. We **measure** it using real example pairs, then choose a value that gives many correct hits and very few wrong ones.
**Safety rules:** Never save questions about "today", "latest", "weather", "price", or personal things ("my"). Never save creative requests. Only use it for single questions, not long chats. Answers expire after a set time. Each customer's saved answers are kept separate.
**Tool used:** Qdrant (a database made for searching by meaning).

### 4.3 Router (the decision maker)
**What:** Decides if a question is easy (cheap model) or hard (strong model).
**Two versions:**
1. **Rule router.** Uses simple signs of difficulty: long text, code, math, words like "prove" or "optimize". Quick to build, rough.
2. **Learned router.** A small machine-learning model trained on real examples. We show it many questions, find out which ones the cheap model got wrong, and it learns to spot them.
**A key idea:** The router gives each question a "how likely is the cheap model to fail" score from 0 to 1. A single dial (the **threshold**) turns that score into a decision. Turn the dial one way and you save more money but lose some quality. Turn it the other way and you keep quality but save less. We draw this trade-off as a chart.

### 4.4 Fallback
**What:** If one model is down or too busy, automatically try another one.
**Why:** The app keeps working even when a provider has problems.

### 4.5 Safety and control
- **API keys:** only approved callers can use the gateway.
- **Rate limit:** each caller gets a maximum number of requests per minute, so a bug cannot burn your budget.
- **No private text in logs:** we record sizes and costs, not what people asked.

### 4.6 Tracking and dashboard
**What:** Every request is recorded: which model, how many tokens, how much it cost, how long it took, and **what it would have cost if we always used the strong model**. A live web dashboard shows the totals.
**Why:** This is the proof. "Saved 60%" must be a number you can show, not a claim.

### 4.7 Works with existing apps
GateLLM copies the format that OpenAI uses. Any app built for OpenAI can switch to GateLLM by changing **one web address**. Nothing else changes.

---

## 5. How we know it works (the honest part)

Most student projects say "it works" and stop. This one **measures** everything. You will produce these numbers yourself:

| Number | What it tells you |
|---|---|
| **Cost saved** compared to "always use the strong model" | The main result |
| **Quality kept** (an AI judge scores answers from 1 to 10) | Proof that cheaper did not mean worse |
| **Cache hit rate** | How often saved answers were reused |
| **Cache false-hit rate** | How often a saved answer was *wrong* for the new question |
| **Speed** (typical and slow cases, with 100 users at once) | Whether it is fast enough to use |

**Comparing against simple alternatives.** A result only means something next to a baseline. We compare against:
- *Always strong* (best quality, highest cost)
- *Always cheap* (lowest cost, lower quality)
- *Rule router* vs *learned router*
- *Best possible router* (a perfect decision maker, shows the upper limit)

All of this goes on one chart (cost on one side, quality on the other). A good system sits **higher and further left**.

**Being honest about limits.** The AI judge is not perfect. Prompts from public datasets may differ from real traffic. Write these limits in your README. It makes the project more believable, not weaker.

---

## 6. Tools used (and why)

| Tool | Plain-language job |
|---|---|
| **Python** | The main language |
| **FastAPI** | Builds the web server (the API) |
| **LiteLLM** | One simple way to talk to many AI providers |
| **Redis** | Fast memory for the exact cache and the rate limit |
| **Qdrant** | Finds saved questions with similar meaning |
| **Sentence-Transformers (a small embedding model)** | Turns text into "meaning numbers" |
| **scikit-learn** | Trains the learned router |
| **SQLite** | Simple file database for the request log |
| **Streamlit** | Builds the live dashboard |
| **Locust** | Simulates many users to test speed |
| **Docker + Docker Compose** | Starts the whole system with one command |
| **pytest** | Automatic tests |
| **Groq (free tier)** | Free AI models to run the project |

---

## 7. What you will have at the end

1. A **working gateway** you can start with one command.
2. **Real measured results**: money saved, quality kept, cache safety, speed.
3. A **cost-vs-quality chart** and a **cache safety chart**.
4. A **live dashboard**.
5. **Automatic tests** that pass.
6. A clean **GitHub project** with a README, charts, and a 2-minute demo video or GIF.

---

## 8. What you need before starting

**Skills (basic level is enough):**
- Python basics (functions, files, installing packages)
- Using a terminal
- A rough idea of what an API is

**Everything else you learn while building.** The plan below introduces each idea when it is needed.

**Tools to install:** Python 3.11 or newer, Git, Docker Desktop, a code editor (VS Code is fine).

**Accounts:** a free **Groq** account for an API key. A second free key from a different provider (for example Google's Gemini) is recommended for the quality judge, so the judge is not biased toward the same model family.

**Money:** nothing. Everything runs on free tiers and your own computer. If you ever use a paid provider, set a spending limit first.

**Time:** about **4 weeks** at 1 to 2 hours a day for the core project. Two optional extra weeks add advanced features.

---

## 9. The project plan

The plan has a **core** (Weeks 1 to 4) and **optional extras** (Weeks 5 and 6). The core alone is a complete, impressive project.

### Week 1: Foundation. Build a first working gateway

**Goal:** a server that accepts a question, calls an AI model, and records the cost.

**Tasks**
- [ ] Set up the project folder and Python environment
- [ ] Get the free API key and save it safely in a settings file (never in the code)
- [ ] Start Redis and Qdrant using Docker
- [ ] Build the settings, price table, and cost calculation
- [ ] Build the request log (SQLite)
- [ ] Build the part that talks to AI models, with fallback
- [ ] Add API key checking
- [ ] Build the first simple gateway endpoint
- [ ] Test it with a normal OpenAI library by changing one web address

**Done when:** you send a question, get an answer, and see its cost in the log. A wrong API key is rejected.

**Why it matters:** you already have a real, working product. Everything else adds to it.

---

### Week 2: Caching, router version 1, full gateway, tests

**Goal:** add both caches and a rule-based router, then protect it with tests.

**Tasks**
- [ ] Learn what embeddings are (a short, simple idea: meaning as numbers)
- [ ] Build the embedding step
- [ ] Build the rate limiter
- [ ] Build the exact cache
- [ ] Build the semantic cache with all the safety rules from Section 4.2
- [ ] Build the rule-based router
- [ ] Join everything into the full gateway (including streaming answers word by word)
- [ ] Try each feature by hand: same question twice, reworded question, "latest news today", hard question
- [ ] Write automatic tests (they run without internet or API keys, using a fake AI)

**Done when:**
- The same question twice gives a free, instant answer the second time.
- A reworded question can reuse the saved answer.
- "Latest news today" is never saved.
- A hard coding question goes to the strong model.
- All tests pass.

---

### Week 3: The learned router and the benchmark

**Goal:** replace guessing with data, and measure the savings honestly.

**Tasks**
- [ ] Download public question datasets (math, coding, general questions) and split them into a **training set** and a **separate test set**
- [ ] For each question, get the cheap answer and the strong answer
- [ ] Use an AI judge to score both answers
- [ ] Label each question: "hard" if the strong answer was clearly better, otherwise "easy"
- [ ] Train the learned router on the training set
- [ ] Turn the learned router on in the gateway
- [ ] Run the benchmark **on the test set only** and draw the cost-vs-quality chart
- [ ] Choose the threshold that saves the most money while keeping about 95% of the quality
- [ ] Write down the headline: "Cost down X%, quality kept Y%, on N test questions"

**Done when:** you have a chart comparing always-cheap, always-strong, the rule router, and the learned router, plus one clear headline sentence with real numbers.

**Practical tips:** start small (about 300 training and 100 test questions). Free tiers have limits, so run it in small batches. The scripts can stop and continue later.

---

### Week 4: Make it safe, visible, and shareable

**Goal:** prove the cache is safe, show the results live, and package the project.

**Tasks**
- [ ] **Cache safety measurement:** create pairs of questions (same meaning vs. similar words but different meaning), test many threshold values, draw the chart, and choose a safe threshold
- [ ] Build the live dashboard (money saved, cache hits, speed)
- [ ] **Load test:** simulate 100 users at once and record typical and slow response times
- [ ] Package everything with Docker Compose so one command starts it all
- [ ] Write the README with your real numbers, both charts, a dashboard screenshot, and a short demo recording
- [ ] Add an honest "Limitations" section
- [ ] Publish on GitHub

**Done when:** a stranger can download the project, run one command, and see it working, and your README shows measured results.

---

### Optional Week 5: Check the cheap answer, then escalate (the cascade)

**Idea:** instead of only deciding *before* answering, let the cheap model answer first. A small checker then estimates whether that answer is probably wrong. If it looks risky, call the strong model and use that answer instead.

**Why it is interesting:** you pay for the strong model only when the cheap answer looks bad. You can place this strategy on the same chart as the router and see which is better.

**Tasks:** build the checker, score the cheap answers you already have, add the "cascade" to the benchmark chart, try it live.

**Honest note:** it does not work with word-by-word streaming (the answer is already sent), and a small checker can itself be wrong. Measuring that is part of the project.

---

### Optional Week 6: Predict failure before answering (the risk probe) and extras

**Idea:** a small AI model running on your own computer reads the question. Its *internal numbers* (activations) are used to predict "will the cheap model fail on this?" before any provider is called. This is a research-style router. It connects to work on detecting AI mistakes before they happen.

**Other extras for this week:**
- **Shadow monitor:** quietly re-check a small share of cheap answers with the strong model in the background, to confirm quality is not dropping.
- **Per-user daily spending limit.**
- **Judge check:** hand-score about 30 comparisons yourself and measure how often the AI judge agrees with you.
- **Automatic tests on GitHub** (a green badge on your project).

---

## 10. Risks and how to handle them

| Risk | What could go wrong | What to do |
|---|---|---|
| Semantic cache returns a wrong answer | Similar-looking questions with different meanings | Measure the threshold (Week 4). Use the safety rules. State the false-hit rate honestly. |
| AI judge is biased | Quality numbers look better than they are | Use a judge from a different provider. Shuffle answer order. Check it against your own scores. |
| Free API limits | Scripts stop with "rate limit" errors | Use small batches and low concurrency. Re-run later. Scripts continue where they stopped. |
| Router learns too little | Not much better than the rules | Add more training questions, add your own domain questions, try a different "hard" cutoff. |
| Project is too big | You run out of time | Do only Weeks 1 to 3. That is already a finished project. |
| Model names or prices change | Errors like "model not found" | Update names and prices in the settings file. No code changes needed. |
| Secret keys leak | Keys end up on GitHub | Keep keys only in the ignored settings file. Check before every commit. |

---

## 11. How to present the project

**Resume lines (fill in your real numbers):**
- Built **GateLLM**, an OpenAI-compatible LLM gateway with semantic caching, a learned model router, fallback, and cost tracking.
- Trained a router that cut inference cost by **X%** while keeping **Y%** of strong-model quality on **N** held-out questions.
- Measured cache safety on labelled question pairs and chose the threshold from the data: **X%** hit rate, **Y%** false hits.
- Load tested with 100 simultaneous users: p95 latency **X ms**, no errors. Docker Compose setup and automatic tests.

**The 2-minute demo:**
1. Show the dashboard.
2. Ask an easy question. Show it went to the cheap model.
3. Ask a hard question. Show it went to the strong model.
4. Ask the first question again. Show it is free and instant.
5. Reword it. Show the semantic cache catches it.
6. Show the cache safety chart and the cost-vs-quality chart.
7. Show the savings line on the dashboard.

**What interviewers will like:**
- You **measured** things instead of just claiming them.
- You thought about **failure** (what if Redis is down? what if a model fails?).
- You thought about **safety** (wrong cache hits, private data, spending limits).
- You can explain the trade-offs: cost vs quality, cache hits vs wrong answers.

**Be ready for:** "Why not use an existing gateway like LiteLLM Proxy or Portkey?" A good answer: those exist and are good. You built this to learn how they work, and to add something you could measure yourself: a learned router compared against baselines, and a cache threshold chosen from data.

---

## 12. Words you will see

| Word | Simple meaning |
|---|---|
| **LLM** | A large AI language model that answers text questions |
| **Token** | A small piece of text (about 4 letters). Providers charge per token. |
| **Prompt** | The question or text you send to a model |
| **Provider** | A company that runs models (Groq, OpenAI, Google, ...) |
| **Gateway** | A server in the middle that forwards requests and adds features |
| **Embedding** | A list of numbers that represents the meaning of a text |
| **Cache** | A notebook of saved answers |
| **Threshold** | A cut-off number. Above it, do one thing. Below it, do another. |
| **Router** | The part that picks the cheap or strong model |
| **Fallback** | Plan B when something fails |
| **Latency** | How long a request takes |
| **p95 latency** | 95 out of 100 requests are faster than this number |
| **LLM judge** | A strong AI that scores answers so we can measure quality |
| **Cascade** | Try the cheap model first, check the answer, escalate if risky |
| **Mock mode** | A fake AI used for testing without any API key |

---

## 13. How to start today

1. Install Python, Git, and Docker Desktop.
2. Create a free Groq account and get an API key.
3. Create the project folder on your computer and start a Git repository.
4. Begin **Week 1, first task**. Do not read ahead. One task at a time.

When you want the detailed, step-by-step build instructions with all the code, ask for the **Build Guide**. This file is the map. The Build Guide is the walking directions.
