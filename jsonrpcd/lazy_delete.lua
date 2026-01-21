redis.debug(ARGV)
local v = redis.call('HGET', KEYS[1], ARGV[1]);
if (v) then
    redis.call('HDEL', KEYS[1], ARGV[1])
    redis.call('PUBLISH', KEYS[1], '{"' .. ARGV[1] .. '":null}')
    return v
end
return ''
