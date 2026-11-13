import base64
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import http.cookiejar
from unittest.mock import patch
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

# Valid one-pixel PNG; no external imaging library required.
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')

class WorkbenchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        server.DATA = Path(self.tmp.name)
        server.init()
        self.http = server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever,daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:'+str(self.http.server_port)

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.tmp.cleanup()

    def call(self,path,body=None):
        req = urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    def test_cross_batch_dedup_and_persistence(self):
        payload = {'name':'photo.png','batch':'week 1','data':base64.b64encode(PNG).decode()}
        first = self.call('/api/import',payload)
        payload['batch']='week 2'
        second = self.call('/api/import',payload)
        self.assertEqual(first['id'],second['id'])
        self.assertTrue(second['duplicate'])
        server.init()
        self.assertEqual(len(self.call('/api/items')),1)
        self.assertEqual(len(list((server.DATA/'images').iterdir())),1)

    def test_demo_review_export(self):
        self.call('/api/demo',{})
        self.call('/api/demo',{})
        items = self.call('/api/items')
        self.assertEqual(len(items),12)
        self.assertTrue(all(x['demo']==1 for x in items))
        for item in items:
            with urllib.request.urlopen(self.url+'/image/'+str(item['id'])) as r:
                self.assertEqual(r.headers['Content-Type'],'image/png')
                self.assertTrue(r.read().startswith(b'\x89PNG'))
        selected = items[0]['id']
        self.call('/api/review',{'id':selected,'review':'confirmed','note':'=not-a-formula'})
        server.init()
        self.assertEqual(self.call('/api/items')[0]['review'],'confirmed')
        with urllib.request.urlopen(self.url+'/api/export') as r:
            exported = r.read().decode('utf-8-sig')
        self.assertIn("'=not-a-formula",exported)
        self.assertIn('预设演示',exported)

    def test_routing_and_invalid_outputs(self):
        value = dict(vehicle='yes',sign='yes',marking='no',relation='unclear',evidence=[],uncertainties=[])
        self.assertEqual(server.normalize(value)['category'],'uncertain')
        value['relation']='yes'
        self.assertEqual(server.normalize(value)['category'],'candidate')
        value['sign']='no'
        self.assertEqual(server.normalize(value)['category'],'none')
        with self.assertRaises(ValueError):
            server.normalize({'vehicle':'yes'})

    def test_weekly_sample_files_deduplicate(self):
        counts=[]
        for week in ('week-01','week-02'):
            results=[server.add_image(p.name,week,p.read_bytes()) for p in (server.ROOT/'samples'/week).glob('*.png')]
            counts.append((sum(not r['duplicate'] for r in results),sum(r['duplicate'] for r in results)))
        self.assertEqual(counts,[(8,0),(4,2)])
        self.assertEqual(len(self.call('/api/items')),12)

    def test_public_sessions_https_and_data_isolation(self):
        original=server.PUBLIC
        server.PUBLIC=True
        first=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        second=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        def get(client,path):
            with client.open(self.url+path) as r:return json.load(r)
        def post(client,path,body):
            req=urllib.request.Request(self.url+path,json.dumps(body).encode(),{'Content-Type':'application/json','Origin':self.url.replace('http:','https:')})
            with client.open(req) as r:return json.load(r)
        try:
            a=get(first,'/api/items');b=get(second,'/api/items')
            self.assertEqual(len(a),12)
            self.assertEqual(len(b),12)
            self.assertTrue(set(x['id'] for x in a).isdisjoint(x['id'] for x in b))
            post(first,'/api/review',{'id':a[0]['id'],'review':'confirmed','note':'private'})
            with self.assertRaises(urllib.error.HTTPError):
                post(second,'/api/review',{'id':a[0]['id'],'review':'rejected'})
            with self.assertRaises(urllib.error.HTTPError) as cm:
                second.open(self.url+'/image/'+str(a[0]['id']))
            self.assertEqual(cm.exception.code,404)
            self.assertTrue(all(x['review']=='pending' for x in get(second,'/api/items')))
        finally:
            server.PUBLIC=original

    def test_cloud_free_only_and_payload(self):
        path=server.DATA/'cloud.png';path.write_bytes(PNG)
        response={'choices':[{'message':{'content':json.dumps(dict(vehicle='yes',sign='yes',marking='no',relation='yes',evidence=['右侧标志'],uncertainties=['需复核']))}}]}
        def fake(req,timeout):
            payload=json.loads(req.data)
            self.assertEqual(payload['provider']['max_price'],{'prompt':0,'completion':0})
            self.assertTrue(payload['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
            return io.BytesIO(json.dumps(response).encode())
        with patch.object(server,'API_KEY','test-only'),patch.object(server,'CLOUD_MODEL','openrouter/free'),patch.object(server.urllib.request,'urlopen',fake):
            self.assertEqual(server.cloud(path)['category'],'candidate')
        with patch.object(server,'API_KEY','test-only'),patch.object(server,'CLOUD_MODEL','paid-model'):
            with self.assertRaises(ValueError):server.cloud(path)
        with patch.object(server,'API_KEY',''):
            with self.assertRaises(ValueError):server.cloud(path)

    def test_tokenhub_payload_and_errors(self):
        path=server.DATA/'tokenhub.png';path.write_bytes(PNG)
        response={'choices':[{'message':{'content':json.dumps(dict(vehicle='yes',sign='yes',marking='no',relation='yes',evidence=['路侧标志'],uncertainties=['需人工核对']))}}]}
        def fake(req,timeout):
            body=json.loads(req.data)
            self.assertEqual(req.full_url,'https://tokenhub.tencentmaas.com/v1/chat/completions')
            self.assertEqual(body['model'],'hy-vision-2.0-instruct')
            self.assertNotIn('provider',body)
            self.assertEqual(req.get_header('Authorization'),'Bearer test-tokenhub-only')
            self.assertFalse(body['stream'])
            uri=body['messages'][0]['content'][1]['image_url']['url']
            self.assertEqual(base64.b64decode(uri.split(',',1)[1]),PNG)
            return io.BytesIO(json.dumps(response).encode())
        with patch.object(server,'PROVIDER','tokenhub'),patch.object(server,'TOKENHUB_KEY','test-tokenhub-only'):
            with patch.object(server.urllib.request,'urlopen',fake):
                self.assertEqual(server.cloud(path)['category'],'candidate')
            with patch.object(server.urllib.request,'urlopen',side_effect=urllib.error.HTTPError('https://example.invalid',401,'secret',{},None)):
                with self.assertRaisesRegex(RuntimeError,'密钥无效') as cm:server.cloud(path)
                self.assertNotIn('test-tokenhub-only',str(cm.exception))
            with patch.object(server,'TOKENHUB_KEY',''):
                with self.assertRaisesRegex(ValueError,'未配置腾讯云'):server.cloud(path)

    def test_reject_invalid_upload_and_unfinished_review(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.call('/api/import',{'name':'fake.png','batch':'week','data':base64.b64encode(b'not image').decode()})
        self.assertEqual(cm.exception.code,400)
        entry = server.add_image('test.png','week',PNG)
        with self.assertRaises(urllib.error.HTTPError):
            self.call('/api/review',{'id':entry['id'],'review':'confirmed'})
        with server.db() as c:
            c.execute("UPDATE items SET state='running' WHERE id=?",(entry['id'],))
        server.init()
        self.assertEqual(self.call('/api/items')[0]['state'],'queued')

    def test_model_adapter_with_mock_http(self):
        original = server.OLLAMA
        captured = []
        class Mock(server.BaseHTTPRequestHandler):
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                captured.append(body)
                response={'message':{'content':json.dumps(dict(vehicle='yes',sign='yes',marking='no',relation='yes',evidence=['右侧标志'],uncertainties=['需复核']))}}
                raw=json.dumps(response).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(raw)
        mock=server.ThreadingHTTPServer(('127.0.0.1',0),Mock)
        threading.Thread(target=mock.serve_forever,daemon=True).start()
        try:
            server.OLLAMA='http://127.0.0.1:'+str(mock.server_port)
            path=server.DATA/'sample.png'
            path.write_bytes(PNG)
            result=server.ollama(path)
            self.assertEqual(result['category'],'candidate')
            self.assertEqual(base64.b64decode(captured[0]['messages'][0]['images'][0]),PNG)
            self.assertFalse(captured[0]['stream'])
        finally:
            server.OLLAMA=original
            mock.shutdown()
            mock.server_close()

if __name__=='__main__':
    unittest.main()
