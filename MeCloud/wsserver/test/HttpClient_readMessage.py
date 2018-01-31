import httplib
#userid 59dc6266ca714327af2e4e85
cookie = 'u="2|1:0|10:1506671668|1:u|32:NTljZGZhZDU1MTE1OWEyODRlZWViYzQw|b73bf9a0c49bc6e2213a58b12dec2e0d94fc0d42f1ff9f30dfa51335e2a00a77"'
# cookie = 'u="2|1:0|10:1508570328|1:u|32:NTlkYzYyNjZjYTcxNDMyN2FmMmU0ZTg1|98788f9a7e0f7e7ca101598cf14301ac7c9d5d05171c61e4a5299ed3c31420b6"'
base = 'localhost'
# base = 'n01.me-yun.com'
path = '/1.0/push/readMessage'
# body = '{"from_id":"59e861b7ca714367c7ea89dd","message_id":"59e87107ca714367c7ea89ef"}'

body = '{"message_id":"59f03ab851159a27b8e56519","from_id":"59ed78feca71434a3f370db7"}'

try:
    header = {'Cookie': cookie, 'X-MeCloud-Debug': 1}  # 'Cookie': cookie,
    print header
    httpClient = httplib.HTTPConnection(base, 8000, timeout=30)
    httpClient.request("POST", path, body, header)

    response = httpClient.getresponse()
    print response.status
    print response.reason
    print response.read()
    # print response.msg
    # print response.getheaders()
except Exception, e:
    print e
finally:
    if httpClient:
        httpClient.close()
