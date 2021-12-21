# for freetype mutator
import random
import zlib
import struct
import io
import png
import numpy as np
import os

def padding(index, length): # for test
    index = hex(index)[2:]
    return '0'*(length-len(index)) + index

def print_hex(data): # for test
    tmp = ''
    idx = 0
    print(" " * 9, "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n")
    for i,v in enumerate(data):
        if (i % 0x10) == 0:
            if (len(tmp) != 0):
                print(padding(idx, 8)+' ', tmp)
                tmp = ''
                idx += 0x10
        char_tmp = hex(v)[2:]
        if (len(char_tmp) < 2):
            tmp += '0'+hex(v)[2:]+' '
        else:
            tmp += hex(v)[2:]+' '
    print(padding(idx, 8)+' ', tmp+"\n")

class Ttf():
    def __init__(self):
        self.init_sbix()
        self.PNG = Glitch_png() # 현재 freetype - TTF에는 PNG만 구현되어 있습니다.
        
        with open('./glitch/ttf_template.ttf' ,'rb') as fp:
            self.TTF_template = fp.read()
        self.TTF_result = b''

    def init_sbix(self, graphic_type=None, data=None): # init에서 무조건 이 두개의 인자값을 설정해줘야합니다!
        # bitmap strike
        self.ppem = 0x96 # 2byte
        self.resolution = 0x48 # 2byte
        self.glyphdataOffsets = [0x14,0x14] # not mutate target # 4byte
        
        # glyph data record
        self.originOffsetX = 0 # 2byte
        self.originOffsetY = 0 # 2byte
        self.graphicType = graphic_type # not mutate target # 4byte
        self.bitmap_data = data # bitmap image data # 이미 여기 넣기 전에 각 class에서 뮤테이트 해놓음
        self.TTF_result = b''

    def mutate_sbix(self):
        self.ppem = random.randrange(0, 0x10000)
        self.resolution = random.randrange(0, 0x10000)
        self.originOffsetX = random.randrange(0, 0x10000)
        self.originOffsetY = random.randrange(0, 0x10000)
        
    def append_sbix(self):
        self._sbix = b'' # bit strike 구조체 부터
        ppem = struct.pack(">H", self.ppem)
        resolution = struct.pack(">H", self.resolution)
        originOffsetX = struct.pack(">H", self.originOffsetX)
        originOffsetY = struct.pack(">H", self.originOffsetY)
        graphicType = bytes(self.graphicType, 'ascii')

        if ((int((len(self.bitmap_data)+0x8+self.glyphdataOffsets[0])/2) % 4) == 0):
            self.glyphdataOffsets.append(int(len(self.bitmap_data)+0x8+self.glyphdataOffsets[0]/2))
        else:
            self.glyphdataOffsets.append(int( ((len(self.bitmap_data)+0x8+self.glyphdataOffsets[0])/2) + (((len(self.bitmap_data)+0x8+self.glyphdataOffsets[0])/2) % 4)))
        self.glyphdataOffsets.append(int(len(self.bitmap_data)+0x8+self.glyphdataOffsets[0])) # + 0x8 : grahpicType(4) + originOffsetX(2) + originOffsetY(2)
        
        self._sbix += ppem + resolution
        for offset in self.glyphdataOffsets:
            self._sbix += struct.pack(">I", offset)
        self._sbix += originOffsetX + originOffsetY + graphicType + self.bitmap_data

        self.TTF_result = self.TTF_template[:self.TTF_template.find(b'sbix') + 0xc] + struct.pack(">I", len(self._sbix)+0xc) + self.TTF_template[self.TTF_template.find(b'sbix') + 0xc + 4:] + self._sbix
        
    def make_ttf(self, graphicType=None, file_path=None):
        if ('png' in graphicType): # 현재 TTF에는 png만 구현이 되어 있습니다.
            bitmap_data = self.PNG.make_png()
            self.init_sbix(graphic_type='png ', data=bitmap_data)
            
        # mutate
        if(random.randrange(0,10) > 3):
            self.mutate_sbix()
        self.append_sbix()
        with open(file_path, 'wb') as fp:
            fp.write(self.TTF_result)
        print("[*] Gen TTF : ",file_path)

class Glitch_png():
    def __init__(self):
        # IHDR
        self.IHDR = b''
        self.IHDR_length = struct.pack(">I", 0x0000000d) # 4바이트 0xd로 값 고정
        self.IHDR_type = b'IHDR' # 4바이트 고정
        # IHDR Data
        self.IHDR_width = 0x00000000 # 4바이트
        self.IHDR_height = 0x00000000 # 4바이트
        self.IHDR_bit_depth = 0 # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
        self.IHDR_color_type = 0 # 유효한 값 0,2,3,4,6 # 1바이트
        self.IHDR_compression_method = struct.pack(">B", 0) # 1바이트 고정
        self.IHDR_filter_method = 0 # 유효한 값 (0~5) (0인 경우 None) # 1바이트 
        self.IHDR_interlace_method = 0 # 유효한 값 (0,1) (0인경우 interace x, 1인경우 interlace) # 1바이트
        self.IHDR_CRC = 0xf4999459 # (4바이트) (IHDR_type ~ CRC전의 값을 crc32 연산)

        # IDAT
        self.IDAT = b''
        self.IDAT_length = 0x00000000 # 4바이트 # IDAT chunk data의 크기
        self.IDAT_type = b'IDAT' # 4바이트 고정
        # IDAT Data
        self.IDAT_data = b''
        self.IDAT_CRC = 0xac5bd421 # (4바이트)

        # IEND
        self.IEND_length = 0x00000000 # (4바이트 고정)
        self.IEND_type = b'IEND' # 4바이트 고정
        self.IEND_CRC = 0xae426082 # (4바이트 고정, IEND 는 값이 변하지 않기 때문) 
        self.IEND = struct.pack(">I", self.IEND_length) + self.IEND_type + struct.pack(">I", self.IEND_CRC)

    def calc_CRC(self, value : bytes): # value : type + data 
        return struct.pack(">I", (zlib.crc32(value) % 0xffffffff)) # 4 byte로 리턴됨

    def mutate_IDHR(self, png_binary):
        self.IHDR_width = struct.pack(">I", self.IHDR_width)   # 이미 랜덤값으로 골라져 있는 상태
        self.IHDR_height = struct.pack(">I", self.IHDR_height)

        # 0. png_binary에서 IDHR값 추출 (length 필드는 제외)
        png_IDHR = png_binary[png_binary.find(b'IHDR'):png_binary.find(b'IHDR')+(0xd+8)] # 0xd : IHDR Lenght , 8 : IHDR_type_size + CRC_size
        #print_hex(png_IDHR)

        # 1. 50퍼 확률로 기존값 그대로 사용
        ## 뮤테이션 대상 flag 셋팅
        IHDR_color_type_flag = False
        IHDR_bit_depth_flag = False
        IHDR_compression_method_flag = False
        IHDR_filter_method_flag = False
        IHDR_interlace_method_flag = False
        
        ## 뮤테이션을 할지 그냥 그대로 쓸지 - 참 : 뮤테이션, 거짓 : 그대로 사용
        if(random.choice([True,False])):
            IHDR_color_type_flag = True
        self.IHDR_color_type = png_IDHR[0xd:0xe]
            
        if(random.choice([True,False])):
            IHDR_bit_depth_flag = True
        self.IHDR_bit_depth = png_IDHR[0xc:0xd]
            
        if(random.choice([True,False])):
            IHDR_compression_method_flag = True
        self.IHDR_compression_method = png_IDHR[0xe:0xf]
            
        if(random.choice([True,False])):
            IHDR_filter_method_flag = True
        self.IHDR_filter_method = png_IDHR[0xf:0x10]
            
        if(random.choice([True,False])):
            IHDR_interlace_method_flag = True
        self.IHDR_interlace_method = png_IDHR[0x10:0x11]
            
        # 2. 실제 뮤테이션
        ## color_type, bit depth 뮤테이션
        if((random.randrange(0,10) > 3)): # 70% 확률로 유효한 범위의 값을 사용 # 70%인 이유 : 따로 없습니다.
            if(IHDR_color_type_flag):
                available_list = [0,2,3,4,6]
                IHDR_color_type_int = random.choice(available_list) # 유효한 값 0,2,3,4,6  # 1바이트
            else:
                IHDR_color_type_int = int.from_bytes(self.IHDR_color_type, byteorder='big')

            if(random.randrange(0,10) > 3): # 70% 확률로 유효한 범위의 값을 사용 # 70%인 이유 : 따로 없습니다.
                ## color_type에 가능한 값이 아닌 경우 무조건 뮤테이트, 이미 올바른 값을 가지고 있는 경우 뮤테이션을 하기로 했으면 뮤테이트
                if(IHDR_color_type_int == 0):
                    available_list = [1,2,4,8,16]
                    if(int.from_bytes(self.IHDR_bit_depth, byteorder='big') not in available_list) or (IHDR_bit_depth_flag):
                        self.IHDR_bit_depth = random.choice(available_list)  # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
                elif( (IHDR_color_type_int == 2) or (IHDR_color_type_int == 4) or (IHDR_color_type_int == 6) ):
                    available_list = [8,16]
                    if(int.from_bytes(self.IHDR_bit_depth, byteorder='big') not in available_list) or (IHDR_bit_depth_flag):
                        self.IHDR_bit_depth = random.choice(available_list)  # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
                elif(IHDR_color_type_int == 3):
                    available_list = [1,2,4,8]
                    if (int.from_bytes(self.IHDR_bit_depth, byteorder='big') not in available_list) or (IHDR_bit_depth_flag):
                        self.IHDR_bit_depth = random.choice(available_list)  # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
            else:
                if(IHDR_bit_depth_flag):
                    self.IHDR_bit_depth = random.randrange(0,256)
        else:
            ## 뮤테이션 하기로 했으면 뮤테이션, 아니면 뮤테이션 안함
            if(IHDR_color_type_flag):
                IHDR_color_type_int = random.randrange(0,256)
            else:
                IHDR_color_type_int = int.from_bytes(self.IHDR_color_type, byteorder='big')
                
            if(random.randrange(0,10) > 3): # 70% 확률로 유효한 범위의 값을 사용 # 70%인 이유는 따로 없습니다.
                available_list = [1,2,4,8,16]
                self.IHDR_bit_depth = random.choice(available_list)  # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
            else:
                self.IHDR_bit_depth = random.randrange(0,256)  # 유효한 값 1,2,4,8,16 # 1바이트 # 이 두개는 표 참고
        if(type(IHDR_color_type_int) != type(b'')):
            self.IHDR_color_type = struct.pack(">B", IHDR_color_type_int)
        if(type(self.IHDR_bit_depth) != type(b'')):
            self.IHDR_bit_depth = struct.pack(">B", self.IHDR_bit_depth)
        
        if (IHDR_filter_method_flag):
            if(random.randrange(0,10) > 3): # 70% 확률로 유효한 범위의 값을 사용 # 70%인 이유는 따로 없습니다.
                self.IHDR_filter_method = struct.pack(">B", random.randrange(0, 6)) # 유효한 값 (0~5) (0인 경우 None) # 1바이트 
            else:
                self.IHDR_filter_method = struct.pack(">B", random.randrange(0, 256))

        if (IHDR_interlace_method_flag):
            if(random.randrange(0,10) > 3): # 70% 확률로 유효한 범위의 값을 사용 # 70%인 이유는 따로 없습니다.
                self.IHDR_interlace_method = struct.pack(">B", random.randrange(0, 2)) # 유효한 값 (0,1) (0인경우 interace x, 1인경우 interlace) # 1바이트
            else:
                self.IHDR_interlace_method = struct.pack(">B", random.randrange(0, 256))
        
        if (IHDR_compression_method_flag):
            if(random.randrange(0,10) > 7): # 10% 확률로 뮤테이션 (IHDR_interlace_method_flag:50% * 이거 랜덤 20%)
                self.IHDR_compression_method = struct.pack(">B", random.randrange(0, 256)) # 1바이트 고정
        if(type(self.IHDR_compression_method) != type(b'')):
                self.IHDR_compression_method = struct.pack(">B", self.IHDR_compression_method) # 1바이트 고정

        self.IDHR = self.IHDR_type + self.IHDR_width + self.IHDR_height + self.IHDR_bit_depth + self.IHDR_color_type + self.IHDR_compression_method + self.IHDR_filter_method + self.IHDR_interlace_method
        self.IHDR_CRC = self.calc_CRC(self.IDHR)
        self.IDHR = self.IHDR_length + self.IDHR + self.IHDR_CRC
    
    def make_png(self): # 정상적인 png 파일 생성
        # 1. width, height 값 랜덤 설정
        mutate_method_width_height = random.randrange(0,3) 
        if(mutate_method_width_height == 0):
            self.IHDR_width = random.randrange(1, 0x100) 
            self.IHDR_height = random.randrange(0x10000, 0x00020000)
        elif(mutate_method_width_height == 1):
            self.IHDR_width = random.randrange(0x10000, 0x00020000)
            self.IHDR_height = random.randrange(1, 0x100)
        elif(mutate_method_width_height == 3): # 되게 오래 걸림
            self.IHDR_width = random.randrange(1, 0x10000)
            self.IHDR_height = random.randrange(1, 0x10000)
        elif(mutate_method_width_height == 2): # 빠름
            self.IHDR_width = random.randrange(1, 0x1000)
            self.IHDR_height = random.randrange(1, 0x1000)

        # 2. bit_depth, compression_method, greyscale, alpha 값 랜덤 설정 ( 정상적인 범위 내에서 )
        tf = [True,False]
        self.IHDR_bit_depth = random.randrange(1, 17)
        self.IHDR_compression_method = random.randrange(-1, 10) # -1 : default, 0 : none, 1~9 : compress level

        # make_header and options
        new_png = png.Writer(width=self.IHDR_width, height=self.IHDR_height, greyscale=random.choice(tf), alpha=random.choice(tf), bitdepth=self.IHDR_bit_depth, compression=self.IHDR_compression_method,interlace=random.choice(tf))

        # 3. png_data값을 (줄단위로) 랜덤으로 할 것인지, 널값으로 통일시킬 것인지
        # make png data 
        if(random.choice([True,False])): # 참이면 랜덤
            png_data = [list(np.random.randint(0,256,4)) * self.IHDR_width for i in range(self.IHDR_height)]
        else:                            # 거짓이면 널값 통일
            png_data_front = list(np.random.randint(0,256,random.randrange(4,0x10,2)-1))
            png_data_back = list(np.random.randint(0,256,random.randrange(4,0x10,2)-1))
            try:
                png_data = png_data_front + list(np.zeros((self.IHDR_width*4*self.IHDR_height-len(png_data_front)-len(png_data_back)))) + png_data_back
            except (ValueError, MemoryError): # ValueError : width와 height 값이 둘다 매우매우 낮은 경우(예: 1,4) 해당 에러가 날 수 있음, MemoryError : 너무 큰 사이즈를 사용하는 경우 발생 할 수 있음.
                png_data = png_data_front + png_data_back
            
        # 정상적인 png 파일 생성 및 데이터 읽어오기
        byte_data = io.BytesIO()
        new_png.write_packed(byte_data, png_data)
        byte_data = byte_data.getvalue()
        byte_data += struct.pack('>H', random.randrange(0,0x10000)) # 무슨 값인지는 모르겠지만 poc코드를 보면 png 데이터 뒤에 알수없는 2바이트 값이 존재함. 해당 값은 테스트를 통해 아무런 값이 있어도 poc에는 영향을 주지 않는다는 사실을 알아 랜덤으로 값을 정하도록함.
        if ((len(byte_data) % 4) != 0) :
            byte_data += b'\x00'*( 4*((int(len(byte_data)/4))+1) - len(byte_data) )
        
        # 4. header mutate 
        # 4-1. 뮤테이트를 할지 말지 선택
        if(random.choice([True,False])): # 참이면 뮤테이트 안하고 png 데이터 리턴
            return byte_data
        self.mutate_IDHR(byte_data) # 헤더값 뮤테이션
        # 4-2.뮤테이트된 iDHR 값 고대로 적용 후 리턴
        byte_data = byte_data[:byte_data.find(b'IHDR')-4] + self.IDHR + byte_data[byte_data.find(b'IHDR')+(0xd+8):]
        #print("------------------") # test
        #print_hex(byte_data) # test
        return byte_data
        
        
class Glitch():
    def __init__(self):
        self.log_dir = "./log/"
        self.dir_check()
        #Ttf
        self.TTF = Ttf()
    
    def dir_check(self):
        if os.path.isdir(self.log_dir) != True:
            print("[*] Make log directory ")
            os.mkdir(self.log_dir)

if __name__ == '__main__':
    glitch = Glitch()
    png_data = glitch.TTF.PNG.make_png()
    glitch.TTF.make_ttf(graphicType='png', file_path='./glitch/glitch_png_test.ttf')
