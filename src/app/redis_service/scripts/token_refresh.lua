-- KEYS:
-- 1 = session:{old_sid}
-- 2 = user_sessions:{user_id}

-- ARGV:
-- 1 = old_sid
-- 2 = new_sid
-- 3 = uid
-- 4 = ttl
-- 5 = now
-- 6 = ip
-- 7 = ua
-- 8 = user_type

local rotated = redis.call("HGET", KEYS[1], "rotated")
if rotated == "1" then
    return { err = "REPLAY" }
end

local half_ttl = math.floor(tonumber(ARGV[4]) / 2)
if half_ttl < 1 then
    half_ttl = 1
end

redis.call(
    "HSETEX",
    KEYS[1],
    "EX", half_ttl,
    "FIELDS", 2,
    "rotated", "1",
    "rotated_at", ARGV[5]
)

redis.call("ZREM", KEYS[2], ARGV[1])

local new_key = "session:" .. ARGV[2]
redis.call(
    "HSETEX",
    new_key,
    "EX", tonumber(ARGV[4]),
    "FIELDS", 5,
    "uid", ARGV[3],
    "type", ARGV[8],
    "ip", ARGV[6],
    "user_agent", ARGV[7],
    "created_at", ARGV[5]
)

redis.call("ZADD", KEYS[2], ARGV[5], ARGV[2])

return ARGV[2]
