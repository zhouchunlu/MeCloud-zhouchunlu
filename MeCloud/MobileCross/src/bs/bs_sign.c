#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "bs_sign.h"
#include "bs_common.h"

static uint32_t crc_table[256]; 
static bool_t   is_crc_init = BS_FALSE;

static void init_crc_table(){
    uint32_t c;  
    uint32_t i, j;  
              
    for (i = 0; i < 256; i++) {  
        c = (uint32_t)i;  
        for (j = 0; j < 8; j++) {  
            if (c & 1){
                c = 0xedb88320L ^ (c >> 1);  
            }
            else{
                c = c >> 1;  
            }
        }  
        crc_table[i] = c;  
    }  
}

uint32_t bs_crc32(uint32_t crc, void* buffer, uint32_t size){
    uint32_t        i;

    if(!is_crc_init){
        init_crc_table();
        is_crc_init = BS_TRUE;
    }

    for (i = 0; i < size; i++){
        crc = crc_table[(crc ^ ((unsigned char*)buffer)[i]) & 0xff] ^ (crc >> 8);
    }

    return crc;
}

typedef struct {
    unsigned int state[4];      
    unsigned int count[2];      
    unsigned char buffer[64];      
} md5_context_t;

static void md5_encode(unsigned char * output, unsigned int * input, unsigned int len);
static void md5_decode(unsigned int * output, unsigned char * input, unsigned int len);
static void md5_transform(unsigned int state[4], unsigned char block[64]);
static void md5_init(md5_context_t * context);
static void md5_update(md5_context_t * context, unsigned char * buf, unsigned int len);
static void md5_final(md5_context_t * context, unsigned char digest[16]);

#define S11 7
#define S12 12
#define S13 17
#define S14 22
#define S21 5
#define S22 9
#define S23 14
#define S24 20
#define S31 4
#define S32 11
#define S33 16
#define S34 23
#define S41 6
#define S42 10
#define S43 15
#define S44 21

static unsigned char PADDING[64] =
{
    0x80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
};

#define F(x, y, z) (((x) & (y)) | ((~x) & (z)))
#define G(x, y, z) (((x) & (z)) | ((y) & (~z)))
#define H(x, y, z) ((x) ^ (y) ^ (z))
#define I(x, y, z) ((y) ^ ((x) | (~z)))
#define ROTATE_LEFT(x, n) (((x) << (n)) | ((x) >> (32-(n))))
#define FF(a, b, c, d, x, s, ac) {(a) += F((b), (c), (d)) + (x) + (unsigned int)(ac); (a) = ROTATE_LEFT((a), (s));(a) += (b);}
#define GG(a, b, c, d, x, s, ac) {(a) += G((b), (c), (d)) + (x) + (unsigned int)(ac); (a) = ROTATE_LEFT((a), (s));(a) += (b);}
#define HH(a, b, c, d, x, s, ac) {(a) += H((b), (c), (d)) + (x) + (unsigned int)(ac); (a) = ROTATE_LEFT((a), (s));(a) += (b);}
 
#define II(a, b, c, d, x, s, ac) {(a) += I((b), (c), (d)) + (x) + (unsigned int)(ac); (a) = ROTATE_LEFT((a), (s));(a) += (b);}

int bs_sign(const char* buf, bs_sign_t sign){
    md5_context_t       context;
    unsigned char       buff[BS_MD5_STRLEN/2];
    int                 j;
    int                 len = strlen(buf);
   
    md5_init(&context);
    md5_update(&context,(unsigned char *)buf, len);
    memset(buff, 0, 16);
    md5_final(&context,buff);
    for(j=0; j<BS_MD5_STRLEN/2; j++)
    {
        sprintf(sign+2*j, "%x",(buff[j] & 0xF0)>>4);
        sprintf(sign+2*j+1, "%x",buff[j] & 0x0F);
    }

    sign[BS_MD5_STRLEN] = '\0';
    return BS_SUCCESS;
}

uint64_t bs_usign(const char* buf){
    bs_sign_t           sign;
    /*
    int                 i;
    uint64_t            factor = 1;
    uint64_t            value = 0;
    */

    bs_sign(buf, sign);
    /*
    for(i=BS_MD5_STRLEN-1; i>=0; i--){
        factor *= 10;
        if(bs_is_num(sign[i])){
            value += (sign[i]-'0')*factor/10;
        }
        else{
            value += (sign[i]-'a'+10)*factor/10;
        }
    }
    */

    return *(uint64_t*)sign;
}

static void md5_encode(unsigned char * output, unsigned int * input, unsigned int len)
{
    unsigned int i, j;
    for (i = 0, j = 0; j < len; i++, j += 4) 
    {
       output[j] = (unsigned char) (input[i] & 0xff);
       output[j + 1] = (unsigned char) ((input[i] >> 8) & 0xff);
       output[j + 2] = (unsigned char) ((input[i] >> 16) & 0xff);
       output[j + 3] = (unsigned char) ((input[i] >> 24) & 0xff);
    }
}
static void md5_decode(unsigned int * output, unsigned char * input, unsigned int len)
{
    unsigned int i, j;
    for (i = 0, j = 0; j < len; i++, j += 4)
    {
       output[i] = ((unsigned int) input[j]) |
           (((unsigned int) input[j + 1]) << 8) |
           (((unsigned int) input[j + 2]) << 16) |
           (((unsigned int) input[j + 3]) << 24);
    }
}
static void md5_transform(unsigned int state[4], unsigned char block[64])
{
    unsigned int a = state[0], b = state[1], c = state[2], d = state[3], x[16];
    md5_decode(x, block, 64);
    /* Round 1 */
    FF(a, b, c, d, x[0], S11, 0xd76aa478);    /* 1 */
    FF(d, a, b, c, x[1], S12, 0xe8c7b756);    /* 2 */
    FF(c, d, a, b, x[2], S13, 0x242070db);    /* 3 */
    FF(b, c, d, a, x[3], S14, 0xc1bdceee);    /* 4 */
    FF(a, b, c, d, x[4], S11, 0xf57c0faf);    /* 5 */
    FF(d, a, b, c, x[5], S12, 0x4787c62a);    /* 6 */
    FF(c, d, a, b, x[6], S13, 0xa8304613);    /* 7 */
    FF(b, c, d, a, x[7], S14, 0xfd469501);    /* 8 */
    FF(a, b, c, d, x[8], S11, 0x698098d8);    /* 9 */
    FF(d, a, b, c, x[9], S12, 0x8b44f7af);    /* 10 */
    FF(c, d, a, b, x[10], S13, 0xffff5bb1);   /* 11 */
    FF(b, c, d, a, x[11], S14, 0x895cd7be);   /* 12 */
    FF(a, b, c, d, x[12], S11, 0x6b901122);   /* 13 */
    FF(d, a, b, c, x[13], S12, 0xfd987193);   /* 14 */
    FF(c, d, a, b, x[14], S13, 0xa679438e);   /* 15 */
    FF(b, c, d, a, x[15], S14, 0x49b40821);   /* 16 */
    /* Round 2 */
    GG(a, b, c, d, x[1], S21, 0xf61e2562);    /* 17 */
    GG(d, a, b, c, x[6], S22, 0xc040b340);    /* 18 */
    GG(c, d, a, b, x[11], S23, 0x265e5a51);   /* 19 */
    GG(b, c, d, a, x[0], S24, 0xe9b6c7aa);    /* 20 */
    GG(a, b, c, d, x[5], S21, 0xd62f105d);    /* 21 */
    GG(d, a, b, c, x[10], S22, 0x2441453);    /* 22 */
    GG(c, d, a, b, x[15], S23, 0xd8a1e681);   /* 23 */
    GG(b, c, d, a, x[4], S24, 0xe7d3fbc8);    /* 24 */
    GG(a, b, c, d, x[9], S21, 0x21e1cde6);    /* 25 */
    GG(d, a, b, c, x[14], S22, 0xc33707d6);   /* 26 */
    GG(c, d, a, b, x[3], S23, 0xf4d50d87);    /* 27 */
    GG(b, c, d, a, x[8], S24, 0x455a14ed);    /* 28 */
    GG(a, b, c, d, x[13], S21, 0xa9e3e905);   /* 29 */
    GG(d, a, b, c, x[2], S22, 0xfcefa3f8);    /* 30 */
    GG(c, d, a, b, x[7], S23, 0x676f02d9);    /* 31 */
    GG(b, c, d, a, x[12], S24, 0x8d2a4c8a);   /* 32 */
    /* Round 3 */
    HH(a, b, c, d, x[5], S31, 0xfffa3942);    /* 33 */
    HH(d, a, b, c, x[8], S32, 0x8771f681);    /* 34 */
    HH(c, d, a, b, x[11], S33, 0x6d9d6122);   /* 35 */
    HH(b, c, d, a, x[14], S34, 0xfde5380c);   /* 36 */
    HH(a, b, c, d, x[1], S31, 0xa4beea44);    /* 37 */
    HH(d, a, b, c, x[4], S32, 0x4bdecfa9);    /* 38 */
    HH(c, d, a, b, x[7], S33, 0xf6bb4b60);    /* 39 */
    HH(b, c, d, a, x[10], S34, 0xbebfbc70);   /* 40 */
    HH(a, b, c, d, x[13], S31, 0x289b7ec6);   /* 41 */
    HH(d, a, b, c, x[0], S32, 0xeaa127fa);    /* 42 */
    HH(c, d, a, b, x[3], S33, 0xd4ef3085);    /* 43 */
    HH(b, c, d, a, x[6], S34, 0x4881d05); /* 44 */
    HH(a, b, c, d, x[9], S31, 0xd9d4d039);    /* 45 */
    HH(d, a, b, c, x[12], S32, 0xe6db99e5);   /* 46 */
    HH(c, d, a, b, x[15], S33, 0x1fa27cf8);   /* 47 */
    HH(b, c, d, a, x[2], S34, 0xc4ac5665);    /* 48 */
    /* Round 4 */
    II(a, b, c, d, x[0], S41, 0xf4292244);    /* 49 */
    II(d, a, b, c, x[7], S42, 0x432aff97);    /* 50 */
    II(c, d, a, b, x[14], S43, 0xab9423a7);   /* 51 */
    II(b, c, d, a, x[5], S44, 0xfc93a039);    /* 52 */
    II(a, b, c, d, x[12], S41, 0x655b59c3);   /* 53 */
    II(d, a, b, c, x[3], S42, 0x8f0ccc92);    /* 54 */
    II(c, d, a, b, x[10], S43, 0xffeff47d);   /* 55 */
    II(b, c, d, a, x[1], S44, 0x85845dd1);    /* 56 */
    II(a, b, c, d, x[8], S41, 0x6fa87e4f);    /* 57 */
    II(d, a, b, c, x[15], S42, 0xfe2ce6e0);   /* 58 */
    II(c, d, a, b, x[6], S43, 0xa3014314);    /* 59 */
    II(b, c, d, a, x[13], S44, 0x4e0811a1);   /* 60 */
    II(a, b, c, d, x[4], S41, 0xf7537e82);    /* 61 */
    II(d, a, b, c, x[11], S42, 0xbd3af235);   /* 62 */
    II(c, d, a, b, x[2], S43, 0x2ad7d2bb);    /* 63 */
    II(b, c, d, a, x[9], S44, 0xeb86d391);    /* 64 */
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    memset((char *) x, 0, sizeof(x));
}
static void md5_init(md5_context_t * context)
{
    context->count[0] = context->count[1] = 0;
    context->state[0] = 0x67452301;
    context->state[1] = 0xefcdab89;
    context->state[2] = 0x98badcfe;
    context->state[3] = 0x10325476;
}
static void md5_update(md5_context_t * context, unsigned char * buf, unsigned int len)
{
    unsigned int i, index, partLen;
    index = (unsigned int) ((context->count[0] >> 3) & 0x3F);
    if ((context->count[0] += ((unsigned int) len << 3)) < ((unsigned int) len << 3))
    context->count[1]++;
    context->count[1] += ((unsigned int) len >> 29);
    partLen = 64 - index;
    if (len >= partLen) 
    {
       memcpy((char *) &context->buffer[index], (char *) buf, partLen);
       md5_transform(context->state, context->buffer);
       for (i = partLen; i + 63 < len; i += 64)
           md5_transform(context->state, &buf[i]);
       index = 0;
    } 
    else 
    {
        i = 0;
    }
    memcpy((char *) &context->buffer[index], (char *) &buf[i], len - i);
}
static void md5_final(md5_context_t * context, unsigned char digest[16])
{
    unsigned char bits[8];
    unsigned int index, padLen;
    md5_encode(bits, context->count, 8);
    index = (unsigned int) ((context->count[0] >> 3) & 0x3f);
    padLen = (index < 56) ? (56 - index) : (120 - index);
    md5_update(context, PADDING, padLen);
    md5_update(context, bits, 8);
    md5_encode(digest, context->state, 16);
    memset((char *) context, 0, sizeof(*context));
}
