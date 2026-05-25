// ============================================
// ANDY_RUNTIME_V1 — PRODUCTION CORE (HARDENED)
// ============================================

import Queue from "bull";
import IORedis from "ioredis";
import fs from "fs";
import crypto from "crypto";

const redis = new IORedis();
const queue = new Queue("andy-runtime", { redis });

// –––––––– LOGGING ––––––––
function log(type, msg, meta = {}) {
  const entry = { time: Date.now(), type, msg, meta };
  try {
    console.log(entry);
    fs.appendFileSync("runtime.log", JSON.stringify(entry) + "\n");
  } catch (e) {
    console.error("LOG_FAIL", e);
  }
}

// –––––––– IDEMPOTENCY ––––––––
async function isProcessed(key) {
  try {
    return await redis.get(`andy:done:${key}`);
  } catch {
    log("REDIS_FAIL", "isProcessed", { key });
    return null;
  }
}

async function markProcessed(key) {
  try {
    await redis.set(`andy:done:${key}`, 1, "EX", 3600);
  } catch {
    log("REDIS_FAIL", "markProcessed", { key });
  }
}

// –––––––– TIMEOUT ––––––––
function withTimeout(promise, ms, step) {
  let timeoutId;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error(`Timeout: ${step}`));
    }, ms);
  });

  return Promise.race([promise, timeout]).finally(() => {
    clearTimeout(timeoutId);
  });
}

// –––––––– SAFE EXECUTION ––––––––
async function safeExecute(fn, step) {
  try {
    return await fn();
  } catch (e) {
    log("AGENT_ERROR", step, { error: e.message });
    throw e;
  }
}

// –––––––– AGENTS ––––––––
const Agents = {
  "A_CORE:init_state": async () => {
    log("STEP", "init_state");
  },
  "A_CORE:run_single_agent_cycle": async () => {
    log("STEP", "run_cycle");
  },
  "A_GITHUB:sync_repo": async () => {
    log("STEP", "github_sync");
  },
  "A_NOTION:update_docs": async () => {
    log("STEP", "notion_update");
  },
  "A_VERCEL:deploy": async () => {
    log("STEP", "vercel_deploy");
  },
  "A_HUBSPOT:update_analytics": async () => {
    log("STEP", "hubspot_update");
  },
  "A_FIGMA:sync_design": async () => {
    log("STEP", "figma_sync");
  },
};

// –––––––– PIPELINES ––––––––
const pipelines = {
  P_CORE: ["A_CORE:init_state", "A_CORE:run_single_agent_cycle"],
  P_FULLSTACK: [
    "A_GITHUB:sync_repo",
    "A_NOTION:update_docs",
    "A_VERCEL:deploy",
    "A_HUBSPOT:update_analytics",
    "A_FIGMA:sync_design",
  ],
};

// –––––––– EXECUTION ENGINE ––––––––
async function runPipeline(name, jobId) {
  log("PIPELINE_START", name, { jobId });

  const steps = pipelines[name];
  if (!steps) {
    throw new Error(`Unknown pipeline: ${name}`);
  }

  for (const step of steps) {
    if (!Agents[step]) {
      throw new Error(`Unknown step: ${step}`);
    }

    const key = crypto
      .createHash("sha256")
      .update(`${jobId}:${name}:${step}`)
      .digest("hex");

    if (await isProcessed(key)) {
      log("SKIP", step, { jobId });
      continue;
    }

    try {
      await withTimeout(safeExecute(Agents[step], step), 10000, step);
      await markProcessed(key);
    } catch (err) {
      log("ERROR", `step failed: ${step}`, {
        jobId,
        error: err.message,
      });

      throw err;
    }
  }

  log("PIPELINE_DONE", name, { jobId });
}

// –––––––– IMPACT SCORE ––––––––
function impactScore() {
  return Math.random();
}

// –––––––– JOB PROCESSOR ––––––––
queue.process(5, async (job) => {
  const { pipeline } = job.data;
  const jobId = job.id;

  log("JOB_START", pipeline, { jobId });
  await runPipeline(pipeline, jobId);

  const score = impactScore();
  if (score < 0.9999) {
    log("ALERT", "ImpactScore drop", { jobId, score });
    throw new Error("ImpactScore violation");
  }

  log("JOB_DONE", pipeline, { jobId });
});

// –––––––– ERROR HANDLING ––––––––
queue.on("failed", (job, err) => {
  log("JOB_FAILED", job.data.pipeline, {
    jobId: job.id,
    error: err.message,
  });
});

queue.on("completed", (job) => {
  log("JOB_COMPLETED", job.data.pipeline, {
    jobId: job.id,
  });
});

// –––––––– DISPATCH ––––––––
async function dispatch() {
  const baseOptions = {
    attempts: 3,
    backoff: {
      type: "exponential",
      delay: 5000,
    },
    removeOnComplete: true,
    removeOnFail: false,
  };

  await queue.add({ pipeline: "P_CORE" }, baseOptions);
  await queue.add({ pipeline: "P_FULLSTACK" }, baseOptions);
}

dispatch();
log("BOOT", "ANDY_RUNTIME_V1 started");
