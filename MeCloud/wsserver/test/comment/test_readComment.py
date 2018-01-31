import httplib

# cookie = 'u="2|1:0|10:1506671668|1:u|32:NTljZGZhZDU1MTE1OWEyODRlZWViYzQw|b73bf9a0c49bc6e2213a58b12dec2e0d94fc0d42f1ff9f30dfa51335e2a00a77"'
cookie = 'u="2|1:0|10:1508582078|1:u|32:NTlkYzYyNjZjYTcxNDMyN2FmMmU0ZTg1|58e21bcb52acf0b6855226deee07419b25a990eebd9e55a733cf0ec36508abec"'
base = 'localhost'
# base = 'n01.me-yun.com'
path = '/1.0/comment/read'
#body = '{"from_id":"59cdfad551159a284eeebc40","message_id":"59e47d2551159a577b4a13aa","m_id":"596cac72b4b33e28c0e746f8"}'

body = '{"from_id":"59e861b7ca714367c7ea89dd","message_id":"59eb2288ca71430c388625a2","m_id":"596cac72b4b33e28c0e746f8"}'

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
