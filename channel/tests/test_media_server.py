import http.client,sys,tempfile,threading,unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
from server import Handler

class QuietHandler(Handler):
    def log_message(self,*args):pass

class MediaServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory();cls.data=bytes(range(256))*64
        (Path(cls.folder.name)/'story.mp3').write_bytes(cls.data)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=cls.folder.name))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.folder.cleanup()
    def request(self,byte_range=None,method='GET'):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        connection.request(method,'/story.mp3',headers={'Range':byte_range} if byte_range else {})
        response=connection.getresponse();result=(response.status,dict(response.getheaders()),response.read());connection.close();return result
    def test_partial_media_serves_exact_bytes_and_length(self):
        status,headers,body=self.request('bytes=150-299')
        self.assertEqual(status,206);self.assertEqual(body,self.data[150:300]);self.assertEqual(headers['Content-Length'],'150')
        self.assertEqual(headers['Content-Range'],f'bytes 150-299/{len(self.data)}')
    def test_open_ended_suffix_and_head_requests(self):
        self.assertEqual(self.request('bytes=120-')[2],self.data[120:])
        self.assertEqual(self.request('bytes=-128')[2],self.data[-128:])
        self.assertEqual(self.request('bytes=0-1','HEAD')[2],b'')
        self.assertEqual(self.request()[2],self.data)
    def test_invalid_range_is_rejected_without_transferring_entire_media(self):
        for value in ('bytes=999999-','bytes=30-20','bytes=-0','bytes=','bytes=1-2,4-5'):
            status,headers,body=self.request(value);self.assertEqual(status,416);self.assertEqual(body,b'')

if __name__=='__main__':unittest.main()
