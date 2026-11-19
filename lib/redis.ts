import { Redis } from "@upstash/redis";

/**
 * Upstash Redis client.
 *
 * Reads credentials from UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN
 * in the environment (see .env).
 */
export const redis = Redis.fromEnv();
