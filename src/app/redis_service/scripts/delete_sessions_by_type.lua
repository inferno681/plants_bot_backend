-- KEYS[1]= user:sessions:{user_id}

-- ARGV[1]: ='session:' session key prefix
-- ARGV[2]: = type to delete

local all_sids = redis.call('ZRANGE', KEYS[1], 0, -1)
local deleted_count = 0

for _, sid in ipairs(all_sids) do
    local session_key = ARGV[1] .. sid
    local stored_type = redis.call('HGET', session_key, 'type')

    if stored_type == ARGV[2] then
        redis.call('DEL', session_key)
        redis.call('ZREM', KEYS[1], sid)
        deleted_count = deleted_count + 1
    end
end

return deleted_count
