/*
 *  gcc -W -Wall -o RSA_Encrypt RSA_Encrypt.c -D_DEBUG -l crypto -g
 *  gcc -W -Wall RSA_Encrypt.c -l crypto -D_DEBUG -shared -fPIC -o RSA_Encrypt.so
 *  gcc -W -Wall RSA_Encrypt.c -l crypto -shared -fPIC -o RSA_Encrypt.so
 *  */


#include <string.h>

#include <openssl/rsa.h>
#include <openssl/err.h>

unsigned char * RSA_Encrypt(unsigned char *plain, int flen, const unsigned char *n , const unsigned char *e)
{
    unsigned char *to;
    int ret = 0;

    RSA *rsa;

    ERR_load_crypto_strings();

#ifdef _DEBUG
    int i;
    printf("RSA.n\n");
    for (i=0;i<128;i++) {
        if (i!=0 && i%16==0) printf("\n");
        printf("%02x ",n[i]);
    }
    printf("\n");
    printf("plain[len:%d]%s\n",flen,plain);
    printf("\n");

#endif
    rsa = RSA_new();
    //假定1024位公钥
    rsa->n = BN_bin2bn(n, 128, rsa->n);
    rsa->e = BN_bin2bn(e, 3, rsa->e);


    to = (unsigned char *)malloc(128);
    memset(to,0,128);
    ret = RSA_public_encrypt(flen, plain , (unsigned char *)to, rsa, RSA_PKCS1_PADDING);

    if (ret < 0) {
        ERR_print_errors_fp (stderr);
        return NULL;
    }
    else{
#ifdef _DEBUG
        printf("encrypted:\n");
        for (i=0;i<128;i++) {
            if (i!=0 && i%16==0) printf("\n");
            printf("%02x ",to[i]);
        }
        printf("\n");
#endif

        return to;
    }
}
#ifdef _DEBUG
int main(void)
{
    unsigned char rsa_n[128];
    char *data = "test";
    unsigned char *to;
    int len = 0;

    FILE *          fp;

    fp = fopen ("rsa_n", "rb");
    if (fp == NULL) {
        return -1;
    }

    len = fread(rsa_n,1, 128, fp);

    fclose(fp);

    to = (unsigned char *)malloc(128);
    memset(to,0,128);
    to = RSA_Encrypt((unsigned char *)data,strlen(data),rsa_n,(const unsigned char *)"\x01\x00\x01");

    return 1;

}
#endif

