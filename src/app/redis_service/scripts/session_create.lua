-- KEYS:
-- 1 = user_sessions:{user_id}

-- ARGV:
-- 1 = max_sessions
-- 2 = refresh_ttl
-- 3 = now
-- 4 = sid
-- 5 = ip
-- 6 = user_agent
-- 7 = user_id
-- 8 = user_type

local key = KEYS[1]
local max = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local sid = ARGV[4]
local ip = ARGV[5]
local ua = ARGV[6]
local uid = ARGV[7]
local user_type = ARGV[8]

redis.call(
    "HSETEX",
    "session:" .. sid,
    "EX", ttl,
    "FIELDS", 5,
    "uid", uid,
    "ip", ip,
    "user_agent", ua,
    "type", user_type,
    "created_at", now
)
redis.call("ZADD", key, now, sid)
redis.call("EXPIRE", key, ttl)

local removed_info = {}

local count = redis.call("ZCARD", key)
if count > max then
    local excess = count - max
    local old = redis.call("ZRANGE", key, 0, excess - 1)

    for _, osid in ipairs(old) do
        local hash_key = "session:" .. osid

        local info = redis.call("HGETALL", hash_key)
        local obj = { sid = osid }

        for i = 1, #info, 2 do
            obj[info[i]] = info[i+1]
        end

        local ttl_left = redis.call("TTL", hash_key)
        obj.ttl = ttl_left

        table.insert(removed_info, obj)

        redis.call("UNLINK", hash_key)
    end

    redis.call("ZREMRANGEBYRANK", key, 0, excess - 1)
end

return removed_info
