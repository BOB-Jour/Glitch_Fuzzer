from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from urllib.parse import urlparse
import Glitch

DUP_FLAG = False
class GlitchHTTPHandler(BaseHTTPRequestHandler):
    glitch = Glitch.Glitch() # Freetype Mutator
    with open ('./templates/glitch_test.html', 'rt', encoding="utf-8") as fp:
        glitch_template = fp.read()

    def do_GET(self):
        parsed_path=urlparse(self.path)
        if(parsed_path.path == "/flag"):
            self.flag(parsed_path.query)
        
        elif(parsed_path.path == "/"):
            self.home()
        
        elif(parsed_path.path == "/freetype_test"):
            self.run_freetype_test(parsed_path.query)
        elif(parsed_path.path == "/glitch_testcase.ttf"):
            self.run_freetype_test2(parsed_path.path[-3:])
            
        return None

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
 
    def run_freetype_test(self, query):
        global DUP_FLAG
        if (DUP_FLAG):
            return None
        else:
            DUP_FLAG = True 

        query = query.split('=') 
        font_type = query[0]
        if (font_type.lower() == 'ttf'): # /freetype_test?ttf=png
            graphictype = query[1]
            self.glitch.TTF.make_ttf(graphicType=graphictype, file_path='./templates/glitch_testcase.ttf')
            html_code = self.glitch_template % (graphictype) # .format(domino_width=width, domino_height=height, domino_msec=msec)
        ## 아래부터는 다른 font...
        ## 현재는 ttf - png만 지원합니다.

        self._set_response()
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self.wfile.write(bytes(html_code, 'utf-8'))

        return None
        
    def run_freetype_test2(self, font_type):
        if(font_type == 'ttf'):
            test_case = 'glitch_testcase.ttf'
        with open('./templates/'+test_case, 'rb') as fp:
            font_binary = fp.read()

        self.send_response(200)
        self.send_header('Content-type', 'Application/ttf')
        self.end_headers()
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self.wfile.write(font_binary)
        return None

    
    def flag(self, _redirect):
        global DUP_FLAG
        DUP_FLAG = False
        self.send_response(302) # redirect code
        self.send_header('Location', "http://127.0.0.1:8080/"+_redirect)
        self.end_headers()
        return None

    def home(self):
        test_case = 'index.html'
        with open ('./templates/'+test_case, 'rb') as fp:
            html_code = fp.read()
        self._set_response()
        self.wfile.write(html_code)
        return None

def usage():
    print("[*] Glitch Fuzzing : http://127.0.0.1:8080/flag?freetype_test?[Font]=[graphicType]")
    print("[-] ex) font: ttf, graphicType: png = http://127.0.0.1:8080/flag?freetype_test?ttf=png")

def run(server_class=HTTPServer, handler_class=GlitchHTTPHandler, port=8080):
    logging.basicConfig(level=logging.CRITICAL)
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Start TestCase Server')
    logging.info('Server Info : http://127.0.0.1:8080/')
    usage()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping TestCase Server\n')

if __name__ == '__main__':
    run()