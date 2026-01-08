-- KEYS:
-- 1 = session:{old_sid}
-- 2 = user_sessions:{user_id}

-- ARGV:
-- 1 = old_sid
-- 2 = new_sid
-- 3 = user_id
-- 4 = ttl
-- 5 = now
-- 6 = ip
-- 7 = user_agent

-- 1. Проверяем, что сессия существует
if redis.call("EXISTS", KEYS[1]) == 0 then
    return { err = "SESSION_NOT_FOUND" }
end

-- 2. Проверяем владельца
local stored_uid = redis.call("HGET", KEYS[1], "uid")
if not stored_uid or stored_uid ~= ARGV[3] then
    return { err = "INVALID_OWNER" }
end

-- 3. Удаляем старую сессию
redis.call("DEL", KEYS[1])
redis.call("ZREM", KEYS[2], ARGV[1])

-- 4. Создаём новую сессию
redis.call(
    "HSET",
    "session:" .. ARGV[2],
    "uid", ARGV[3],
    "ip", ARGV[6],
    "user_agent", ARGV[7],
    "created_at", ARGV[5]
)
redis.call(
    "EXPIRE",
    "session:" .. ARGV[2],
    tonumber(ARGV[4])
)

-- 5. Добавляем в ZSET
redis.call(
    "ZADD",
    KEYS[2],
    ARGV[5],
    ARGV[2]
)

return ARGV[2]
