-- Atomically create link code <-> user mapping.
-- KEYS[1] = LINK_CODE{code}
-- KEYS[2] = LINK_USER{user_id}
-- ARGV[1] = user_id
-- ARGV[2] = code
-- ARGV[3] = ttl (seconds)

if redis.call('exists', KEYS[1]) == 1 then
  return 0
end
if redis.call('exists', KEYS[2]) == 1 then
  return 0
end

redis.call('set', KEYS[1], ARGV[1], 'EX', ARGV[3])
redis.call('set', KEYS[2], ARGV[2], 'EX', ARGV[3])
return 1
